
import click

from . import cliVar, prep_logging

@click.command()
@click.option('--file-format', type=click.Choice(['yaml', 'json']), default='yaml', help='File format')
@click.option('--file-folder', type=str, default='', help='File folder')
def export_resources(file_format: str, file_folder: str):
    """
    Export the Resources in yaml, json format

    """
    logger = prep_logging('DEBUG', 'export_resources()')

    cliVar.update(file_folder=file_folder, file_format=file_format)
    cliVar.data_in_file.pull_resources()

    cliVar.export_file()
    

