import asyncio
import json
import os
import pathlib
import shutil
import time
from datetime import timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler

import click
import git
import httpx
import sqlite_utils
import uvicorn
from asgiref.sync import async_to_sync
from bs4 import BeautifulSoup
from click import echo
from datasette.app import Datasette
from sqlite_utils.db import NotFoundError

from .plugin import plugin_manager
from .search.pagefind import index_site
from .utils import add_config_to_env, load_config, local_config_file, static_folder

root = pathlib.Path.cwd()


# Define the main command group for the CLI
@click.group()
@click.version_option()
def cli():
    """TIL (Today I Learned) Command Line Interface."""
    pass


# Define a command to list all available plugins
@cli.command()
def list_plugins():
    """List all available plugins."""
    # Get the list of plugins from the plugin manager
    plugins = plugin_manager.get_plugins()

    # Check if there are any plugins available
    if plugins:
        click.echo("Available plugins:")
        # Print each plugin
        for plugin in plugins:
            click.echo(f"- {plugin}")
    else:
        click.echo("No plugins installed.")


@cli.command(name="build")
def build():
    """Build database tils.db."""
    build_database(root)


# options shared by multiple commands
template_folder_option = click.option(
    "--template-folder", type=click.Path(exists=True, file_okay=False, dir_okay=True), help="Override the default template directory."
)


@cli.command(name="serve")
@click.option("static", "-s", "--static", is_flag=True, help="Serve static files.")
@template_folder_option
def serve(template_folder, static):
    """Serve tils.db using datasette or the generated static files."""
    if static:
        os.chdir(static_folder())
        port = 8080
        server_address = ("localhost", port)
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
        print(f"Starting http server on http://localhost:{port}")
        httpd.serve_forever()
    else:
        add_config_to_env()
        serve_datasette(template_folder)


@cli.command(name="gen-static")
@template_folder_option
def gen_static(template_folder):
    """Generate static site from tils.db using datasette."""
    # disable search
    os.environ["TILLY_SEARCH"] = "static"

    add_config_to_env()
    db = database(root)
    # Get all distinct topics from the 'topics' column using a simple split approach
    all_topics = set()

    # Extract topics by splitting the comma-separated values
    for row in db.query("SELECT topics FROM til WHERE topics IS NOT NULL"):
        if row["topics"]:
            topics = [t.strip() for t in row["topics"].split(",")]
            for topic in topics:
                if topic:
                    all_topics.add(topic)

    urls = (
        ["/"]
        +
        # For URLs, use the first topic in the topics list for each document
        [f'/{row["topics"].split(",")[0]}/{row["slug"]}' for row in db.query("SELECT topics, slug FROM til")]
        + ["/all"]
        + [f"/{topic}" for topic in all_topics]
    )
    pages = get(urls=urls, template_folder=template_folder)
    write_html(pages)
    write_static()
    add_search_index()


@cli.command(name="copy-templates")
def copy():
    """Copy default templates to current repo for customization."""
    copy_templates()


@cli.command(name="config")
@click.option("local_config", "-l", "--local", is_flag=True, help="Local config.")
@click.option("url", "-u", "--url", help="The github repo https url.")
@click.option("base_url", "-b", "--base-url", help="The base url of the static site.")
@click.option("google_analytics", "-g", "--google-analytics", help="Your Google Analytics id.")
@click.option("output_folder", "-o", "--output-folder", help="The output folder for the static site.")
# @click.option("template_folder", "-t", "--template-folder", help="Custom templates folder.")
def config(local_config, url, base_url, google_analytics, output_folder="_static"):
    """List config."""
    config = {}

    if local_config:
        config = load_config(local_config=load_config)

        # Update config with provided parameters
        if url:
            config["TILLY_GITHUB_URL"] = url
        if base_url:
            config["TILLY_BASE_URL"] = base_url
        if google_analytics:
            config["TILLY_GOOGLE_ANALYTICS"] = google_analytics
        if output_folder:
            config["TILLY_OUTPUT_FOLDER"] = output_folder

        # Save the updated config
        with open(local_config_file(), "w") as f:
            json.dump(config, f, indent=4)

    # Print the configuration
    print(json.dumps(config, indent=4, default=str))
    return config


def datasette(template_folder=None):
    """Create a Datasette instance with the specified template folder."""
    script_dir = pathlib.Path(__file__).parent.parent / "tilly"
    template_folder = template_folder or script_dir / "templates"

    return Datasette(
        files=["tils.db"],
        static_mounts=[("static", script_dir / "static")],
        plugins_dir=script_dir / "plugins",
        template_dir=template_folder,
    )


def serve_datasette(template_folder=None):
    """Serve the Datasette application."""
    ds = datasette(template_folder=template_folder)

    # Get the ASGI application and serve it
    app = ds.app()
    uvicorn.run(app, host="localhost", port=8001)


@async_to_sync
async def get(urls=None, template_folder=None):
    """Fetch pages for the given URLs."""
    ds = datasette(template_folder)
    await ds.invoke_startup()

    pages = []
    for url in urls:
        httpx_response = await ds.client.request(
            "GET",
            url,
            follow_redirects=False,
            avoid_path_rewrites=True,
        )
        pages.append({"url": url, "html": httpx_response.text})

    return pages


def write_html(pages):
    """Write HTML files for the given pages."""
    static_root = root / static_folder()
    echo(f"write_html to {static_root}")

    # clear the directory
    if static_root.exists():
        shutil.rmtree(static_root / "_static", ignore_errors=True)

    # skip jekyll
    no_jekyll = root / ".nojekyll"
    no_jekyll.touch()

    for page in pages:
        path = static_root / page["url"].lstrip("/") / "index.html"
        echo(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(page["html"])


def write_static():
    """Copy generated static files from the default directory to the output folder."""
    script_dir = pathlib.Path(__file__).parent.parent / "tilly"
    src = script_dir / "static"
    dst = root / static_folder()

    echo(dst / "static")

    shutil.copytree(src, os.path.join(dst, os.path.basename(src)), dirs_exist_ok=True)


def add_search_index():
    """Add search index using Pagefind."""
    src = root / static_folder()
    dst = root / static_folder() / "pagefind"

    asyncio.run(index_site(site=str(src), output_path=str(dst)))


def copy_templates(template_folder="templates"):
    """Copy templates from the default directory to the current working directory."""
    script_dir = pathlib.Path(__file__).parent.parent / "tilly"
    src = script_dir / "templates"
    dst = root

    try:
        # Ensure the destination directory exists
        if not os.path.exists(dst):
            os.makedirs(dst)

        shutil.copytree(src, os.path.join(dst, os.path.basename(src)), dirs_exist_ok=True)
        print(f"Successfully copied default templates to {dst}")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise


def database(repo_path):
    """Create or return the database."""
    return sqlite_utils.Database(repo_path / "tils.db")


def build_database(repo_path):
    """Build the database from the markdown files."""
    echo(f"build_database {repo_path}")
    config = load_config(local_config=True)
    all_times = created_changed_times(repo_path, "main")
    db = database(repo_path)
    _til_table(db, all_times, config)
    _snippets_table(db, all_times, config)


def _til_table(db, all_times, config):
    table = db.table("til", pk="path")
    for filepath in root.glob(f"[!_]*/*.md"):
        print(filepath)
        # Read the entire file content
        content = filepath.read_text()

        # Check for frontmatter
        frontmatter = {}
        if content.startswith("---"):
            # Extract frontmatter
            _, frontmatter_text, remaining_content = content.split("---", 2)
            try:
                # Try to parse the frontmatter as YAML
                import yaml

                frontmatter = yaml.safe_load(frontmatter_text.strip())
                # Get the first line of the remaining content as title
                title_line = remaining_content.strip().split("\n", 1)[0]
                title = title_line.lstrip("#").strip()
                body = remaining_content.strip()
            except Exception as e:
                print(f"Error parsing frontmatter in {filepath}: {e}")
                # Fall back to original parsing method
                lines = content.split("\n")
                title = lines[0].lstrip("#").strip()
                body = "\n".join(lines[1:]).strip()
        else:
            # No frontmatter, use original parsing method
            lines = content.split("\n")
            title = lines[0].lstrip("#").strip()
            body = "\n".join(lines[1:]).strip()

        path = str(filepath.relative_to(root))
        slug = filepath.stem

        # Get path-based topic (from directory structure)
        path_topic = path.split("/")[0]

        # Get frontmatter topics if available
        frontmatter_topics = frontmatter.get("topics", [])
        if isinstance(frontmatter_topics, str):
            frontmatter_topics = [frontmatter_topics]

        # Combine topics with path_topic always first
        topics = [path_topic]
        for topic in frontmatter_topics:
            if topic != path_topic and topic not in topics:
                topics.append(topic)

        url = config.get("url", "") + "{}".format(path)
        # Do we need to render the markdown?
        path_slug = path.replace("/", "_")
        try:
            row = table.get(path_slug)
            previous_body = row["body"]
            previous_html = row["html"]
        except (NotFoundError, KeyError):
            previous_body = None
            previous_html = None
        record = {
            "path": path_slug,
            "slug": slug,
            "topics": ",".join(topics),
            "title": title,
            "url": url,
            "body": body,
        }
        if (body != previous_body) or not previous_html:
            record["html"] = github_markdown(body, path)
            print("Rendered HTML for {}".format(path))

        # Populate summary
        record["summary"] = first_paragraph_text_only(record.get("html") or previous_html or "")
        record.update(all_times[path])
        with db.conn:
            table.upsert(record, alter=True)

    # enable full text search
    table.enable_fts(["title", "body", "topics"], tokenize="porter", create_triggers=True, replace=True)


def _snippets_table(db, all_times, config):
    # Create the table explicitly with the schema we want
    if "snippets" not in db.table_names():
        # Create empty table with the desired schema
        db.create_table(
            "snippets",
            {
                "path": str,
                "slug": str,
                "topics": str,
                "title": str,
                "url": str,
                "body": str,
                "html": str,
                "summary": str,
                "created": str,
                "created_utc": str,
                "updated": str,
                "updated_utc": str,
            },
            pk="path",
        )
        print("Created empty snippets table")

    # Reference to the table
    table = db.table("snippets", pk="path")

    # Process any existing snippet files
    for snippets_count, filepath in enumerate(root.glob("_snippets*/*.md"), 1):
        print(filepath)
        # Read the entire file content
        content = filepath.read_text()

        # Check for frontmatter
        frontmatter = {}
        if content.startswith("---"):
            # Extract frontmatter
            _, frontmatter_text, remaining_content = content.split("---", 2)
            try:
                # Try to parse the frontmatter as YAML
                import yaml

                frontmatter = yaml.safe_load(frontmatter_text.strip())
                # Get the first line of the remaining content as title
                title_line = remaining_content.strip().split("\n", 1)[0]
                title = title_line.lstrip("#").strip()
                body = remaining_content.strip()
            except Exception as e:
                print(f"Error parsing frontmatter in {filepath}: {e}")
                # Fall back to original parsing method
                lines = content.split("\n")
                title = lines[0].lstrip("#").strip()
                body = "\n".join(lines[1:]).strip()
        else:
            # No frontmatter, use original parsing method
            lines = content.split("\n")
            title = lines[0].lstrip("#").strip()
            body = "\n".join(lines[1:]).strip()

        path = str(filepath.relative_to(root))
        slug = filepath.stem

        # Get path-based topic (from directory structure)
        path_topic = path.split("/")[0]

        # Get frontmatter topics if available
        frontmatter_topics = frontmatter.get("topics", [])
        if isinstance(frontmatter_topics, str):
            frontmatter_topics = [frontmatter_topics]

        # Combine topics with path_topic always first
        topics = [path_topic]
        for topic in frontmatter_topics:
            if topic != path_topic and topic not in topics:
                topics.append(topic)

        url = config.get("url", "") + "{}".format(path)
        # Do we need to render the markdown?
        path_slug = path.replace("/", "_")
        try:
            row = table.get(path_slug)
            previous_body = row["body"]
            previous_html = row["html"]
        except (NotFoundError, KeyError):
            previous_body = None
            previous_html = None
        record = {
            "path": path_slug,
            "slug": slug,
            "topics": ",".join(topics),
            "title": title,
            "url": url,
            "body": body,
        }
        if (body != previous_body) or not previous_html:
            record["html"] = github_markdown(body, path)
            print("Rendered HTML for {}".format(path))

        # Populate summary
        record["summary"] = first_paragraph_text_only(record.get("html") or previous_html or "")
        record.update(all_times[path])
        with db.conn:
            table.upsert(record, alter=True)

    # enable full text search
    table.enable_fts(["title", "body", "topics"], tokenize="porter", create_triggers=True, replace=True)


def github_markdown(body, path):
    """Render markdown using GitHub API."""
    retries = 0
    response = None
    html = None
    while retries < 3:
        headers = {}
        if os.environ.get("MARKDOWN_GITHUB_TOKEN"):
            headers = {"authorization": "Bearer {}".format(os.environ["MARKDOWN_GITHUB_TOKEN"])}
        response = httpx.post(
            "https://api.github.com/markdown",
            json={
                # mode=gfm would expand #13 issue links and suchlike
                "mode": "markdown",
                "text": body,
            },
            headers=headers,
        )
        if response.status_code == 200:
            html = response.text
            break
        elif response.status_code == 401:
            assert False, "401 Unauthorized error rendering markdown"
        else:
            print(response.status_code, response.headers)
            print("  sleeping 60s")
            time.sleep(60)
            retries += 1
    else:
        assert False, "Could not render {} - last response was {}".format(path, response.headers)
    return html


def first_paragraph_text_only(html):
    """Extract and returns the text of the first paragraph from a html object.

    Args:
        html: The HTML content.

    Returns:
        str: The text of the first paragraph, or an empty string if not found.

    """
    try:
        soup = BeautifulSoup(html, "html.parser")
        # Attempt to find the first paragraph and extract its text
        first_paragraph = soup.find("p")
        return " ".join(first_paragraph.stripped_strings)
    except AttributeError:
        # Handle the case where 'soup.find('p')' returns None
        return ""


def created_changed_times(repo_path, ref="main"):
    """Extract creation and modification timestamps for all files in a git repository.

    Args:
        repo_path (str): Path to the git repository
        ref (str, optional): Git reference (branch, tag, commit). Defaults to "main"

    Returns:
        dict: Dictionary with filepaths as keys and nested dictionaries as values containing:
            - created: Initial commit timestamp in local timezone
            - created_utc: Initial commit timestamp in UTC
            - updated: Latest commit timestamp in local timezone
            - updated_utc: Latest commit timestamp in UTC

    Raises:
        ValueError: If repository has uncommitted changes or untracked files

    """
    # Initialize empty dictionary to store file timestamps
    created_changed_times = {}

    # Open git repository with GitDB backend
    repo = git.Repo(repo_path, odbt=git.GitDB)

    # Ensure working directory is clean before processing
    # if repo.is_dirty() or repo.untracked_files:
    #     raise ValueError("The repository has changes or untracked files.")

    # Get commits in reverse chronological order (oldest first)
    commits = reversed(list(repo.iter_commits(ref)))

    # Process each commit
    for commit in commits:
        dt = commit.committed_datetime
        # Get list of files modified in this commit
        affected_files = list(commit.stats.files.keys())

        # Update timestamps for each affected file
        for filepath in affected_files:
            # If file not seen before, record creation time
            if filepath not in created_changed_times:
                created_changed_times[filepath] = {
                    "created": dt.isoformat(),
                    "created_utc": dt.astimezone(timezone.utc).isoformat(),
                }
            # Always update the modification time
            created_changed_times[filepath].update(
                {
                    "updated": dt.isoformat(),
                    "updated_utc": dt.astimezone(timezone.utc).isoformat(),
                }
            )
    return created_changed_times
