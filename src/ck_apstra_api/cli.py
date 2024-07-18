from dataclasses import dataclass, asdict, fields
from pathlib import Path
import click
import os
import logging
import time
import json
from pprint import pprint
import csv


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
def check_apstra(ctx):
    """
    Test the connectivity to the server
    """
    from ck_apstra_api.apstra_session import CkApstraSession, prep_logging
    from result import Ok, Err

    logger = prep_logging('DEBUG', 'check_apstra()')

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
def check_blueprint(ctx, bp_name: str):
    """
    Test the connectivity to the blueprint
    """
    from ck_apstra_api.apstra_session import CkApstraSession, prep_logging
    from ck_apstra_api.apstra_blueprint import CkApstraBlueprint
    from result import Ok, Err

    logger = prep_logging('DEBUG', 'check_blueprint()')

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
@click.option('--bp-name', type=str, default='terra', help='Blueprint name')
@click.option('--json-file', type=str, help='Json file name to export to')
@click.pass_context
def export_blueprint(ctx, bp_name: str, json_file: str = None):
    """
    Export a blueprint into a json file
    """
    from ck_apstra_api.apstra_session import CkApstraSession, prep_logging
    from ck_apstra_api.apstra_blueprint import CkApstraBlueprint
    from result import Ok, Err

    logger = prep_logging('DEBUG', 'export_blueprint()')

    host_ip = ctx.obj['HOST_IP']
    host_port = ctx.obj['HOST_PORT']
    host_user = ctx.obj['HOST_USER']
    host_password = ctx.obj['HOST_PASSWORD']    
    session = CkApstraSession(host_ip, host_port, host_user, host_password)

    bp = CkApstraBlueprint(session, bp_name)
    logger.info(f"{bp_name=} {json_file=}")

    if not json_file:
        json_file = f"{bp_name}.json"
    json_path = os.path.expanduser(json_file)

    the_blueprint_data = bp.dump()
    with open(json_path, 'w') as f:
        f.write(json.dumps(the_blueprint_data, indent=2))

    logger.info(f"blueprint {bp_name} exported to {json_file}")


@cli.command()
@click.option('--bp-name', type=str, default='terra', help='Blueprint name to create')
@click.option('--json-file', type=str, help='Json file name to import from')
@click.pass_context
def import_blueprint(ctx, bp_name: str, json_file: str = None):
    """
    Import a blueprint from a json file
    """
    from ck_apstra_api.apstra_session import CkApstraSession, prep_logging
    from ck_apstra_api.apstra_blueprint import CkApstraBlueprint
    from result import Ok, Err

    logger = prep_logging('DEBUG', 'import_blueprint()')

    host_ip = ctx.obj['HOST_IP']
    host_port = ctx.obj['HOST_PORT']
    host_user = ctx.obj['HOST_USER']
    host_password = ctx.obj['HOST_PASSWORD']    
    session = CkApstraSession(host_ip, host_port, host_user, host_password)

    logger.info(f"{bp_name=} {json_file=}")
    session = CkApstraSession(host_ip, host_port, host_user, host_password)

    json_path = os.path.expanduser(json_file)
    with open(json_path, 'r') as f:
        bp_json = f.read()
    bp_dict = json.loads(bp_json)
    node_list = []
    for node_dict in bp_dict['nodes'].values():
        # remove system_id for switches
        if node_dict['type'] == 'system' and node_dict['system_type'] == 'switch' and node_dict['role'] != 'external_router':
            node_dict['system_id'] = None
            node_dict['deploy_mode'] = 'undeploy'
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

    bp_dict['label'] = bp_name

    # TODO: just reference copy
    relationship_list = [rel_dict for rel_dict in bp_dict['relationships'].values()]

    bp_spec = { 
        'design': bp_dict['design'], 
        'label': bp_dict['label'], 
        'init_type': 'explicit', 
        'nodes': node_list,
        'relationships': relationship_list
    }
    bp_created = session.post('blueprints', data=bp_spec)
    logger.info(f"blueprint {bp_name} created: {bp_created}")


@cli.command()
@click.option('--bp-name', type=str, default='terra', help='Blueprint name')
@click.option('--out-folder', type=str, default='~/Downloads/devices', help='Folder name to export')
@click.pass_context
def export_device_configs(ctx, bp_name: str, out_folder: str):
    """
    Export a device configurations into multiple files

    The folder for each device will be created with the device name.
    0_load_override_pristine.txt (if the device is managed)
    0_load_override_freeform.txt (if case of freeform)
    1_load_merge_intended.txt
    2_load_merge_configlet.txt (if applicable)
    3_load_set_configlet-set.txt (if applicable)
    """
    from pathlib import Path
    from ck_apstra_api.apstra_session import CkApstraSession, prep_logging
    from ck_apstra_api.apstra_blueprint import CkApstraBlueprint
    from result import Ok, Err

    logger = prep_logging('DEBUG', 'export_device_configs()')

    host_ip = ctx.obj['HOST_IP']
    host_port = ctx.obj['HOST_PORT']
    host_user = ctx.obj['HOST_USER']
    host_password = ctx.obj['HOST_PASSWORD']    
    session = CkApstraSession(host_ip, host_port, host_user, host_password)

    bp = CkApstraBlueprint(session, bp_name)
    
    logger.info(f"{bp_name=} {out_folder=}")
    bp_folder_path = os.path.expanduser(f"{out_folder}/{bp_name}")
    Path(bp_folder_path).mkdir(parents=True, exist_ok=True)


    def write_to_file(file_name, content):
        MIN_SIZE = 2  # might have one \n
        if len(content) > MIN_SIZE:
            with open(file_name, 'w') as f:
                f.write(content)
            logger.info(f"write_to_file(): {os.path.basename(file_name)}")


    # switch for reference architecture, internal for freeform
    for switch in [x['switch'] for x in bp.query("node('system', system_type=is_in(['switch', 'internal']), name='switch')").ok_value]:
        system_label = switch['label']
        system_id = switch['id']
        system_serial = switch['system_id']
        system_dir = f"{bp_folder_path}/{system_label}"
        Path(system_dir).mkdir(exist_ok=True)
        logger.info(f"{system_label=}")

        if system_serial:
            pristine_config = session.get_items(f"systems/{system_serial}/pristine-config")['pristine_data'][0]['content']
            write_to_file(f"{system_dir}/0_load_override_pristine.txt", pristine_config)

        rendered_confg = bp.get_item(f"nodes/{system_id}/config-rendering")['config']
        write_to_file(f"{system_dir}/rendered.txt", rendered_confg)

        begin_configlet = '------BEGIN SECTION CONFIGLETS------'
        begin_set = '------BEGIN SECTION SET AND DELETE BASED CONFIGLETS------'

        config_string = rendered_confg.split(begin_configlet)
        if bp.design == 'freeform':
            write_to_file(f"{system_dir}/0_load_override_freeform.txt", config_string[0])
        else:
            write_to_file(f"{system_dir}/1_load_merge_intended.txt", config_string[0])
        if len(config_string) < 2:
            # no configlet. skip
            continue

        configlet_string = config_string[1].split(begin_set)
        write_to_file(f"{system_dir}/2_load_merge_configlet.txt", configlet_string[0])
        if len(configlet_string) < 2:
            # no configlet in set type. skip
            continue

        write_to_file(f"{system_dir}/3_load_set_configlet-set.txt", configlet_string[1])



@cli.command()
@click.option('--bp-name', type=str, default='terra', help='Blueprint name')
@click.option('--vn-csv', type=str, required=True, help='The CSV file path of virtual networks to import from')
@click.pass_context
def import_virtual_networks(ctx, bp_name, vn_csv: str):
    """
    Import virtual networks from a CSV file
    """
    from pathlib import Path
    from ck_apstra_api.apstra_session import CkApstraSession, prep_logging
    from ck_apstra_api.apstra_blueprint import CkApstraBlueprint
    from result import Ok, Err
    import io

    logger = prep_logging('DEBUG', 'export_device_configs()')

    host_ip = ctx.obj['HOST_IP']
    host_port = ctx.obj['HOST_PORT']
    host_user = ctx.obj['HOST_USER']
    host_password = ctx.obj['HOST_PASSWORD']    
    session = CkApstraSession(host_ip, host_port, host_user, host_password)

    bp = CkApstraBlueprint(session, bp_name)
    logger.info(f"{bp_name=} {vn_csv=}")

    # get the list of dictionaries per each virtual network from the Apstra
    vn_csv_string = bp.get_item('virtual-networks-csv-bulk')['csv_bulk']
    csv_reader = csv.DictReader(io.StringIO(vn_csv_string))
    current_vn_dict = [row for row in csv_reader]
    # logger.info(f"{vn_csv_dict=}")
    # pprint(vn_csv_dict)
    return

    vn_csv_path = os.path.expanduser(vn_csv)
    # input_vn_dict = []
    with open(vn_csv_path, 'r') as csvfile:
        csv_reader = csv.reader(csvfile)
        input_vn_dict = [row for row in csv_reader]

    for header in current_vn_dict[0].keys():
        if header not in input_vn_dict[0].keys():
            raise ValueError(f"Header {header} not found in the input CSV file")

        for row in csv_reader:
            links_to_add.append(dict(zip(headers, row)))
    imported = bp.patch_virtual_networks_csv_bulk(df.to_csv(index=False))




@cli.command()
@click.option('--bp-name', type=str, default='terra', help='Blueprint name')
@click.pass_context
def print_lldp_data(ctx, bp_name: str = 'terra'):
    """
    Print the LLDP data of the blueprint
    """
    from pathlib import Path
    from ck_apstra_api.apstra_session import CkApstraSession, prep_logging
    from ck_apstra_api.apstra_blueprint import CkApstraBlueprint
    from result import Ok, Err

    logger = prep_logging('DEBUG', 'export_device_configs()')

    host_ip = ctx.obj['HOST_IP']
    host_port = ctx.obj['HOST_PORT']
    host_user = ctx.obj['HOST_USER']
    host_password = ctx.obj['HOST_PASSWORD']    
    session = CkApstraSession(host_ip, host_port, host_user, host_password)

    bp = CkApstraBlueprint(session, bp_name)
    logger.info(f"{bp_name=}")

    lldp_data = bp.get_lldp_data()
    for link in lldp_data['links']:
        logger.info(f"{link['id']=} {link['endpoints'][0]['system']['label']}:{link['endpoints'][0]['interface']['if_name']} {link['endpoints'][1]['system']['label']}:{link['endpoints'][1]['interface']['if_name']}")
    
    # server_hostnames = session.get_items('server-hostnames-lldp')
    # pprint(server_hostnames)
    
    return lldp_data




@dataclass
class SystemsData:
    system: str
    asn: str
    lo0: str
    rack: str
    device_profile: str

    def __init__(self, system_input: dict):
        self.system = system_input['system']['label']
        self.asn = system_input['domain']['domain_id'] if system_input['domain'] else None
        self.lo0 = system_input['loopback']['ipv4_addr'] if system_input['loopback'] else None
        self.rack = system_input['rack']['label'] if system_input['rack'] else None
        self.device_profile = system_input['interface_map']['device_profile_id'] if system_input['interface_map'] else None

@cli.command()
@click.option('--bp-name', type=str, default='terra', help='Blueprint name')
@click.option('--systems-csv', type=str, required=True, help='The CSV file path to create')
@click.pass_context
def export_systems(ctx, bp_name, systems_csv):
    """
    Export systems of a blueprint to a CSV file

    The CSV file will have below columns:
    system, asn, lo0, rack, device_profile
    
    """
    from ck_apstra_api.apstra_session import CkApstraSession, prep_logging
    from ck_apstra_api.apstra_blueprint import CkApstraBlueprint
    from result import Ok, Err
    logger = prep_logging('DEBUG', 'export_systems()')

    host_ip = ctx.obj['HOST_IP']
    host_port = ctx.obj['HOST_PORT']
    host_user = ctx.obj['HOST_USER']
    host_password = ctx.obj['HOST_PASSWORD']

    session = CkApstraSession(host_ip, host_port, host_user, host_password)
    bp = CkApstraBlueprint(session, bp_name)
    systems_csv_path = os.path.expanduser(systems_csv)
    logger.info(f"{systems_csv_path=} writing to {systems_csv_path}")
    """
    TODO: implement tags
        optional(
            node(name='system').in_('tag').node(name='tag')
            )
    """
    systems_query = """match(
        node('system', name='system'),
        optional(
            node(name='system').in_('composed_of_systems').node('domain', name='domain')
        ),
        optional(
            node(name='system').out('hosted_interfaces').node('interface', if_name='lo0.0', name='loopback')
            ),
        optional(
            node(name='system').out('part_of_rack').node('rack', name='rack')
            ),
        optional(
            node(name='system').out('interface_map').node('interface_map', name='interface_map')
            )
    )"""
    systems_rest = bp.query(systems_query)
    systems = systems_rest.ok_value
    with open(systems_csv_path, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([field.name for field in fields(SystemsData)])
        for system in systems:
            system_data = SystemsData(system)
            # logger.info(f"{system_data}")    
            writer.writerow(asdict(system_data).values())





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


@cli.command()
@click.option('--virtual-network', type=str, required=True, help='Subject Virtual Network name')
@click.option('--routing-zone', type=str, required=True, help='Destination Routing Zone name')
@click.option('--blueprint', type=str, required=True, help='Blueprint name')
@click.pass_context
def relocate_vn(ctx, blueprint: str, virtual_network: str, routing_zone: str):
    """
    Move a Virtual Network to the target Routing Zone

    The virtual network move involves deleting and recreating the virtual network in the target routing zone.
    To delete the virtual network, the associated CT should be taken care of. Either deassign and delete them and later do reverse.
    This CT handling trouble can be mitigated with a temporary VN to replace the original VN in the CT. Later, to be reversed later.

    """
    from ck_apstra_api.apstra_session import CkApstraSession, prep_logging
    from ck_apstra_api.apstra_blueprint import CkApstraBlueprint

    from result import Ok, Err

    logger = prep_logging('INFO', 'relocate_vn()')
    logger.info(f"Took order {blueprint=} {virtual_network=} {routing_zone=}")

    NODE_NAME_RZ = 'rz'

    host_ip = ctx.obj['HOST_IP']
    host_port = ctx.obj['HOST_PORT']
    host_user = ctx.obj['HOST_USER']
    host_password = ctx.obj['HOST_PASSWORD']

    session = CkApstraSession(host_ip, host_port, host_user, host_password)
    bp = CkApstraBlueprint(session, blueprint)

    @dataclass
    class Order(object):
        target_vn: str = virtual_network
        target_vn_id: str = None
        target_vn_spec: dict = None
        test_vn: str = None
        test_vn_id: str = None
        test_vn_spec: dict = None
        target_rz: str = routing_zone
        terget_rz_id: str = None

        def summary(self):
            return f"Order: {self.target_vn=} {self.target_vn_id=} {self.test_vn=} {self.test_vn_id=} {self.target_rz=} {self.terget_rz_id=}"
    the_order = Order()

    # get the target_rz_id
    found_rz = bp.query(f"node('security_zone', name='{NODE_NAME_RZ}', label='{routing_zone}')").ok_value
    the_order.terget_rz_id = found_rz[0][NODE_NAME_RZ]['id']

    # get all the VNs
    found_vns_dict = bp.get_item('virtual-networks')['virtual_networks']

    # pick the target VN data
    target_vn_node = [vn for vn in found_vns_dict.values() if vn['label'] == virtual_network]    
    if len(target_vn_node) == 0:
        logger.error(f"Virtual Network {virtual_network} not found")
        return
    the_order.target_vn_spec = target_vn_node[0]
    the_order.target_vn_id = the_order.target_vn_spec['id']
    # check if the VN is already in the target RZ
    if the_order.target_vn_spec['security_zone_id'] == the_order.terget_rz_id:
        logger.warning(f"Virtual Network {virtual_network} already in the target Routing Zone {routing_zone}")
        return

    for res in bp.get_temp_vn(the_order.target_vn):
        if isinstance(res, dict):
            the_order.test_vn_spec = res
            the_order.test_vn_id = res['id']
            the_order.test_vn = res['label']
        else:
            logger.info(res)

    logger.info(f"Ready to relocate vn {virtual_network}: {the_order.summary()}")

    # replace CTs with test VN
    for res in bp.swap_ct_vns(the_order.target_vn_id, the_order.test_vn_id):
        logger.info(res)

    # delete the original VN
    deleted = bp.delete_item(f"virtual-networks/{the_order.target_vn_id}")
    logger.info(f"VN {the_order.target_vn}:{the_order.target_vn_id} deleted: {deleted=}")

    # create the original VN in the target RZ
    the_order.target_vn_spec['security_zone_id'] = the_order.terget_rz_id
    created = bp.post_item('virtual-networks', the_order.target_vn_spec)
    the_order.target_vn_id = created.json()['id']
    logger.info(f"VN {the_order.target_vn}:{the_order.target_vn_id} created: {created=} under RZ:{the_order.target_rz}")

    # restore the CTs
    logger.info(f"Restoring CTs with new VN {the_order.test_vn}:{the_order.test_vn_id}")
    for res in bp.swap_ct_vns(the_order.test_vn_id, the_order.target_vn_id):
        logger.info(res)

    # remove the temporary VN
    deleted = bp.delete_item(f"virtual-networks/{the_order.test_vn_id}")
    logger.info(f"Temporary VN {the_order.test_vn}:{the_order.test_vn_id} deleted: {deleted=}")

    logger.info(f"Order completed: {the_order.summary()}")
    session.logout()


@cli.command()
@click.option('--virtual-network', type=str, required=True, help='Subject Virtual Network name')
@click.option('--routing-zone', type=str, required=True, help='Destination Routing Zone name')
@click.option('--blueprint', type=str, required=True, help='Blueprint name')
@click.pass_context
def test_get_temp_vn(ctx, blueprint: str, virtual_network: str, routing_zone: str):
    """
    Test get_temp_vn
    """
    from ck_apstra_api.apstra_session import CkApstraSession, prep_logging
    from ck_apstra_api.apstra_blueprint import CkApstraBlueprint

    logger = prep_logging('INFO', 'test_get_temp_vn()')
    host_ip = ctx.obj['HOST_IP']
    host_port = ctx.obj['HOST_PORT']
    host_user = ctx.obj['HOST_USER']
    host_password = ctx.obj['HOST_PASSWORD']

    session = CkApstraSession(host_ip, host_port, host_user, host_password)
    bp = CkApstraBlueprint(session, blueprint)

    for res in bp.get_temp_vn(virtual_network):
        if isinstance(res, dict):
            temp_vn = res
        else:
            logger.info(res)

if __name__ == "__main__":
    cli()
