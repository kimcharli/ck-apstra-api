
from functools import cache
import json
import click

from . import cliVar, prep_logging


@cache
def get_logical_device(logical_device_id: str) -> dict:
    """Get the logical device from the blueprint"""
    # logical_device_data = cliVar.session.get_items(f"design/logical-devices/{logical_device_id}")
    if not logical_device_id:
        return None
    logical_device = cliVar.blueprint.query(f"node(id='{logical_device_id}', name='n')").ok_value
    try:
        if 'json' in logical_device[0]['n']:
            return json.loads(logical_device[0]['n']['json'])
    except Exception as e:
        print(f"Error: {e}, {logical_device_id=}")
        raise e
    breakpoint()
    return None

@cache
def get_device_profile_label(device_profile_id: str) -> dict:
    """Get the device profile from the blueprint"""
    if not device_profile_id:
        return None
    device_profile_data = cliVar.blueprint.query(f"node(id='{device_profile_id}', name='n')").ok_value
    if device_profile_data[0]['n']:
        return device_profile_data[0]['n']['label']
    return None

@cache 
def get_interface_map_label(interface_map_id: str) -> dict:
    """Get the interface map from the blueprint"""
    if not interface_map_id:
        return None
    interface_map_data = cliVar.session.get_items(f"design/interface-maps/{interface_map_id}")
    if 'label' in interface_map_data:
        return interface_map_data['label']    
    breakpoint()



@click.command()
@click.option('--file-format', type=click.Choice(['yaml', 'json']), default='yaml', help='File format')
@click.option('--file-folder', type=str, default='.', help='File folder')
@click.option('--bp-name', type=str, envvar='BP_NAME', help='Blueprint name')
@click.pass_context
def export_design(ctx, bp_name: str, file_format: str, file_folder: str):
    """
    Export the Resources in yaml, json format

    """
    logger = prep_logging('DEBUG', 'export_resources()')

    bp = cliVar.get_blueprint(bp_name, logger)
    if not bp:
        return

    catalog_in_file = cliVar.bp_in_file['catalog'] = {}
    logical_device_in_file = catalog_in_file['logical_device'] = {}
    interface_map_in_file = catalog_in_file['interface_map'] = {}
    physical_in_file = catalog_in_file['physical'] = {}
    node_in_file = physical_in_file['node'] = {}

    system_info_results = bp.get_item("experience/web/system-info", 
        params={'type': 'staging', 'comment': 'system-nodes'})
    # breakpoint()
    # switch_query = "node('system', name='system', system_type='switch').out().node('interface_map', name='interface_map')"
    # switch_nodes = cliVar.blueprint.query(switch_query).ok_value
    # for nodes in switch_nodes:
    #     switch_in_bp = nodes['system']
    #     switch_label = switch_in_bp['label']
    #     interface_map_in_bp = nodes['interface_map']
    #     interface_map_label = interface_map_in_bp['label']
    #     logical_device_id = interface_map_in_bp['logical_device_id']
    #     logical_device_data = get_logical_device(logical_device_id)
    #     logical_device_name = logical_device_data.get('display_name', f"{logical_device_id}-not-found")
    #     node_in_file[switch_label] = {
    #         'label': switch_label,
    #         'system_type': switch_in_bp['system_type'],
    #         'hostname': switch_in_bp['hostname'],
    #         'interface_map': interface_map_in_bp['label'],
    #         'role': switch_in_bp['role'],
    #     }
    #     interface_map_in_file[interface_map_label] = {
    #         'logical_device': logical_device_name,
    #         'device_profile': interface_map_in_bp['device_profile_id'],
    #     }
    #     logical_device_in_file[logical_device_name] = {'panels': logical_device_data.get('panels', [])}
    for system_info in system_info_results['data']:
        system_id = system_info['system_id']
        system_name = system_info['label']
        # system_interface_map = system_info['interface_map_id']
        system_interface_map_label = get_interface_map_label(system_info['interface_map_id'])
        # system_logical_device = get_logical_device(system_info['logical_device_id'])
        system_logical_device = get_logical_device(system_info['logical_device_id'])
        system_device_profile_label = get_device_profile_label(system_info['device_profile_id'])
        system_loopback_ipv4 = getattr(system_info, 'loopback', {}).get('ipv4_addr', None)
        system_loopback_ipv6 = getattr(system_info, 'loopback', {}).get('ipv6_addr', None)
        node_in_file[system_name] = {
            'label': system_name,
            'tags': system_info['tags'],
            'role': system_info['role'],
            'external': system_info['external'],
            'deploy_mode': system_info['deploy_mode'],
            'device_profile': system_device_profile_label,
            'hostname': system_info['hostname'],
            'asn': system_info['domain_id'],
            'loopback_ipv4': system_loopback_ipv4,
            'loopback_ipv6': system_loopback_ipv6,

            'interface_map': system_interface_map_label,
        }
        if system_info['interface_map_id']:
            interface_map_in_file[system_interface_map_label] = {
                'logical_device': system_logical_device,
                'device_profile': system_device_profile_label,
            }
        if system_logical_device:
            system_logical_device_name = system_logical_device['display_name']
            if system_logical_device_name not in logical_device_in_file:
                # breakpoint()
                logical_device_in_file[system_logical_device_name] = {'panels': system_logical_device['panels']} 


    cliVar.export_file(file_folder, file_format)
    

