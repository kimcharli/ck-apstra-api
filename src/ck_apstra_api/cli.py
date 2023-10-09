from pathlib import Path
import click
from dotenv import load_dotenv
import os
import pandas as pd
import logging
import time

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
    df_no_loop = df.drop(columns=['loopback_ips'])
    # logging.debug(f"{df_no_loop.to_csv(index=False)=}")
    imported = bp.patch_security_zones_csv_bulk(df_no_loop.to_csv(index=False))

    # update the loopback_ips pool of the routinz zones
    loopback_ips_spec = {
        'resource_groups': [
            # {
            #     'pool_ids': [ "b66cd3ed-c1fb-4ed1-b669-d8bff6a13287" ],
            #     'resource_type': 'ip',
            #     'group_name': "sz:yK-lzKeNP5D273wXJuU,leaf_loopback_ips"
            # }
        ]
    }
    ip_pool_name_to_id = { ip_pool['display_name']: ip_pool['id'] for ip_pool in bp.get_ip_pools() }
    # RZ will not be available immediately. Wait for the RZ to be created
    for i in range(3):
        rz_name_to_id = { rz['rz']['label']: rz['rz']['id'] for rz in bp.query("node('security_zone', name='rz')") }
        # There are default RZ, so it should be more than 1
        if len(rz_name_to_id) > 1:
            break
        time.sleep(3)

    for index, row in df.iterrows():
        # logging.debug(f"{index=} {row=}")
        # logging.debug(f"{row['name']=} {row['loopback_ips']=}")
        loopback_ips_spec['resource_groups'].append({
            'pool_ids': [ ip_pool_name_to_id[row['loopback_ips']] ],
            'resource_type': 'ip',
            'group_name': f"sz:{rz_name_to_id[row['name']]},leaf_loopback_ips"
        })

    patched = bp.patch_resource_groups(loopback_ips_spec)
    logging.debug(f"{patched=} {patched.text=}")

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
