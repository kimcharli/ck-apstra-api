from functools import cache
import json
import os
import time
import click
import yaml

from . import cliVar, prep_logging

INTERCONNECT = 'evpn_interconnect_groups'
IC_ROUTING_ZONES = 'interconnect_security_zones'
IC_VIRTUAL_NETWORKS = 'interconnect_virtual_networks'


@cache
def get_routing_policy_id(bp, label: str):
    """
    Get routing policy by label

    """
    logger = prep_logging('DEBUG', 'get_routing_policy()')

    if label:
        routing_policies = {x['label']: x for x in bp.get_item('routing-policies')['items']}
        if label in routing_policies:
            return routing_policies[label]['id']
    return None

def pull_ic_virtual_networks(ic_datum_in_blueprint: dict, ic_datum: dict):
    """
    Retrieve virtual networks

    """
    logger = prep_logging('DEBUG', 'pull_ic_virtual_networks()')

    variables = ['label', 'translation_vni', 'vrf_name', 'vni', 'l2', 'l3']
    ic_datum[IC_VIRTUAL_NETWORKS] = { v1['label']: 
                                { k2: v2 for k2, v2 in v1.items() if k2 in variables } 
                                for v1 in ic_datum_in_blueprint[IC_VIRTUAL_NETWORKS].values()}

    return


def pull_ic_routingz_zones(ic_datum_in_blueprint: dict, ic_datum: dict):
    """
    Retrieve routing zones

    """
    logger = prep_logging('DEBUG', 'pull_ic_routingz_zones()')

    variables = ['vrf_name', 'routing_policy_label', 'interconnect_route_target', 'enabled_for_l3']
    ic_datum[IC_ROUTING_ZONES] = { v1['vrf_name']: 
        { k2: v2 for k2, v2 in v1.items() if k2 in variables } 
        for v1 in ic_datum_in_blueprint[IC_ROUTING_ZONES].values()}

    return


def pull_remote_gateway_node_ids(ic_rw_node_ids:dict, ic_datum: dict ):
    """
    Retrieve remote gateway variables

    """
    logger = prep_logging('DEBUG', 'pull_remote_gateway_variables()')

    variables = ['gw_name', 'gw_ip', 'gw_asn', 'ttl', 'keepalive_timer', 'holdtime_timer', 'local_gw_nodes']
    remote_gateway_data = ic_datum['remote_gateway_node_ids'] = {}

    for rg_datum_in in ic_rw_node_ids.values():
        rg_name = rg_datum_in['gw_name']
        rg_datum = remote_gateway_data[rg_name] = { k: v for k, v in rg_datum_in.items() if k in variables}
        rg_datum['local_gw_nodes'] = [ x['label'] for x in rg_datum_in['local_gw_nodes']]

    return



def pull_interconnect(bp, dci_tree):
    """
    Pull interconnect data from the blueprint

    """
    logger = prep_logging('DEBUG', 'pull_interconnect()')

    variables = ['label', 'interconnect_route_target', 'interconnect_esi_mac']
    ic_tree = dci_tree['interconnect'] = []

    # retrieve top level variables
    ic_data_in_blueprint = bp.get_item(INTERCONNECT)[INTERCONNECT]
    if not ic_data_in_blueprint:
        logger.info(f"No DCI interconnect data in blueprint {bp.label}")
        return
    
    # 'evpn_interconnect_groups': [ dci, dci, ...]
    for ic_datum_in_bp in ic_data_in_blueprint:
        ic_datum = { k: v for k, v in ic_datum_in_bp.items() if k in variables  }

        pull_remote_gateway_node_ids(ic_datum_in_bp['remote_gateway_node_ids'], ic_datum)
        pull_ic_routingz_zones(ic_datum_in_bp, ic_datum)
        pull_ic_virtual_networks(ic_datum_in_bp, ic_datum)

        ic_tree.append(ic_datum)

    return


def pull_ott(bp, dci_tree):
    """
    Pull OTT data from the blueprint

    """
    logger = prep_logging('DEBUG', 'pull_ott()')
    pass



class DciEsiMacMsb():
    def pull_msb():
        '''Retribe ESI MAC MSB from the blueprint'''
        bp = cliVar.blueprint
        fabric_settings_in_bp = bp.get_item('fabric-settings')
        dci_tree = cliVar.data_in_file['blueprint'][bp.label]['dci']
        dci_tree['esi_mac_msb'] = fabric_settings_in_bp['esi_mac_msb']

    def push_msb():
        '''Update ESI MAC MSB in the blueprint'''
        bp = cliVar.blueprint
        dci_in_file = cliVar.data_in_file['blueprint'][bp.label]['dci']
        fabric_settings_in_bp = bp.get_item('fabric-settings')
        if fabric_settings_in_bp['esi_mac_msb'] != dci_in_file['esi_mac_msb']:
            _ = bp.patch_item('fabric-settings', {'esi_mac_msb': dci_in_file['esi_mac_msb']})



@click.command()
@click.option('--file-format', type=click.Choice(['yaml', 'json']), default='yaml', help='File format')
@click.option('--file-folder', type=str, default='.', help='File folder')
@click.option('--bp-name', type=str, envvar='BP_NAME', help='Blueprint name')
@click.pass_context
def export_dci(ctx, bp_name: str, file_format: str, file_folder: str):
    """
    Export the DCI interconnect configuration in yaml, json format

    """
    logger = prep_logging('DEBUG', 'export_dci()')

    bp = cliVar.get_blueprint(bp_name, logger)
    if not bp:
        return

    dci_tree = cliVar.data_in_file['blueprint'][bp.label].setdefault('dci', {})

    pull_interconnect(bp, dci_tree)

    pull_ott(bp, dci_tree)

    DciEsiMacMsb.pull_msb()


    # write to file based on the format with the blueprint name
    file_name = f"{bp.label}.{file_format}"
    file_path = os.path.expanduser(f"{file_folder}/{file_name}")
    with open(file_path, 'w') as f:
        if'file_format' == 'json':
            f.write(json.dumps(cliVar.data_in_file, indent=2))
        else:
            f.write(yaml.dump(cliVar.data_in_file))



def create_interconnect(bp, ic_spec) -> str:
    """
    Create interconnect data in the blueprint

    """
    logger = prep_logging('DEBUG', 'create_interconnect()')

    posted = bp.post_item(INTERCONNECT, ic_spec)
    logger.debug(f"{posted=}, {posted.text=}, {posted.status_code=}")
    return posted.json()['id']


def import_interconnect():
    """
    Update interconnect data in the blueprint

    """
    logger = prep_logging('DEBUG', 'update_interconnect()')

    bp = cliVar.blueprint

    interconnect_in_blueprint = bp.get_item(INTERCONNECT)[INTERCONNECT]
    interconnect_in_file = cliVar.bp_in_file['dci']['interconnect']
    # conver to dictionary for easy access
    ic_data_in_bp = { x['label']: x for x in interconnect_in_blueprint}

    # iterate through the interconnects in the file
    for ic_datum_in_file in interconnect_in_file:
        ic_label = ic_datum_in_file['label']
        ic_datum_in_bp = ic_data_in_bp.get(ic_label, {})
        ic_id = ic_datum_in_bp.get('id', None)
        ic_spec = {
            'label': ic_datum_in_file['label'],
            'interconnect_route_target': ic_datum_in_file['interconnect_route_target'],
            'interconnect_esi_mac': ic_datum_in_file['interconnect_esi_mac']
        }
        # update if there is a change
        is_changed = False
        logger.info(f"{ic_label=}")        
        if not ic_id:
            # create the interconnect
            posted = bp.post_item(INTERCONNECT, ic_spec)
            logger.info(f"{posted=}, {posted.text=}, {posted.status_code=}")
            ic_id = posted.json()['id']
            # TODO:
            time.sleep(2)
            ic_datum_in_bp = [ x for x in bp.get_item(INTERCONNECT)[INTERCONNECT] if x['label'] == ic_label][0]
        if any([
            ic_datum_in_bp['interconnect_route_target'] != ic_datum_in_file['interconnect_route_target'],
            ic_datum_in_bp['interconnect_esi_mac'] != ic_datum_in_file['interconnect_esi_mac']
            ]):
            patched = bp.patch_item(f"{INTERCONNECT}/{ic_id}", ic_spec)
            logger.info(f"{patched=}, {patched.text=}, {patched.status_code=}")

        # import remote gateways
        remote_gateways_in_bp = { x['gw_name']: x for x in ic_datum_in_bp.get('remote_gateway_node_ids', {}).values()}
        remote_gateways_in_file = ic_datum_in_file['remote_gateway_node_ids']
        # remove the remote gateways those are not present in the file
        for rg_in_bp in remote_gateways_in_bp.values():
            if rg_in_bp['gw_name'] not in remote_gateways_in_file:
                rg_deleted = bp.delete_item(f"remote_gateways/{rg_in_bp['id']}")
                logger.info(f"{rg_deleted=}, {rg_deleted.text=}, {rg_deleted.status_code=}")
        # add or update the remote gateways in the file
        for rg_datum_in_file in remote_gateways_in_file.values():
            rg_name = rg_datum_in_file['gw_name']
            rg_datum_in_bp = remote_gateways_in_bp.get(rg_name, {})
            rg_datum_id = rg_datum_in_bp.get('id', None)
            rg_spec = {
                'gw_name': rg_datum_in_file['gw_name'],
                'gw_ip': rg_datum_in_file['gw_ip'],
                'gw_asn': rg_datum_in_file['gw_asn'],
                'ttl': rg_datum_in_file.get('ttl', 30),
                'keepalive_timer': rg_datum_in_file.get('keepalive_timer', 10),
                'holdtime_timer': rg_datum_in_file.get('holdtime_timer', 30),
                # 'local_gw_nodes': rg_datum_in_file['local_gw_nodes']
            }
            logger.info(f"{rg_name=}")
            # create one if not in the blueprint
            if not rg_datum_in_bp:
                # create the remote gateway
                rg_spec['evpn_interconnect_group_id'] = ic_id
                rg_spec['evpn_route_types'] = 'all'
                rg_spec['local_gw_nodes'] = [bp.get_system_node_from_label(x).ok_value['id'] for x in rg_datum_in_file['local_gw_nodes']]
                posted = bp.post_item("remote_gateways", rg_spec)
                logger.info(f"{posted=}, {posted.text=}, {posted.status_code=}")
                continue
            for variable in ['gw_ip', 'gw_asn', 'ttl', 'keepalive_timer', 'holdtime_timer']:
                if rg_datum_in_file[variable] != rg_datum_in_bp.get(variable, None):
                    is_changed = True
            # local_gw_nodes should be present always
            if is_changed or rg_datum_in_file['local_gw_nodes'] != [x['label'] for x in rg_datum_in_bp['local_gw_nodes']]:
                rg_spec['local_gw_nodes'] = [bp.get_system_node_from_label(x).ok_value['id'] for x in rg_datum_in_file['local_gw_nodes']]
            if is_changed:
                patched = bp.put_item(f"remote_gateways/{rg_datum_id}", rg_spec)
                logger.info(f"{patched=}, {patched.text=}, {patched.status_code=}")                
            else:
                logger.info(f"No change in remote gateway {rg_name}")

        # iterarte through the routing zones        
        security_zones_in_bp = { x['vrf_name']: x for x in ic_datum_in_bp.get('interconnect_security_zones', {}).values()}
        security_zones_in_file = ic_datum_in_file['interconnect_security_zones']
        rz_spec = ic_spec['interconnect_security_zones'] = {}
        for vrf_name, security_zone_in_file in security_zones_in_file.items():
            security_zone_in_bp = security_zones_in_bp[vrf_name]
            this_rz_spec = {}
            sz_id = security_zone_in_bp['security_zone_id']
            this_rz_spec['enabled_for_l3'] = security_zone_in_file['enabled_for_l3']
            if security_zone_in_file['enabled_for_l3'] != security_zone_in_bp['enabled_for_l3']:
                is_changed = True
            this_rz_spec['interconnect_route_target'] = security_zone_in_file['interconnect_route_target']
            if security_zone_in_file['interconnect_route_target'] != security_zone_in_bp['interconnect_route_target']:
                is_changed = True
            this_rz_spec['routing_policy_id'] = get_routing_policy_id(bp, security_zone_in_file['routing_policy_label'])
            rz_spec[sz_id] = this_rz_spec

        # iterate through the virtual networks
        virtual_networks_in_file = ic_datum_in_file['interconnect_virtual_networks']
        virtual_networks_in_bp = ic_datum_in_bp['interconnect_virtual_networks']
        vn_spec = ic_spec['interconnect_virtual_networks'] = {}
        for vn_id, virtual_network_in_bp in virtual_networks_in_bp.items():
            vn_label = virtual_network_in_bp['label']
            virtual_network_in_file = virtual_networks_in_file.get(vn_label, {})
            if virtual_network_in_file:
                if any([
                    virtual_network_in_file['translation_vni'] != virtual_network_in_bp['translation_vni'],
                    virtual_network_in_file['l2'] != virtual_network_in_bp['l2'],
                    virtual_network_in_file['l3'] != virtual_network_in_bp['l3']
                ]):
                    is_changed = True
                this_vn_spec = {
                    'translation_vni': virtual_network_in_file['translation_vni'],
                    'l2': virtual_network_in_file['l2'],
                    'l3': virtual_network_in_file['l3']
                }
            else:
                is_changed = True
                this_vn_spec = {
                    'translation_vni': virtual_network_in_bp['translation_vni'],
                    'l2': virtual_network_in_bp['l2'],
                    'l3': virtual_network_in_bp['l3']
                }
            if is_changed:
                vn_spec[vn_id] = this_vn_spec

        if is_changed:
            patched = bp.patch_item(f"{INTERCONNECT}/{ic_id}", ic_spec)
            logger.info(f"{patched=}, {patched.text=}, {patched.status_code=}")

    return


def import_ott():
    """
    Update OTT data in the blueprint

    """
    logger = prep_logging('DEBUG', 'import_ott()')
    pass


@click.command()
@click.option('--file-format', type=click.Choice(['yaml', 'json']), default='yaml', help='File format')
@click.option('--file-folder', type=str, default='.', help='File folder')
@click.option('--bp-name', type=str, envvar='BP_NAME', help='Blueprint name')
@click.pass_context
def import_dci(ctx, bp_name: str, file_format: str, file_folder: str):
    """
    Import the DCI interconnect configuration in yaml, json format
    """
    logger = prep_logging('DEBUG', 'import_dci()')

    # read the file based on the format with the blueprint name
    file_name = f"{bp_name}.{file_format}"
    file_path = os.path.expanduser(f"{file_folder}/{file_name}")
    cliVar.load_file(file_path, file_format)

    bp = cliVar.get_blueprint(bp_name, logger)
    if not bp:
        return


    import_interconnect()

    import_ott()

    DciEsiMacMsb.push_msb()
