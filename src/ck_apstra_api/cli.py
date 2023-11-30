from pathlib import Path
import click
from dotenv import load_dotenv
import os
import pandas as pd
import logging
import time
import json
from datetime import datetime
from pprint import pprint

from ck_apstra_api.apstra_session import prep_logging
from ck_apstra_api.apstra_session import CkApstraSession
from ck_apstra_api.apstra_blueprint import CkApstraBlueprint

class CkJobEnv:
    # session: CkApstraSession
    # log_level: str
    # session: CkApstraSession
    # main_bp: CkApstraBlueprint
    # excel_input_file: str
    # main_blueprint_name: str
    # config_dir: str
    # bp_json_file: str

    def __init__(self, command: str = None, bp_name: str = None):
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
        self.main_blueprint_name = bp_name or os.getenv('main_blueprint')
        # self.main_blueprint_name = os.getenv('main_blueprint')
        # in case of skipping the bp loading
        if command and command == 'add-bp-from-json':
            self.bp_json_file = os.getenv('bp_json_file')
            return
        self.main_bp = CkApstraBlueprint(self.session, self.main_blueprint_name)
        self.excel_input_file = os.getenv('excel_input_file')
        self.config_dir = os.getenv('config_dir')

    def get_bp_json_file(self):
        if hasattr(self, 'bp_json_file') and self.bp_json_file != '':
            return self.bp_json_file
        datetime_str = time.strftime("%Y-%m-%d-%H:%M")
        return f"{self.main_blueprint_name}-{datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}.json"


def add_bp_from_json(job_env: CkJobEnv, bp_json_file: str = None, new_bp_name: str = None):
    """
    Add a blueprint from a json file
    The json file - job_env.bp_json_file
    The blueprint label - job_env.main_blueprint_name

    """
    bp_json = ''
    bp_json_file = bp_json_file or job_env.bp_json_file or input('Blueprint json file: ')
    logging.info(f"{bp_json_file=}")
    with open(bp_json_file, 'r') as f:
        bp_json = f.read()
    bp_dict = json.loads(bp_json)
    node_list = []
    for node_id, node_dict in bp_dict['nodes'].items():
        if node_dict['type'] == 'system' and node_dict['system_type'] == 'switch' and node_dict['role'] != 'external_router':
            node_dict['system_id'] = None
            # node_dict['deploy_mode'] = 'undeploy'
        if node_dict['type'] == 'metadata':
            node_dict['label'] = job_env.main_blueprint_name      
        for k, v in node_dict.items():
            if k == 'tags':
                if v is None or v == "['null']":
                    node_dict[k] = []
            elif k == 'property_set' and v is None:
                node_dict.update({
                    k: {}
                })
        node_list.append(node_dict)        

    bp_dict['label'] = new_bp_name or job_env.main_blueprint_name

    relationship_list = [
        rel_dict for rel_id, rel_dict in bp_dict['relationships'].items()
    ]

    bp_spec = { 
        'design': bp_dict['design'], 
        'label': bp_dict['label'], 
        'init_type': 'explicit', 
        'nodes': node_list,
        'relationships': relationship_list
    }
    bp_created = job_env.session.post('blueprints', data=bp_spec)
    logging.info(f"push_bp_from_json() BP bp_created = {bp_created}")

@click.command(name='add-bp-from-json')
@click.option('--bp-json-file', default='')
@click.option('--new-bp-name', default='')
def click_add_bp_from_json(bp_json_file, new_bp_name):
    job_env = CkJobEnv(command='add-bp-from-json')
    add_bp_from_json(job_env, bp_json_file=bp_json_file, new_bp_name=new_bp_name)


def get_bp_into_json(job_env: CkJobEnv, bp_name, json_path):
    """
    Create a blueprint into a json file
    The blueprint label - job_env.main_blueprint_name
    The json file - job_env.bp_json_file
    """
    the_bp_name = bp_name if bp_name != '' else job_env.main_blueprint_name
    the_json_path = json_path if json_path != '' else job_env.get_bp_json_file()
    logging.info(f"{the_bp_name=} {the_json_path=}")

    the_blueprint_data = job_env.main_bp.dump()
    logging.info(f"{the_blueprint_data.keys()=}")
    with open(the_json_path, 'w') as f:
        f.write(json.dumps(the_blueprint_data, indent=2))

    return

@click.command(name='get-bp-into-json')
@click.option('--bp-name', default='')
@click.option('--json-path', default='')
def click_get_bp_into_json(bp_name, json_path):
    job_env = CkJobEnv(command='get-bp-into-json',bp_name=bp_name)
    get_bp_into_json(job_env, bp_name, json_path)


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


def get_lldp_data(job_env: CkJobEnv):
    bp = job_env.main_bp
    lldp_data = bp.get_lldp_data()
    for link in lldp_data['links']:
        logging.info(f"{link['id']=} {link['endpoints'][0]['system']['label']}:{link['endpoints'][0]['interface']['if_name']} {link['endpoints'][1]['system']['label']}:{link['endpoints'][1]['interface']['if_name']}")
    
    server_hostnames = bp.get_items('server-hostnames-lldp')
    pprint(server_hostnames)
    
    return lldp_data

@click.command(name='get-lldp-data', help='Get LLDP data between managed switches')
def click_get_lldp_data():
    job_env = CkJobEnv()
    get_lldp_data(job_env)


@click.group()
@click.option('--logging-level', default='')
def cli(logging_level: str = ''):
    # job_env = CkJobEnv(logging_level)
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
cli.add_command(click_add_bp_from_json)
cli.add_command(click_get_bp_into_json)
cli.add_command(click_get_lldp_data)

from ck_apstra_api.ip_endpoint import click_add_ip_endpoints
cli.add_command(click_add_ip_endpoints)

from ck_apstra_api.pull_device_configuration import click_pull_configurations
cli.add_command(click_pull_configurations)