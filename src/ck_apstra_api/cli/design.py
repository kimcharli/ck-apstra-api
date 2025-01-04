
from functools import cache
import click

from . import cliVar, prep_logging


@cache
def get_logical_device(logical_device_id: str) -> dict:
    """Get the logical device from the blueprint"""
    logical_device_data = cliVar.session.get_items(f"design/logical-devices/{logical_device_id}")
    return logical_device_data
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

    switch_query = "node('system', name='system', system_type='switch').out().node('interface_map', name='interface_map')"
    switch_nodes = cliVar.blueprint.query(switch_query).ok_value
    for nodes in switch_nodes:
        switch_in_bp = nodes['system']
        switch_label = switch_in_bp['label']
        interface_map_in_bp = nodes['interface_map']
        interface_map_label = interface_map_in_bp['label']
        logical_device_id = interface_map_in_bp['logical_device_id']
        logical_device_data = get_logical_device(logical_device_id)
        logical_device_name = logical_device_data.get('display_name', f"{logical_device_id}-not-found")
        node_in_file[switch_label] = {
            'label': switch_label,
            'system_type': switch_in_bp['system_type'],
            'hostname': switch_in_bp['hostname'],
            'interface_map': interface_map_in_bp['label'],
            'role': switch_in_bp['role'],
        }
        interface_map_in_file[interface_map_label] = {
            'logical_device': logical_device_name,
            'device_profile': interface_map_in_bp['device_profile_id'],
        }
        logical_device_in_file[logical_device_name] = {'panels': logical_device_data.get('panels', [])}

    cliVar.export_file(file_folder, file_format)
    

