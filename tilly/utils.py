import pathlib

import click

def get_app_dir():
    path = pathlib.Path(click.get_app_dir("tilly"))
    path.mkdir(exist_ok=True, parents=True)
    return path
