
import logging
from math import isnan
from pathlib import Path
from typing import List, Optional, Any, TypeVar, Annotated
import os
import uuid

from result import Result, Ok, Err

from ck_apstra_api.apstra_session import CkApstraSession
from ck_apstra_api.apstra_blueprint import CkApstraBlueprint, CkEnum


def form_lacp(apstra_bp, generic_system_label: str, generic_system_links_list: list):
    # bp = job_env.main_bp
    bp = apstra_bp
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
            logging.warning(f"form_lacp Skipping: Generic system {generic_system_label} has invalid lag_mode {lag_mode}")
            continue
        link_id_num += 1
        group_label = f"link{link_id_num}"
        # iterate over the 4 member interfaces and links list
        for member_number in range(4):
            member_number += 1
            sw_label = link[f"label{member_number}"] if f"label{member_number}" in link else link[f"switch{member_number}"]
            sw_ifname = link[f"ifname{member_number}"] if f"ifname{member_number}" in link else link[f"switch_intf{member_number}"]
            gs_ifname = link[f"gs_ifname{member_number}"] if f"gs_ifname{member_number}" in link else link[f"server_intf{member_number}"]
            # skip if now switch is defined
            if not sw_label or not sw_ifname:
                continue
            if sw_ifname[:2] not in ['et', 'xe', 'ge']:
                # TODO: should fail on input validation
                logging.warning(f"form_lacp Skipping: Switch for {generic_system_label}, {sw_ifname[:2]} has invalid interface name {sw_ifname}:{sw_ifname}")
                continue
            switch_link_nodes_result = bp.get_switch_interface_nodes([sw_label], sw_ifname)
            if isinstance(switch_link_nodes_result, Err):
                return Err(f"form_lacp Err: {sw_label}:{sw_ifname} not found in blueprint {bp.label}")
            switch_link_nodes = switch_link_nodes_result.ok_value
            if switch_link_nodes is None or len(switch_link_nodes) == 0:
                logging.warning(f"form_lacp Skipping: Generic system {generic_system_label} has invalid interface {sw_label}:{sw_ifname}")
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
    

# def add_tags(job_env: CkJobEnv, generic_system_label: str, generic_system_links_list: list):
#     bp = job_env.main_bp
def add_tags(apstra_bp, generic_system_label: str, generic_system_links_list: list) -> Result[str, str]:
    bp = apstra_bp
    link_id_num = 0
    generic_system_node_result = bp.get_system_node_from_label(generic_system_label)
    if isinstance(generic_system_node_result, Err):
        logging.warning(f"add_tags skipping: {generic_system_node_result.err_value}")
        return Err(f"add_tags {generic_system_label} not found in blueprint {bp.label}")
    generic_system_node = generic_system_node_result.ok_value
    if not generic_system_node:
        return Err(f"add_tags {generic_system_label} not found in blueprint {bp.label}")
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
            # take care of old one like label1, label2, label3, label4
            sw_label = link[f"label{member_number}"] if f"label{member_number}" in link else link[f"switch{member_number}"]
            sw_ifname = link[f"ifname{member_number}"] if f"ifname{member_number}" in link else link[f"switch_intf{member_number}"]
            gs_ifname = link[f"gs_ifname{member_number}"] if f"gs_ifname{member_number}" in link else link[f"server_intf{member_number}"]
            member_tags = link[f"tags{member_number}"]  if f"tags{member_number}" in link else [] # list of string(tag)
            # the switch label and the interface should be defined. If not, skip
            if not sw_label or not sw_ifname:
                continue
            # the switch interface name should be legit
            if sw_ifname[:2] not in ['et', 'xe', 'ge']:
                logging.warning(f"Skipping: Generic system {generic_system_label} has invalid interface name {sw_ifname}")
                continue
            switch_link_nodes_result = bp.get_switch_interface_nodes(sw_label, sw_ifname)
            if isinstance(switch_link_nodes_result, Err):
                return Err(f"add_tags Err: {sw_label}:{sw_ifname} not found in blueprint {bp.label}")
            switch_link_nodes = switch_link_nodes_result.ok_value
            if switch_link_nodes is None or len(switch_link_nodes) == 0:
                logging.warning(f"Skipping: Generic system {generic_system_label} has invalid interface {sw_label}:{sw_ifname}")
                continue
            link_node_id = switch_link_nodes[0][CkEnum.LINK]['id']
            # logging.debug(f"{member_tags=}")
            if len(member_tags) > 0:
                logging.debug(f"{member_tags=}")
                bp.post_tagging(link_node_id, tags_to_add=member_tags)
                
    return Ok('done')

# def rename_generic_system_intf(job_env: CkJobEnv, generic_system_label: str, generic_system_links_list: list):
#     bp = job_env.main_bp
def rename_generic_system_intf(apstra_bp, generic_system_label: str, generic_system_links_list: list):
    bp = apstra_bp
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
            sw_label = link[f"label{member_number}"] if f"label{member_number}" in link else link[f"switch{member_number}"]
            sw_ifname = link[f"ifname{member_number}"] if f"ifname{member_number}" in link else link[f"switch_intf{member_number}"]
            gs_ifname = link[f"gs_ifname{member_number}"] if f"gs_ifname{member_number}" in link else link[f"server_intf{member_number}"]
            # skip if data is missing
            if not sw_label or not sw_ifname:
                continue
            if sw_ifname[:2] not in ['et', 'xe', 'ge']:
                logging.warning(f"Skipping: Generic system {generic_system_label} has invalid interface name {sw_ifname}")
                continue
            switch_link_nodes_result = bp.get_switch_interface_nodes([sw_label], sw_ifname)
            # logging.warning(f"{sw_label=}, {sw_ifname=}, {len(switch_link_nodes)=}")
            # logging.debug(f"{label_label=}, {link[label_label]=}")
            # logging.debug(f"{len(switch_link_nodes)=}, {switch_link_nodes=}")
            if isinstance(switch_link_nodes_result, Err):
                return Err(f"rename_generic_system_intf Err: {sw_label}:{sw_ifname} not found in blueprint {bp.label}\n\t get_switch_interface_nodes {switch_link_nodes_result.err_value}") 
            switch_link_nodes = switch_link_nodes_result.ok_value
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


# def assign_connectivity_templates(job_env: CkJobEnv, generic_system_label: str, gs_links_list: list):
#     # update connectivity templates - this should be run after lag update
#     bp = job_env.main_bp
def assign_connectivity_templates(apstra_bp, generic_system_label: str, gs_links_list: list):
    # update connectivity templates - this should be run after lag update
    bp = apstra_bp
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
        # untagged_vlan = link['untagged_vlan']
        # tagged_vlans = link['tagged_vlans']
        ct_ids = []
        # if (ct_names and len(ct_names) == 0) and untagged_vlan is None and len(tagged_vlans) == 0:
        if ct_names and len(ct_names) == 0:
            logging.debug(f"Skipping: Generic system {generic_system_label} has no CTs {link=}")
            continue
        if ct_names:
            ct_name_list = ct_names.split(',')
            ct_ids = bp.get_ct_ids(ct_name_list)
            if len(ct_ids) != len(ct_name_list):
                logging.error(f"Skipping: Generic system {generic_system_label} has wrong data {ct_name_list=} {ct_ids=}")
                continue
        # else:
        #     # can have untagged too
        #     # TODO: check if the CTs exist and create if not
        #     # TODO: naming rule
        #     if link['tagged_vlans']:
        #         for tagged_vlan_id in link['tagged_vlans']:
        #             ct_ids.append(bp.get_single_vlan_ct_or_create(tagged_vlan_id, is_tagged=True))
        #         # logging.debug(f"{untagged_vlan=}, {ct_ids=}")
        #     if untagged_vlan:
        #         # conentional name: vn123-untagged
        #         # untagged_vlan_name = f"vn{untagged_vlan_id}-untagged"
        #         # ct_ids = bp.get_ct_ids([untagged_vlan_name])
        #         # if len(ct_ids) != 1:
        #         #     added = bp.add_single_vlan_ct(200000 + untagged_vlan_id, untagged_vlan_id, is_tagged=False)
        #         #     logging.debug(f"Added CT {untagged_vlan_name}: {added}")
        #         # ct_ids = bp.get_ct_ids([untagged_vlan_name])
        #         # logging.debug(f"{untagged_vlan_name=}, {ct_ids=}")
        #         ct_ids.append(bp.get_single_vlan_ct_or_create(untagged_vlan, is_tagged=False))
        #         logging.debug(f"{untagged_vlan=}, {ct_ids=}")
        if 'ct_ids' not in locals():
            logging.debug(f"Skipping: Generic system {generic_system_label} has no CTs")
            continue
        logging.debug(f"{link=} {ct_ids=}")
        # intf_nodes = bp.get_switch_interface_nodes([link['label1']], link['ifname1'])
        intf_nodes_result = bp.get_switch_interface_nodes([link['switch1']], link['switch_intf1'])
        if isinstance(intf_nodes_result, Err):
            return Err(f"assign_connectivity_templates Err: {link['switch1']}:{link['switch_intf1']} not found in blueprint {bp.label}")
        intf_nodes = intf_nodes_result.ok_value
        if len(intf_nodes) == 0:
            logging.warning(f"{len(intf_nodes)=}, {intf_nodes=}")
            # logging.warning(f"Skipping: Generic system {generic_system_label} has invalid interface {link['label1']}:{link['ifname1']}")
            logging.warning(f"Skipping: Generic system {generic_system_label} has invalid interface {link['switch1']}:{link['switch_intf1']}")
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



def add_single_generic_system(bp, gs_label, gs_links_list) -> Result[str, str]:
    # gs_count += 1
    gs_link_total = len(gs_links_list)
    # logging.info(f"add_generic_system Adding generic system {gs_count}/{gs_total}: {gs_label} with {gs_link_total} links")
    existing_gs_result = bp.get_system_node_from_label(gs_label)
    if isinstance(existing_gs_result, Ok) and existing_gs_result.ok_value:
        error_message = f"add_single_generic_system Skipping: Generic system {gs_label} already exists in blueprint {bp.label}"
        # TODO: verify the content
        return Err(error_message)
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
        # make sure upper case
        link_speed = link['speed'].upper()
        system_type = 'external' if link['is_external'] else 'server'
        for link_id_num in range(1, 5):
            # link_id_num = link_number + 1
            switch_label = link[f"switch{link_id_num}"]
            this_ifname = link[f"switch_intf{link_id_num}"]
            # skip if data is missing
            if not switch_label:
                continue
            if this_ifname[:2] not in ['et', 'xe', 'ge']:
                error_message = f"Error: wrong interface for {gs_label} - {switch_label}:{this_ifname}"
                # logging.warning(f"add_single_generic_system Error : {error_message}")
                return Err(error_message)
            logging.debug(f"{switch_label=}")
            switch_node_result = bp.get_system_node_from_label(switch_label)
            if isinstance(switch_node_result, Err):
                error_message = f"Error: generic system {gs_label} has absent switch {switch_label}\n\tFrom get_system_node_from_label {error}"
                # logging.warning(f"add_single_generic_system {error_message}")
                return Err(error_message)
            switch_node = switch_node_result.ok_value
            if not switch_node:
                return None, f"Error: {switch_label} not found in blueprint {bp.label}"
            switch_id = switch_node['id']
            transformation_id_result = bp.get_transformation_id(switch_label, this_ifname , link_speed)
            if isinstance(transformation_id_result, Err):
                error_message = f"Error: generic system {gs_label} has absent transformation {switch_label}:{this_ifname}\n\tFrom get_transformation_id {transformation_id_result.err_value}"
                logging.warning(f"add_single_generic_system {error_message}")
                return Err(error_message)
            transformation_id = transformation_id_result.ok_value
            link_spec = {
                'switch': {
                    'system_id': switch_id,
                    # 'transformation_id': bp.get_transformation_id(link[f"switch{link_id_num}"], this_ifname , link_speed),
                    'transformation_id': transformation_id,
                    'if_name': link[f"switch_intf{link_id_num}"],
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
    logging.debug(f"add_single_generic_system {generic_system_spec=}, {speed_count=}")

    generic_system_created_result = bp.add_generic_system(generic_system_spec)
    if isinstance(generic_system_created_result, Err):
        error_message = f"Error: generic system {gs_label} not created\n\tFrom add_generic_system {generic_system_created_result.err_value}"
        # logging.warning(error_message)
        return Err(error_message)

    return Ok('done')
                                                                             

def add_generic_system(apstra_session, generic_systems: dict) -> Result[str, str]:
    """
    Add a single generic system to the Apstra server from the given generic systems data.
    Revised from add_generic_systems.

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
                    "ct_names": null,
 
                    "switch1": "server-leaf-1",
                    "switch_intf1": "xe-0/0/0",
                    "server_intf1": eth0,

                    "switch2": null,
                    "switch_intf2": null,
                    "server_intf2": null,

                    "switch3": null,
                    "switch_intf3": null,
                    "server_intf3": null,

                    "switch4": null,
                    "switch_intf4": null,
                    "server_intf4": null,

                    "comment": null
                }
            ]
        }
    }
    """
    func_name = "add_generic_system"

    ## create the generic systems
    bp_total = len(generic_systems)  # total number of blueprints
    bp_count = 0
    logging.info(f"{func_name} Adding generic systems to {bp_total} blueprints")
    for bp_label, bp_data in generic_systems.items():
        bp_count += 1
        logging.info(f"{func_name} Adding generic systems to blueprint {bp_count}/{bp_total}: {bp_label}")
        bp = CkApstraBlueprint(apstra_session, bp_label)
        # logging.debug(f"{bp=}, {bp.id=}")
        gs_total = len(bp_data)
        gs_count = 0
        logging.info(f"{func_name} Adding {gs_total} generic systems to blueprint {bp_label}")
        for gs_label, gs_links_list in bp_data.items():
            gs_count += 1
            gs_link_total = len(gs_links_list)
            logging.info(f"{func_name} Adding generic system {gs_count}/{gs_total}: {gs_label} with {gs_link_total} links")
            add_single_gs_result = add_single_generic_system(bp, gs_label, gs_links_list)
            if isinstance(add_single_gs_result, Err):
                logging.warning(f"{func_name} Error for {gs_label=}:\n\tFrom add_single_generic_system: {add_single_gs_result.err_value}")
                # return None, f"{func_name} {error}"

        ## form LACP in the BP iterating over the generic systems
        for gs_label, gs_links_list in bp_data.items():
            form_lacp(bp, gs_label, gs_links_list)
            add_tags_result = add_tags(bp, gs_label, gs_links_list)
            if isinstance(add_tags_result, Err):
                logging.warning(f"{func_name} Error for {gs_label=}:\n\tFrom add_tags: {add_tags_result.err_value}")
                # return None, f"add_generic_system {error}"
                continue
            rename_generic_system_intf(bp, gs_label, gs_links_list)

            # # update connectivity templates - this should be run after lag update
            # assign_connectivity_templates(job_env, gs_label, gs_links_list)
            assign_connectivity_templates(bp, gs_label, gs_links_list)

    return Ok(f"{func_name}: {bp_total} blueprints, {gs_total} generic systems added")



if __name__ == "__main__":
    # click_add_generic_systems()
    apstra_server_host = '10.85.192.45'
    apstra_server_port = '443'
    apstra_server_username = 'admin'
    apstra_server_password = 'admin'

    apstra = CkApstraSession(apstra_server_host, apstra_server_port, apstra_server_username, apstra_server_password)
    apstra.print_token()
    
    generic_systems = {
        'terra': {
            'single-home-1': [
                {
                    "blueprint": "terra",
                    "system_label": "single-home-1",
                    "is_external": False,
                    "speed": "10G",
                    "lag_mode": None,
                    "ct_names": "vn20",
                    "gs_tags": "single",
                    "server_intf1": "eth0",
                    "switch1": "server_1",
                    "switch_intf1": "xe-0/0/11",
                    "server_intf2": None,
                    "switch2": None,
                    "switch_intf2": None,
                    "server_intf3": None,
                    "switch3": None,
                    "switch_intf3": None,
                    "server_intf4": None,
                    "switch4": None,
                    "switch_intf4": None,
                    "comment": None
                }
            ],
            'dual-home-1': [
                {
                    "blueprint": "terra",
                    "system_label": "dual-home-1",
                    "is_external": False,
                    "speed": "10G",
                    "lag_mode": "lacp_active",
                    "ct_names": "vn20,vn101",
                    "gs_tags": "dual",
                    "server_intf1": "eth0",
                    "switch1": "server_1",
                    "switch_intf1": "xe-0/0/12",
                    "server_intf2": "eth1",
                    "switch2": "server_2",
                    "switch_intf2": "xe-0/0/12",
                    "server_intf3": None,
                    "switch3": None,
                    "switch_intf3": None,
                    "server_intf4": None,
                    "switch4": None,
                    "switch_intf4": None,
                    "comment": None
                }
            ]
        }
    }
    add_gs_result = add_generic_system(apstra, generic_systems)
    logging.info(f"{add_gs_result=}")
    if isinstance(add_gs_result, Ok):
        logging.warning(add_gs_result.ok_value)
    else:
        logging.warning(add_gs_result.err_value)

