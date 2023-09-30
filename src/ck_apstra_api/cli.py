import click
from dotenv import load_dotenv
import os

from ck_apstra_api.apstra_session import prep_logging

@click.group()
def cli():
    load_dotenv()
    log_level = os.getenv('logging_level', 'DEBUG')
    prep_logging(log_level)    
    pass

from ck_apstra_api.generic_system import read_generic_system
cli.add_command(read_generic_system)


