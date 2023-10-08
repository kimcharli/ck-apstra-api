from pathlib import Path
import click
from dotenv import load_dotenv
import os
import pandas as pd
import logging

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


def import_routing_zones(job_env: CkJobEnv, input_file_path_string: str = None, sheet_name: str = 'routing_zones'):
    bp = job_env.main_bp
    excel_file_sting = input_file_path_string or os.getenv('excel_input_file')
    input_file_path = Path(excel_file_sting) 
    df = pd.read_excel(input_file_path, sheet_name=sheet_name)
    logging.debug(f"{df.to_csv(index=False)=}")
    imported = bp.patch_security_zones_csv_bulk(df.to_csv(index=False))
    logging.debug(f"{imported=} {imported.text=}")
    # TODO: loopback_ips

@click.command(name='import-routing-zones')
def click_import_routing_zones():
    job_env = CkJobEnv()
    import_routing_zones(job_env)


def import_virtual_networks(job_env: CkJobEnv, input_file_path_string: str = None, sheet_name: str = 'virtual_networks'):
    bp = job_env.main_bp
    excel_file_sting = input_file_path_string or os.getenv('excel_input_file')
    input_file_path = Path(excel_file_sting) 
    df = pd.read_excel(input_file_path, sheet_name=sheet_name)
    logging.debug(f"{df.to_csv(index=False)=}")
    imported = bp.patch_virtual_networks_csv_bulk(df.to_csv(index=False))
    logging.debug(f"{imported=} {imported.text=}")

@click.command(name='import-virtual-networks')
def click_import_virtual_networks():
    job_env = CkJobEnv()
    import_virtual_networks(job_env)



@click.group()
def cli():
    # load_dotenv()
    # log_level = os.getenv('logging_level', 'DEBUG')
    # prep_logging(log_level)
    pass

from ck_apstra_api.generic_system import click_read_generic_systems, click_add_generic_systems, click_assign_connecitivity_templates
cli.add_command(click_read_generic_systems)
cli.add_command(click_add_generic_systems)
cli.add_command(click_assign_connecitivity_templates)
cli.add_command(click_import_routing_zones)
cli.add_command(click_import_virtual_networks)
