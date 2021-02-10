"""
This module implements flask-cli commands.

@author: Philippe Fajeau
"""

from flask.cli import AppGroup

romwhist_cli = AppGroup("romwhist")


"""
Example command

@rom-whist_cli.command("add-user")
@click.option("--arg1")
@click.option("--arg2")
@click.option("--arg3")
def add_user(arg1, arg2, arg3):
    print("Command executed successfully")
"""
