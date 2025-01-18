import re
import pathlib
import subprocess

root = pathlib.Path(__file__).parent.resolve()


def run_command_and_capture_output(command):
    """
    Runs a CLI command and captures its output into an array.

    :param command: A list where the first item is the command name and
                    subsequent items are command arguments.
    :return: A list containing each line of the command output as a string.
    """
    try:
        # Use subprocess.run to execute the command and capture the output
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        # Split the output into lines and return as a list
        return result.stdout.splitlines()

    except subprocess.CalledProcessError as e:
        # If the command fails, capture the error message
        return [f"Command '{command[0]}' failed with error: {e.stderr.strip()}"]

    except Exception as e:
        # For other exceptions, return a generic error message
        return [f"An error occurred: {str(e)}"]


if __name__ == "__main__":
    # capture output of the tilly command
    cli_re = re.compile(r"<!\-\- cli-help starts \-\->.*<!\-\- cli-help ends \-\->", re.DOTALL)
    cli = ["<!-- cli-help starts -->"]
    cli.append("```bash")
    for output in run_command_and_capture_output("tilly"):
        cli.append(output)
    cli.append("```")
    cli.append("<!-- cli-help ends -->")

    # update the readme
    readme = root / "README.md"
    index_txt = "\n".join(cli).strip()
    readme_contents = readme.open().read()

    # update cli command output
    rewritten = cli_re.sub(index_txt, readme_contents)

    # save the updated readme
    readme.open("w").write(rewritten)
