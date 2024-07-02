from pathlib import Path
import click
import os
import logging
import time
import json
from datetime import datetime
from pprint import pprint
import csv

# from ck_apstra_api.apstra_session import CkApstraSession, CustomFormatter

# ch = logging.StreamHandler()
# ch.setLevel(logging.DEBUG)
# ch.setFormatter(CustomFormatter())


def add_bp_from_json(host_ip, host_port, host_user, host_password, bp_name, bp_json_file: str = None, new_bp_name: str = None):
    """
    Add a blueprint from a json file
    The json file - job_env.bp_json_file
    The blueprint label - job_env.main_blueprint_name

    """
    return
    session = CkApstraSession(host_ip, host_port, host_user, host_password)
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
            node_dict['label'] = bp_name     
        for k, v in node_dict.items():
            if k == 'tags':
                if v is None or v == "['null']":
                    node_dict[k] = []
            elif k == 'property_set' and v is None:
                node_dict.update({
                    k: {}
                })
        node_list.append(node_dict)        

    bp_dict['label'] = new_bp_name or bp_name

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
    bp_created = session.post('blueprints', data=bp_spec)
    logging.info(f"push_bp_from_json() BP bp_created = {bp_created}")



def get_bp_into_json(host_ip, host_port, host_user, host_password, bp_name, json_path):
    """
    Create a blueprint into a json file
    The blueprint label - job_env.main_blueprint_name
    The json file - job_env.bp_json_file
    """
    return
    session = CkApstraSession(host_ip, host_port, host_user, host_password)

    the_bp_name = bp_name
    the_json_path = json_path
    logging.info(f"{the_bp_name=} {the_json_path=}")

    # TODO: fix - load bp data
    the_blueprint_data = bp_name
    logging.info(f"{the_blueprint_data.keys()=}")
    with open(the_json_path, 'w') as f:
        f.write(json.dumps(the_blueprint_data, indent=2))

    return



def import_routing_zones(host_ip, host_port, host_user, host_password, input_file_path_string: str = None, sheet_name: str = 'routing_zones'):
    return
    session = CkApstraSession(host_ip, host_port, host_user, host_password)
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



def import_virtual_networks(host_ip, host_port, host_user, host_password, input_file_path_string: str = None, sheet_name: str = 'virtual_networks'):
    return
    session = CkApstraSession(host_ip, host_port, host_user, host_password)

    bp = job_env.main_bp
    excel_file_sting = input_file_path_string or os.getenv('excel_input_file')
    input_file_path = Path(excel_file_sting) 
    df = pd.read_excel(input_file_path, sheet_name=sheet_name)
    logging.debug(f"{df.to_csv(index=False)=}")
    imported = bp.patch_virtual_networks_csv_bulk(df.to_csv(index=False))
    logging.debug(f"{imported=} {imported.text=}")



def get_lldp_data(host_ip, host_port, host_user, host_password, bp_name: str = 'terra'):
    return
    session = CkApstraSession(host_ip, host_port, host_user, host_password)

    bp = job_env.main_bp
    lldp_data = bp.get_lldp_data()
    for link in lldp_data['links']:
        logging.info(f"{link['id']=} {link['endpoints'][0]['system']['label']}:{link['endpoints'][0]['interface']['if_name']} {link['endpoints'][1]['system']['label']}:{link['endpoints'][1]['interface']['if_name']}")
    
    server_hostnames = bp.get_items('server-hostnames-lldp')
    pprint(server_hostnames)
    
    return lldp_data


@click.group()
@click.option('--host-ip', type=str, default='10.85.192.45', help='Host IP address')
@click.option('--host-port', type=int, default=443, help='Host port')
@click.option('--host-user', type=str, default='admin', help='Host username')
@click.option('--host-password', type=str, default='admin', help='Host password')
@click.version_option(message='%(package)s, %(version)s')
@click.pass_context
def cli(ctx, host_ip: str, host_port: str, host_user: str, host_password: str):
    """
    A CLI tool for interacting with ck-apstra-api
    """    
    ctx.ensure_object(dict)
    ctx.obj['HOST_IP'] = host_ip
    ctx.obj['HOST_PORT'] = host_port
    ctx.obj['HOST_USER'] = host_user
    ctx.obj['HOST_PASSWORD'] = host_password
    pass


@cli.command()
@click.pass_context
def server_check(ctx):
    """
    Test the connectivity to the server
    """
    from ck_apstra_api.apstra_session import CkApstraSession, prep_logging
    from result import Ok, Err

    logger = prep_logging('DEBUG', 'server_check()')

    host_ip = ctx.obj['HOST_IP']
    host_port = ctx.obj['HOST_PORT']
    host_user = ctx.obj['HOST_USER']
    host_password = ctx.obj['HOST_PASSWORD']

    session = CkApstraSession(host_ip, host_port, host_user, host_password)
    logger.info(f"version {session.version=} {session.token=}")
    session.logout()


@cli.command()
@click.option('--bp-name', type=str, default='terra', help='Blueprint name')
@click.pass_context
def blueprint_check(ctx, bp_name: str):
    """
    Test the connectivity to the blueprint
    """
    from ck_apstra_api.apstra_session import CkApstraSession, prep_logging
    from ck_apstra_api.apstra_blueprint import CkApstraBlueprint
    from result import Ok, Err

    logger = prep_logging('DEBUG', 'blueprint_check()')

    host_ip = ctx.obj['HOST_IP']
    host_port = ctx.obj['HOST_PORT']
    host_user = ctx.obj['HOST_USER']
    host_password = ctx.obj['HOST_PASSWORD']    
    session = CkApstraSession(host_ip, host_port, host_user, host_password)

    # bp_name = ctx.obj['BP_NAME']
    bp = CkApstraBlueprint(session, bp_name)
    logger.info(f"{bp_name=}, {bp.id=}")
    if bp.id:
        logger.info(f"Blueprint {bp_name} found")
    else:
        logger.warning(f"Blueprint {bp_name} not found")
        
    session.logout()



@cli.command()
@click.option('--gs-csv-in', type=str, default='~/Downloads/gs_sample.csv', help='Path to the CSV file for generic systems')
@click.pass_context
def import_generic_system(ctx, gs_csv_in: str):
    """
    Import generic systems from a CSV file
    """
    from ck_apstra_api.generic_system import GsCsvKeys, add_generic_systems
    from ck_apstra_api.apstra_session import CkApstraSession, prep_logging
    from result import Ok, Err

    logger = prep_logging('DEBUG', 'import_generic_system()')

    host_ip = ctx.obj['HOST_IP']
    host_port = ctx.obj['HOST_PORT']
    host_user = ctx.obj['HOST_USER']
    host_password = ctx.obj['HOST_PASSWORD']

    # uncomment below for debugging purpose. It prints the username and password
    # logger.info(f"{ctx.obj=}")

    session = CkApstraSession(host_ip, host_port, host_user, host_password)
    gs_csv_path = os.path.expanduser(gs_csv_in)

    links_to_add = []
    with open(gs_csv_path, 'r') as csvfile:
        csv_reader = csv.reader(csvfile)
        headers = next(csv_reader)  # Read the header row
        expected_headers = [header.value for header in GsCsvKeys]
        if headers != expected_headers:
            raise ValueError("CSV header mismatch. Expected headers: " + ', '.join(expected_headers))

        for row in csv_reader:
            links_to_add.append(dict(zip(headers, row)))

    for res in add_generic_systems(session, links_to_add):
        if isinstance(res, Ok):
            logger.info(res.ok_value)
        elif isinstance(res, Err):
            logger.warning(res.err_value)
        else:
            logger.info(f"text {res}")


@cli.command()
@click.option('--gs-csv-out', type=str, default='~/gs.csv', help='Path to the CSV file for generic systems')
@click.pass_context
def export_generic_system(ctx, gs_csv_out: str):
    """
    Export generic systems to a CSV file
    """
    from ck_apstra_api.generic_system import get_generic_systems
    from ck_apstra_api.apstra_session import CkApstraSession, prep_logging
    from result import Ok, Err

    logger = prep_logging('DEBUG', 'export_generic_system()')

    host_ip = ctx.obj['HOST_IP']
    host_port = ctx.obj['HOST_PORT']
    host_user = ctx.obj['HOST_USER']
    host_password = ctx.obj['HOST_PASSWORD']

    # uncomment below for debugging purpose. It prints the username and password
    # logger.info(f"{ctx.obj=}")

    session = CkApstraSession(host_ip, host_port, host_user, host_password)
    gs_csv_path = os.path.expanduser(gs_csv_out)

    for res in get_generic_systems(session, gs_csv_path):
        if isinstance(res, Ok):
            logger.info(res.ok_value)
        elif isinstance(res, Err):
            logger.warning(res.err_value)
        else:
            logger.info(f"text {res}")

if __name__ == "__main__":
    cli()
