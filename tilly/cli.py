import click
from .plugins import plugin_manager

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

