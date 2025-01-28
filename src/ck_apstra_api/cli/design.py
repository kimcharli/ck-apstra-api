
from dataclasses import dataclass
from typing import Any, Dict
import click

from . import cliVar, prep_logging


# TODO: should be dataclass?
# @dataclass
# class BlueprintVar:
#     """Local variables for the module"""
#     bp_name: str
#     bp: Any  = None # reference to cliVar.blueprint
#     # logical_device_map: dict = {}  # internal variable: {id: label}
#     interface_map_map: Dict = None  # internal variable: {id: label}
#     # catalog_in_file: dict # reference to bp_in_file['catalog']
#     # logical_device: Dict = None  # reference to catalog_in_file['logical_device']
#     # interface_map_in_file: dict  # reference to catalog_in_file['interface_map']    
#     # phsical_in_file: dict  # reference to bp_in_file['physical']
#     # physical_node_in_file: dict  # reference to catalog_in_file['physical']['node']
#     # system_map: dict  # internal variable: {id: label}
#     # rack_type_map: dict  # internal variable: {rack-id: rack-label}

#     def __post_init__(self):
#         self.bp = cliVar.get_blueprint(self.bp_name)
#         self.catalog_in_file = cliVar.bp_in_file.catalog
#         self.interface_map_in_file = self.catalog_in_file.interface_map
#         self.physical_in_file = cliVar.bp_in_file.physical
#         self.system_map = {}
#         self.interface_map_map = {}
#         # self.get_rack_type_map_from_blueprint()
#         self.rack_type_map = cliVar.data_in_file.get_rack_type_map_from_blueprint()

# # bp_vars = None


@click.command()
@click.option('--file-format', type=str, default='', help='File format (yaml, json)')
@click.option('--file-folder', type=str, default='', help='File folder')
@click.option('--bp-name', type=str, envvar='BP_NAME', help='Blueprint name')
def export_design(bp_name: str, file_format: str, file_folder: str):
    """
    Export the Logical Devices, Interface Maps, ... within a blueprint in yaml, json format


    """
    # global bp_vars
    logger = prep_logging('DEBUG', 'export_resources()')
    # TODO: dataclass for bp_in_file

    cliVar.update(file_folder=file_folder, file_format=file_format, bp_name=bp_name)
    ck_bp = cliVar.get_blueprint()
    # bp_vars = BlueprintVar(bp_name)
    if not ck_bp:
        logger.error(f"Blueprint {bp_name} not found")
        return
    
    # bp_vars.get_logical_device_map_from_blueprint()
    logical_device_map = cliVar.data_in_file.get_logical_device_map_from_blueprint()
    interface_map_map = cliVar.data_in_file.get_interface_map_map_from_blueprint()
    system_map = cliVar.data_in_file.get_system_nodes_from_blueprint()

    cliVar.export_file()
    
