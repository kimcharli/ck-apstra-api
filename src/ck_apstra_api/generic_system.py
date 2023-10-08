
import logging
import pandas as pd
from math import isnan
from pathlib import Path
from pydantic import BaseModel, validator, StrictStr, field_validator, Field
from typing import List, Optional, Any, TypeVar, Annotated
import numpy as np
import os
import uuid

import click

from ck_apstra_api.apstra_session import prep_logging
from ck_apstra_api.cli import CkJobEnv
from ck_apstra_api.apstra_blueprint import CkApstraBlueprint, CkEnum

class GenericSystemModel(BaseModel):
    """
    The variables from the excel sheet generic_systems
    """
    blueprint: str
    system_label: str
    is_external: Optional[bool] = False
    speed: str               # 10G 
    lag_mode: Optional[str]  # mandatory in case of multiple interfaces
    tags: List[str] = Field(default = [])  # deprecated
    gs_tags: List[str] = Field(default = [])

    label1: str
    ifname1: str
    gs_ifname1: Optional[str]
    tags1: List[str] = Field(default = [])

    label2: Optional[str]
    ifname2: Optional[str]
    gs_ifname2: Optional[str]
    tags2: List[str] = Field(default = [])

    label3: Optional[str]
    ifname3: Optional[str]
    gs_ifname3: Optional[str]
    tags3: List[str] = Field(default = [])

    label4: Optional[str]
    ifname4: Optional[str]
    gs_ifname4: Optional[str]
    tags4: List[str] = Field(default = [])

    untagged_vlan: Optional[int] = None
    tagged_vlans: Optional[List[int]] = None
    ct_names: Optional[List[str]] = None
    comment: Optional[str] = None

    # convert to string in case an int is given
    @field_validator('gs_ifname1', 'gs_ifname2', 'gs_ifname3', 'gs_ifname4', mode='before')
    @classmethod
    def conver_to_string(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return v
        return str(v)

    @field_validator('tagged_vlans', mode='before')
    @classmethod
    def convert_to_list_of_int(cls, v):
        if v is None:
            return None
        if isinstance(v, int):
            return [v]
        return [ x.strip() for x in v.split(',')]

    @field_validator('is_external', mode='before')
    @classmethod
    def convert_to_bool(cls, v):
        if isinstance(v, str) and v == 'yes':
            return True
        return False

    @field_validator('tags', 'gs_tags', 'tags1', 'tags2', 'tags3', 'tags4', 'ct_names', mode='before')
    @classmethod
    def convert_to_list_of_str(cls, v):
        if v is None:
            return []
        return [ x.strip() for x in v.split(',')]

generic_system_data = {} # { blueprint: { generic_system: {....}}}


def process_row(row):
    blueprint_label = row['blueprint']
    blueprint_data = generic_system_data.setdefault(blueprint_label, {})
    system_label = row['system_label']
    system_data = blueprint_data.setdefault(system_label,[])
    # logging.debug(f"{generic_system_data}")
    pydantic_data = GenericSystemModel(**row)
    system_data.append(pydantic_data.model_dump())
    # logging.debug(f"{pydantic_data=}")


def read_generic_systems(input_file_path_string: str = None, sheet_name: str = 'generic_systems'):
    excel_file_sting = input_file_path_string or os.getenv('excel_input_file')
    input_file_path = Path(excel_file_sting) 
    df = pd.read_excel(input_file_path, sheet_name=sheet_name, header=[1])
    df = df.replace({np.nan: None})

    df.apply(process_row, axis=1)
    return generic_system_data

@click.command(name='read-generic-systems')
def click_read_generic_systems():
    job_env = CkJobEnv()
    generic_systems = read_generic_systems(job_env.excel_input_file, 'generic_systems')
    for bp_label, bp_data in generic_systems.items():
        logging.debug(f"{bp_label=}")
        for gs_label, gs_links_list in bp_data.items():
            logging.debug(f"{gs_label=}")
            for link in gs_links_list:
                logging.debug(f"{link=}")

def form_lacp(job_env: CkJobEnv, generic_system_label: str, generic_system_links_list: list):
    bp = job_env.main_bp
    bp_label = bp.label
    lag_spec = {
        'links': {
            # <link_node_id>: {
            #     'group_label': group_label,
            #     'lag_mode': lag_mode,
            # }
        }
    }
    link_id_num = 0
    for link in generic_system_links_list:
        lag_mode = link['lag_mode']
        if lag_mode is None:
            # logging.debug(f"Skipping: Generic system {generic_system_label} has no lag_mode")
            continue                
        if lag_mode not in [ 'lacp_active', 'lacp_passive']:
            logging.warning(f"Skipping: Generic system {generic_system_label} has invalid lag_mode {lag_mode}")
            continue
        link_id_num += 1
        group_label = f"link{link_id_num}"
        # iterate over the 4 member interfaces
        for member_number in range(4):
            member_number += 1
            sw_label = link[f"label{member_number}"]
            sw_ifname = link[f"ifname{member_number}"]
            gs_ifname = link[f"gs_ifname{member_number}"]
            # skip if now switch is defined
            if not sw_label or not sw_ifname:
                continue
            if sw_ifname[:2] not in ['et', 'xe', 'ge']:
                logging.warning(f"Skipping: Generic system {generic_system_label} has invalid interface name {sw_ifname}")
                continue
            switch_link_nodes = bp.get_switch_interface_nodes([sw_label], sw_ifname)
            if switch_link_nodes is None or len(switch_link_nodes) == 0:
                logging.warning(f"Skipping: Generic system {generic_system_label} has invalid interface {sw_label}:{sw_ifname}")
                continue
            link_node_id = switch_link_nodes[0][CkEnum.LINK]['id']
            sw_if_node_id = switch_link_nodes[0][CkEnum.MEMBER_INTERFACE]['id']
            gs_if_node_id = switch_link_nodes[0][CkEnum.GENERIC_SYSTEM_INTERFACE]['id']
            link_spec = {
                'group_label': group_label,
                'lag_mode': lag_mode,
            }
            lag_spec['links'][link_node_id] = link_spec
            # logging.warning(f"{gs_links_list=}, {link_spec=}, {sw_label=}, {sw_ifname=}")
            
    # update LACP
    if len(lag_spec['links']) > 0:
        logging.debug(f"{lag_spec=}")
        lag_updated = bp.patch_leaf_server_link_labels(lag_spec)
        if lag_updated:
            logging.warning(f"Unexpected return: LACP updated for generic system {generic_system_label} in blueprint {bp_label}: {lag_updated}")
        # logging.debug(f"lag_updated: {lag_updated}")
    

def add_tags(job_env: CkJobEnv, generic_system_label: str, generic_system_links_list: list):
    bp = job_env.main_bp
    bp_label = bp.label
    link_id_num = 0
    generic_system_node = bp.get_system_node_from_label(generic_system_label)
    if generic_system_node is None:
        logging.warning(f"Skipping: Generic system {generic_system_label} does not exist in blueprint {bp_label}")
        return
    generic_system_id = generic_system_node['id']
    for link in generic_system_links_list:
        link_id_num += 1
        group_label = f"link{link_id_num}"
        gs_tags = link['gs_tags']
        if len(gs_tags) > 0:
            bp.post_tagging(generic_system_id, tags_to_add=gs_tags)            
        # iterate over the 4 member interfaces        
        for member_number in range(4):
            member_number += 1
            sw_label = link[f"label{member_number}"]
            sw_ifname = link[f"ifname{member_number}"]
            gs_ifname = link[f"gs_ifname{member_number}"]
            member_tags = link[f"tags{member_number}"]  # list of string(tag)
            # the switch label and the interface should be defined. If not, skip
            if not sw_label or not sw_ifname:
                continue
            # the switch interface name should be legit
            if sw_ifname[:2] not in ['et', 'xe', 'ge']:
                logging.warning(f"Skipping: Generic system {generic_system_label} has invalid interface name {sw_ifname}")
                continue
            switch_link_nodes = bp.get_switch_interface_nodes(sw_label, sw_ifname)
            if switch_link_nodes is None or len(switch_link_nodes) == 0:
                logging.warning(f"Skipping: Generic system {generic_system_label} has invalid interface {sw_label}:{sw_ifname}")
                continue
            link_node_id = switch_link_nodes[0][CkEnum.LINK]['id']
            # logging.debug(f"{member_tags=}")
            if len(member_tags) > 0:
                logging.debug(f"{member_tags=}")
                bp.post_tagging(link_node_id, tags_to_add=member_tags)
                


def rename_generic_system_intf(job_env: CkJobEnv, generic_system_label: str, generic_system_links_list: list):
    bp = job_env.main_bp
    bp_label = bp.label
    patch_cable_map_spec = {
        'links': [
            # {
            #     'endpoints': [
            #         {
            #             'interface': {
            #                 'id': <switch_intf_node_id>
            #             }
            #         },
            #         {
            #             'interface': {
            #                 'id': <generic_system_intf_node_id>,
            #                 'if_name': <generci_system_ifname>,
            #             }
            #         }
            #     ],
            #     'id': <link_node_id>
            # }
        ]
    }
    link_id_num = 0
    for link in generic_system_links_list:
        link_id_num += 1
        group_label = f"link{link_id_num}"
        for member_number in range(4):
            member_number += 1
            sw_label = link[f"label{member_number}"]
            sw_ifname = link[f"ifname{member_number}"]
            gs_ifname = link[f"gs_ifname{member_number}"]
            # skip if data is missing
            if not sw_label or not sw_ifname:
                continue
            if sw_ifname[:2] not in ['et', 'xe', 'ge']:
                logging.warning(f"Skipping: Generic system {generic_system_label} has invalid interface name {sw_ifname}")
                continue
            switch_link_nodes = bp.get_switch_interface_nodes([sw_label], sw_ifname)
            # logging.warning(f"{sw_label=}, {sw_ifname=}, {len(switch_link_nodes)=}")
            # logging.debug(f"{label_label=}, {link[label_label]=}")
            # logging.debug(f"{len(switch_link_nodes)=}, {switch_link_nodes=}")
            if switch_link_nodes is None or len(switch_link_nodes) == 0:
                logging.warning(f"Skipping: Generic system {generic_system_label} has invalid interface {sw_label}:{sw_ifname}")
                continue
            link_node_id = switch_link_nodes[0][CkEnum.LINK]['id']
            sw_if_node_id = switch_link_nodes[0][CkEnum.MEMBER_INTERFACE]['id']
            gs_if_node_id = switch_link_nodes[0][CkEnum.GENERIC_SYSTEM_INTERFACE]['id']
            
            # patch_cable_map_spec
            if gs_ifname is not None and len(gs_ifname):
                patch_cable_map_spec['links'].append({
                    'endpoints': [
                        {
                            'interface': {
                                'id': sw_if_node_id
                            }
                        },
                        {
                            'interface': {
                                'id': gs_if_node_id,
                                'if_name': gs_ifname,
                            }
                        }

                    ],
                    'id': link_node_id                            
                })

    # upddate generic system interface names
    if len(patch_cable_map_spec['links']) > 0:
        logging.debug(f"{patch_cable_map_spec=}")
        patch_cable_map_spec_updated = bp.patch_cable_map(patch_cable_map_spec)
        if patch_cable_map_spec_updated:
            logging.warning(f"Unexpected return: cable map updated for generic system {generic_system_label} in blueprint {bp_label}: {patch_cable_map_spec_updated}")
        # logging.debug(f"patch_cable_map_spec_updated: {patch_cable_map_spec_updated}"


def assign_connectivity_templates(job_env: CkJobEnv, generic_system_label: str, gs_links_list: list):
    # update connectivity templates - this should be run after lag update
    bp = job_env.main_bp
    bp_label = bp.label
    ct_assign_spec = {
        'application_points': [
            # {
            #     'id': <interface_id>,
            #     'policies': [
            #         {
            #             'policy': <ct-id>,
            #             'used': True,
            #         }
            #     ]
            # }
        ]

    }
    for link in gs_links_list:
        # ct_names takes precedence
        ct_names = link['ct_names']
        untagged_vlan = link['untagged_vlan']
        tagged_vlans = link['tagged_vlans']
        ct_ids = []
        if (ct_names and len(ct_names) == 0) and untagged_vlan is None and len(tagged_vlans) == 0:
            logging.debug(f"Skipping: Generic system {generic_system_label} has no CTs {link=}")
            continue
        if ct_names:
            ct_ids = bp.get_ct_ids(ct_names)
            if len(ct_ids) != len(ct_names):
                logging.error(f"Skipping: Generic system {generic_system_label} has wrong data {ct_names=} {ct_ids=}")
                continue
        else:
            # can have untagged too
            # TODO: check if the CTs exist and create if not
            # TODO: naming rule
            if link['tagged_vlans']:
                for tagged_vlan_id in link['tagged_vlans']:
                    ct_ids.append(bp.get_single_vlan_ct_or_create(tagged_vlan_id, is_tagged=True))
                # logging.debug(f"{untagged_vlan=}, {ct_ids=}")
            if untagged_vlan:
                # conentional name: vn123-untagged
                # untagged_vlan_name = f"vn{untagged_vlan_id}-untagged"
                # ct_ids = bp.get_ct_ids([untagged_vlan_name])
                # if len(ct_ids) != 1:
                #     added = bp.add_single_vlan_ct(200000 + untagged_vlan_id, untagged_vlan_id, is_tagged=False)
                #     logging.debug(f"Added CT {untagged_vlan_name}: {added}")
                # ct_ids = bp.get_ct_ids([untagged_vlan_name])
                # logging.debug(f"{untagged_vlan_name=}, {ct_ids=}")
                ct_ids.append(bp.get_single_vlan_ct_or_create(untagged_vlan, is_tagged=False))
                logging.debug(f"{untagged_vlan=}, {ct_ids=}")
        if 'ct_ids' not in locals():
            logging.debug(f"Skipping: Generic system {generic_system_label} has no CTs")
            continue
        logging.debug(f"{link=} {ct_ids=}")
        intf_nodes = bp.get_switch_interface_nodes([link['label1']], link['ifname1'])
        if len(intf_nodes) == 0:
            logging.warning(f"{len(intf_nodes)=}, {intf_nodes=}")
            logging.warning(f"Skipping: Generic system {generic_system_label} has invalid interface {link['label1']}:{link['ifname1']}")
            continue
        ap_id = None
        if intf_nodes[0][CkEnum.EVPN_INTERFACE]:
            ap_id = intf_nodes[0][CkEnum.EVPN_INTERFACE]['id']
        else:
            ap_id = intf_nodes[0][CkEnum.MEMBER_INTERFACE]['id']
        ct_assign_spec['application_points'].append({
            'id': ap_id,
            'policies': [{ 'policy': ct_id, 'used': True } for ct_id in ct_ids]
        })

    if len(ct_assign_spec['application_points']) > 0:
        # logging.debug(f"{ct_assign_spec=}")
        ct_assign_updated = bp.patch_obj_policy_batch_apply(ct_assign_spec, params={'async': 'full'})
        logging.debug(f"CT assign updated for generic system {generic_system_label} in blueprint {bp_label}: {ct_assign_updated} {ct_assign_spec=}")
        # logging.debug(f"ct_assign_updated: {ct_assign_updated}"



def add_generic_systems(job_env: CkJobEnv, generic_systems: dict):
    """
    Add the generic systems to the Apstra server from the given generic systems data.

    Generic systems data:
    {
        <blueprint_label>: {
            <generic_system_label>: [
                {
                    "blueprint": "blueprint1",
                    "system_label": "generic_system1",
                    "is_external": false,
                    "speed": "10G",
                    "lag_mode": null,
 
                    "label1": "eth1",
                    "ifname1": "eth1",
                    "gs_ifname1": null,

                    "label2": null,
                    "ifname2": null,
                    "gs_ifname2": null,

                    "label3": null,
                    "ifname3": null,
                    "gs_ifname3": null,

                    "label4": null,
                    "ifname4": null,
                    "gs_ifname4": null,

                    "ct_names": null,
                    "comment": null
                }
            ]
        }
    }
    """

    ## create the generic systems
    bp_total = len(generic_systems)  # total number of blueprints
    bp_count = 0
    logging.info(f"Adding generic systems to {bp_total} blueprints")
    for bp_label, bp_data in generic_systems.items():
        bp_count += 1
        logging.info(f"Adding generic systems to blueprint {bp_count}/{bp_total}: {bp_label}")
        bp = CkApstraBlueprint(job_env.session, bp_label)
        # logging.debug(f"{bp=}, {bp.id=}")
        gs_total = len(bp_data)
        gs_count = 0
        logging.info(f"Adding {gs_total} generic systems to blueprint {bp_label}")
        for gs_label, gs_links_list in bp_data.items():
            gs_count += 1
            gs_link_total = len(gs_links_list)
            logging.info(f"Adding generic system {gs_count}/{gs_total}: {gs_label} with {gs_link_total} links")
            if bp.get_system_node_from_label(gs_label):
                logging.info(f"Skipping: Generic system {gs_label} already exists in blueprint {bp_label}")
                continue
            # if gs_link_total > 1:
            #     logging.warning(f"Adding generic system {gs_label} with {gs_link_total} links\n{gs_links_list}")
            #     return
            generic_system_spec = {
                'links': [],
                'new_systems': [],
            }
            # to form logical device
            speed_count = {}
            system_type = 'server'

            for link in gs_links_list:
            #     logging.debug(f"{link=}")
                link_speed = link['speed']
                system_type = 'external' if link['is_external'] else 'server'
                for link_number in range(4):
                    link_id_num = link_number + 1
                    label_label = f"label{link_id_num}"
                    this_ifname = link[f"ifname{link_id_num}"]
                    # skip if data is missing
                    if not link[label_label]:
                        continue
                    if this_ifname[:2] not in ['et', 'xe', 'ge']:
                        logging.warning(f"Skipping: Generic system {gs_label} has invalid interface name {this_ifname}")
                        continue
                    logging.debug(f"{label_label=}, {link[label_label]=}")
                    switch_id = bp.get_system_node_from_label(link[label_label])['id']
                    link_spec = {
                        'switch': {
                            'system_id': switch_id,
                            'transformation_id': bp.get_transformation_id(link[f"label{link_id_num}"], this_ifname , link_speed),
                            'if_name': link[f"ifname{link_id_num}"],
                        },
                        'system': {
                            'system_id': None,
                        },
                        # 'lag_mode':link['lag_mode'],
                        'lag_mode': None,
                    }
                    generic_system_spec['links'].append(link_spec)
                    # speed_count[link_speed] = getattr(speed_count, link_speed, 0) + 1
                    logging.debug(f"{link_speed=}, {speed_count=}")
                    if link_speed not in speed_count:
                        speed_count[link_speed] = 1
                    else:
                        speed_count[link_speed] += 1

            new_system = {
                'system_type': system_type,
                'label': gs_label,
                'port_channel_id_min': 0,
                'port_channel_id_max': 0,
                'logical_device': {
                    'display_name': None,
                    'id': None,
                    'panels': [
                        {
                            'panel_layout': {
                                'row_count': 1,
                                'column_count': sum(speed_count.values()),
                            },
                            'port_indexing': {
                                'order': 'T-B, L-R',
                                'start_index': 1,
                                'schema': 'absolute'
                            },
                            "port_groups": [
                                # {
                                #     "count": 4,
                                #     "speed": {
                                #         "unit": "G",
                                #         "value": 10
                                #     },
                                #     "roles": [
                                #         "leaf",
                                #         "access"
                                #     ]
                                # }
                            ]
                        }
                    ]
                },
            }
            display_name = 'auto'
            for speed, count in speed_count.items():
                port_group = {
                    'count': count,
                    'speed': {
                        'unit': speed[-1],
                        'value': int(speed[:-1]),
                    },
                    'roles': ['leaf', 'access'],
                }
                new_system['logical_device']['panels'][0]['port_groups'].append(port_group)
                display_name = f"{display_name}-{count}x{speed}"
            new_system['logical_device']['display_name'] = display_name
            new_system['logical_device']['id'] = display_name
            generic_system_spec['new_systems'].append(new_system)
            logging.debug(f"{generic_system_spec=}, {speed_count=}")

            generic_system_created = bp.add_generic_system(generic_system_spec)
            logging.info(f"Generic system {gs_label} created in blueprint {bp_label}")

        ## form LACP in the BP iterating over the generic systems
        for gs_label, gs_links_list in bp_data.items():
            form_lacp(job_env, gs_label, gs_links_list)
            add_tags(job_env, gs_label, gs_links_list)
            rename_generic_system_intf(job_env, gs_label, gs_links_list)

            # # update connectivity templates - this should be run after lag update
            # assign_connectivity_templates(job_env, gs_label, gs_links_list)


@click.command(name='add-generic-systems')
def click_add_generic_systems():
    job_env = CkJobEnv()
    generic_systems = read_generic_systems(job_env.excel_input_file, 'generic_systems')
    add_generic_systems(job_env, generic_systems)


@click.command(name='assign-connectivity-templates')
def click_assign_connecitivity_templates():
    job_env = CkJobEnv()
    generic_systems = read_generic_systems(job_env.excel_input_file, 'generic_systems')
    bp_total = len(generic_systems)  # total number of blueprints
    bp_count = 0
    logging.info(f"Adding connecitivity templates to {bp_total} blueprints")
    for bp_label, bp_data in generic_systems.items():
        bp_count += 1
        logging.info(f"Adding connecitivity templates to blueprint {bp_count}/{bp_total}: {bp_label}")
        bp = CkApstraBlueprint(job_env.session, bp_label)
        # logging.debug(f"{bp=}, {bp.id=}")
        gs_total = len(bp_data)
        gs_count = 0
        logging.info(f"Adding {gs_total} generic systems to blueprint {bp_label}")
        for gs_label, gs_links_list in bp_data.items():
            form_lacp(job_env, gs_label, gs_links_list)
            assign_connectivity_templates(job_env, gs_label, gs_links_list)

if __name__ == "__main__":
    click_add_generic_systems()

