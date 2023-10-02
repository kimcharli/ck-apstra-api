import click
from dotenv import load_dotenv
import os

from ck_apstra_api.apstra_session import prep_logging
from ck_apstra_api.apstra_session import CkApstraSession
from ck_apstra_api.apstra_blueprint import CkApstraBlueprint

class CkJobEnv:
    # session: CkApstraSession
    # log_level: str
    # session: CkApstraSession
    # main_bp: CkApstraBlueprint
    # excel_input_file: str

    def __init__(self):
        load_dotenv()
        self.log_level = os.getenv('logging_level')
        prep_logging(self.log_level)
        apstra_server_host = os.getenv('apstra_server_host')
        apstra_server_port = os.getenv('apstra_server_port')
        apstra_server_username = os.getenv('apstra_server_username')
        apstra_server_password = os.getenv('apstra_server_password')
        self.session = CkApstraSession(
            apstra_server_host, 
            apstra_server_port,
            apstra_server_username,
            apstra_server_password,
            )
        main_blueprint_name = os.getenv('main_blueprint')
        self.main_bp = CkApstraBlueprint(self.session, main_blueprint_name)
        self.excel_input_file = os.getenv('excel_input_file')


@click.group()
def cli():
    # load_dotenv()
    # log_level = os.getenv('logging_level', 'DEBUG')
    # prep_logging(log_level)
    pass

from ck_apstra_api.generic_system import click_read_generic_systems, click_add_generic_systems
cli.add_command(click_read_generic_systems)
cli.add_command(click_add_generic_systems)


