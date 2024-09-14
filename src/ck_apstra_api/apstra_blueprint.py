#!/usr/bin/env python3

import logging
from typing import Any, Dict, Generator, List, Optional
import uuid
from enum import StrEnum
from functools import cache

from result import Err, Result, Ok

from . import CkApstraSession
from .util import deep_copy


class CkEnum(StrEnum):
    MEMBER_SWITCH = 'member_switch'
    MEMBER_INTERFACE = 'member_interface'
    EVPN_INTERFACE = 'evpn_interface'
    LINK = 'link'
    TAG = 'tag'
    GENERIC_SYSTEM = 'generic_system'
    GENERIC_SYSTEM_INTERFACE = 'gs_intf'
    TAGGED_VLANS = 'tagged_vlans'
    UNTAGGED_VLAN = 'untagged_vlan'
    REDUNDANCY_GROUP = 'redundancy_group'
    AE_INTERFACE = 'ae'


class IpLinkEnum(StrEnum):
    '''
    Enum for the IP link
    '''
    HEADER_LINE = 'line'
    HEADER_BLUEPRINT = 'blueprint'
    HEADER_SWITCH = 'switch'
    HEADER_INTERFACE = 'interface'
    HEADER_SERVER = 'server'
    HEADER_IPV4_SWITCH = 'ipv4_switch'
    HEADER_IPV4_SERVER = 'ipv4_server'

class CkApstraBlueprint:
    # __slots__ = ['session', 'label', 'design', 'id', 'logger', 'url_prefix']

    def __init__(self,
                 session: CkApstraSession,
                 label: str,
                 id: str = None) -> None:
        """
        Initialize a CkApstraBlueprint object.

        Args:
            session: The Apstra session object.
            label: The label of the blueprint.
            id: The ID of the blueprint in case it is known
        """
        self.session = session
        self.label = label
        self.id = id
        self.log_prefix = f"CkApstraBlueprint({label})"
        self.logger = logging.getLogger(self.log_prefix)
        if id:
            this_blueprint = self.session.get_items(f"blueprints/{id}")
            self.label = this_blueprint['label']
            self.design = this_blueprint['design']
            self.url_prefix = f"{self.session.url_prefix}/blueprints/{self.id}"
        else:
            self.get_id()
            if self.id:
                self.url_prefix = f"{self.session.url_prefix}/blueprints/{self.id}"


    def get_id(self) -> str:
        """
        Get the ID of the blueprint or None

        Returns:
            The ID of the blueprint. None if the blueprint does not exist.
        """
        if self.id:
            return self.id
        # get summary lists of all the blueprints
        bp = [x for x in self.session.get_items('blueprints')['items'] if x['label'] == self.label]
        if bp:
            self.id = bp[0]['id']
            self.design = bp[0]['design']
        return self.id
        

    def dump(self) -> dict:
        """
        Dump the blueprint.
          {
            'relationships': {},
            'nodes': {},
            'last_modified_at': '2023-10-30T22:25:08.490380Z',            
            'label': 'test',
            'version': 6095,
            'design': 'two_stage_l3clos',
            'id': "43964eca-9b21-4144-8c44-9f173c224623",
            'source_versions': { "config_blueprint": 6051 }
          }
        """
        return self.session.get_items(f"blueprints/{self.id}")

    def query(self, query_string: str) -> Result[List, str]:
        """
        Query the Apstra API.

        Args:
            query: The query string.
            strip: Strip the query string. Required in case of multi-line query.

        Returns:
            The Tuple of the results of the query and the error message

        """
        query_candidate = query_string.strip().replace("\n", '')        
        url = f"{self.url_prefix}/qe"
        payload = {
            "query": query_candidate
        }
        response = self.session.session.post(url, json=payload)
        if response.status_code != 200:
            return Err(f"status_code is not 200 {response.status_code=} != 200: {payload=}, {response.text=}")
        # the content should have 'items'. otherwise, the query would be invalid
        elif 'items' not in response.json():
            return Err(f"items does not exist: {query_string=}, {response.text=}")
        return Ok(response.json()['items'])
    
    # TODO: integrate with other functions
    def get_managed_system_nodes(self):
        SYSTEM_NODE_NAME='system'
        system_query = f"node('system', system_type='switch', management_level='full_control', name='{SYSTEM_NODE_NAME}')"
        resp, error = self.query(system_query)
        self.managed_system_nodes = [x[SYSTEM_NODE_NAME] for x in resp]
        return self.managed_system_nodes

    
    # return the first entry for the system
    # @cache
    def get_system_with_im(self, system_label) -> Result[dict,str]:
        system_im_result = self.query(f"node('system', label='{system_label}', name='system').out().node('interface_map', name='im')")
        # if system_label not in self.system_label_2_id_cache:
        #     # self.system_label_2_id_cache[system_label] = { 'id': system_im['system']['id'] }
        #     # self.system_id_2_label_cache[system_im['system']['id']] = system_label
        #     if  'interface_map_id' not in self.system_label_2_id_cache[system_label]:
        #         self.system_label_2_id_cache[system_label]['interface_map_id'] = system_im['im']['id']
        #         self.system_label_2_id_cache[system_label]['device_profile_id'] = system_im['im']['device_profile_id']
        if isinstance(system_im_result, Err):
            error_message = f"Error: {system_label=}\n\tquery() {system_im_result.err_value=}"
            return Err(error_message)
        return Ok(system_im_result.ok_value[0])

    # can be checked before the system creation - should not be cached in such case
    # @cache
    def get_system_node_from_label(self, system_label) -> Result[dict, str]:
        """
        Return the system dict from the system label
        called from move_access_switch
        """
        query = f"node('system', label='{system_label}', name='system')"
        system_query_result = self.query(query)
        if isinstance(system_query_result, Err):
            return Err(f"{system_label} not found for {query}: from query: {query}")
        # self.logger.warning(f"{system_label=} {system_query_result=}")
        if len(system_query_result.ok_value) == 0:
            return Ok({})
        return Ok(system_query_result.ok_value[0]['system'])


    def get_system_label(self, system_id):
        '''
        Get the system label from the system id
        '''
        if system_id not in self.system_id_2_label_cache:
            return None
        return self.system_id_2_label_cache[system_id]

    def get_server_interface_nodes(self, generic_system_label: str = None, intf_name: str = None) -> Result[str, str]:
        """
        Return interface nodes of a system label
            return CkEnum.MEMBER_INTERFACE and CkEnum.MEMBER_SWITCH
                optionally CkEnum.EVPN_INTERFACE if it is a LAG
            It can be used for VLAN CT association
            TODO: implement intf_name in case of multiple link generic system
        TODO: cache generic system interface id
        called by move_access_switch
        """
        gs_label_filter = f"label='{generic_system_label}', " if generic_system_label else ''
        interface_query = f"""match(
            node('system', system_type='server', {gs_label_filter} name='{CkEnum.GENERIC_SYSTEM}')
                .out('hosted_interfaces').node('interface', name='{CkEnum.GENERIC_SYSTEM_INTERFACE}')
                .out('link').node('link', name='{CkEnum.LINK}')
                .in_('link').node('interface', if_type='ethernet', name='{CkEnum.MEMBER_INTERFACE}')
                .in_('hosted_interfaces').node('system', system_type='switch', name='{CkEnum.MEMBER_SWITCH}'),
            optional(
                node(name='{CkEnum.REDUNDANCY_GROUP}')
                    .out('hosted_interfaces').node('interface', po_control_protocol='evpn', name='{CkEnum.EVPN_INTERFACE}')
                    .out('composed_of').node('interface')
                    .out('composed_of').node(name='{CkEnum.MEMBER_INTERFACE}')
            ),
            optional(
                node(name='{CkEnum.MEMBER_INTERFACE}')
                    .in_('composed_of').node('interface', name='{CkEnum.AE_INTERFACE}')
            ),
            optional(
                node('tag', name='{CkEnum.TAG}').out().node(name='{CkEnum.LINK}')
            )
        )"""
        # self.logger.warning(f"get_server_interface_nodes() {generic_system_label=} {interface_query=}")
        # query_result = self.query(interface_query)
        return self.query(interface_query)

    def get_switch_interface_nodes(self, switch_labels=None, intf_name=None) -> Result[List, str]:
        """
        Return interface nodes of the switches. The once not conencted to generic system may not appear.
            switch_labels: list of system labels, a str for the single system label, or None for all switches
            return CkEnum.MEMBER_INTERFACE and CkEnum.MEMBER_SWITCH
                optionally CkEnum.EVPN_INTERFACE if it is a LAG
            It can be used for VLAN CT association
            TODO: implement intf_name in case of multiple link generic system
        TODO: cache generic system interface id
        """
        if switch_labels is None:
            label_selection = ''
        elif isinstance(switch_labels, list):
            label_selection = f" label=is_in({switch_labels}),"
        elif isinstance(switch_labels, str):
            label_selection = f" label='{switch_labels}',"
        else:
            self.logger.warning(f"{switch_labels=} is not a list or string")
            return Ok([])
        intf_name_filter = f", if_name='{intf_name}'" if intf_name else ""
        interface_query = f"""match(
            node('system', system_type='switch',{label_selection} name='{CkEnum.MEMBER_SWITCH}')
                .out('hosted_interfaces').node('interface', if_type='ethernet', name='{CkEnum.MEMBER_INTERFACE}'{intf_name_filter}),
            optional(
                node(name='{CkEnum.MEMBER_INTERFACE}')
                    .out('link').node('link', name='{CkEnum.LINK}')
                    .in_('link').node('interface', name='{CkEnum.GENERIC_SYSTEM_INTERFACE}')
                    .in_('hosted_interfaces').node('system', system_type='server', name='{CkEnum.GENERIC_SYSTEM}')
            ),
            optional(
                node(name='{CkEnum.REDUNDANCY_GROUP}')
                    .out('hosted_interfaces').node('interface', po_control_protocol='evpn', name='{CkEnum.EVPN_INTERFACE}')
                    .out('composed_of').node('interface')
                    .out('composed_of').node(name='{CkEnum.MEMBER_INTERFACE}')
            ),
            optional(
                node(name='{CkEnum.MEMBER_INTERFACE}')
                    .in_('composed_of').node('interface', name='{CkEnum.AE_INTERFACE}')
            ),
            optional(
                node('tag', name='{CkEnum.TAG}').out().node(name='{CkEnum.LINK}')
            )
        )"""

        interface_nodes_result = self.query(interface_query)
        return interface_nodes_result

    def get_single_vlan_ct_id(self, vn_id: int):
        '''
        Get the single VLAN CT ID

        Return tuple of (tagged CT id, untagged CT id)
        '''
        ct_list_spec = f"""
            node('virtual_network', vn_id='{vn_id}', name='virtual_network')
                .in_().node('ep_endpoint_policy', name='ep_endpoint_policy')
                .in_('ep_first_subpolicy').node()
                .in_('ep_subpolicy').node('ep_endpoint_policy', name='ct')
        """
        ct_list, error = self.query(ct_list_spec)
        tagged_nodes = [x for x in ct_list if 'vlan_tagged' in x['ep_endpoint_policy']['attributes']]
        tagged_ct = len(tagged_nodes) and tagged_nodes[0]['ct']['id'] or None
        # tagged_ct = [x['id'] for x in ct_list if x and 'vlan_tagged' in x['ep_endpoint_policy']['attributes']][0] or None
        untagged_nodes = [x for x in ct_list if 'untagged' in x['ep_endpoint_policy']['attributes']]
        untagged_ct = len(untagged_nodes) and untagged_nodes[0]['ct']['id'] or None
        # untagged_ct = [x['id'] for x in ct_list if x and 'untagged' in x['ep_endpoint_policy']['attributes']][0] or None
        return (tagged_ct, untagged_ct)
    

    @cache
    def get_ct_ids(self, ct_labels: list) -> list:
        '''
        Return the CT IDs from the connectivity template names(labels)
        '''
        if isinstance(ct_labels, str):
            ct_labels = [ct_labels]
        ct_list_query = f"""
            node('ep_endpoint_policy', policy_type_name='batch', label=is_in({ct_labels}), name='ep')
        """
        ct_list_result = self.query(ct_list_query)
        if isinstance(ct_list_result, Err):
            return Err(f"Error: {ct_list_result.err_value=}")
        ct_list = ct_list_result.ok_value
        if len(ct_list) == 0:
            self.logger.debug(f"No CTs found for {ct_labels=}")
            return []
        return [x['ep']['id'] for x in ct_list]
    
    
    def add_generic_system(self, generic_system_spec: dict) -> Result[List, str]:
        """
        Add a generic system (and access switch pair) to the blueprint.

        Args:
            generic_system_spec: The specification of the generic system.

        Returns:
            The ID of the switch-system-link ids.
        """
        new_generic_system_label = generic_system_spec['new_systems'][0]['label']
        existing_system_query = f"node('system', label='{new_generic_system_label}', name='system')"
        existing_system_result = self.query(existing_system_query)
        if len(existing_system_result.ok_value) > 0:
            # skipping if the system already exists
            # return []
            return Ok([])
        url = f"{self.url_prefix}/switch-system-links"
        created_generic_system = self.session.session.post(url, json=generic_system_spec)
        if created_generic_system.status_code >= 400:
            # self.logger.error(f"System not created: {created_generic_system=}, {new_generic_system_label=}, {created_generic_system.text=}")
            return Err(f"System not created: {created_generic_system=}, {new_generic_system_label=}, {created_generic_system.text=}")
        # which case?
        if created_generic_system is None or len(created_generic_system.json()) == 0 or 'ids' not in created_generic_system.json():
            return Err("Not created")
        return Ok(created_generic_system.json()['ids'])

    def get_transformation_id(self, system_label, intf_name, speed) -> Result[int, str]:
        '''
        Get the transformation ID for the interface

        Args:
            system_label: The label of the system
            intf_name: The name of the interface
            speed: The speed of the interface in the format of '10G'
        '''
        # the unit is in uppercase
        speed = speed.upper()
        system_im_result = self.get_system_with_im(system_label)
        if isinstance(system_im_result, Err):
            return Err(f"{system_label=} {intf_name=} {speed=}\n\tError get_system_with_im {system_im_result=}")
        system_im = system_im_result.ok_value
        device_profile_result = self.session.get_device_profile(system_im['im']['device_profile_id'])
        if isinstance(device_profile_result, Err):
            return Err(f"{system_label=} {intf_name=} {speed=}\n\tError get_device_profile {device_profile_result.err_value=}")
        device_profile = device_profile_result.ok_value
        if 'ports' not in device_profile:
            return Err(f"{system_label=} {intf_name=} {speed=}\n\tError: no ports in device profile {device_profile=}")
        for port in device_profile['ports']:
            if 'transformations' not in port:
                return Err(f"{system_label=} {intf_name=} {speed=}\n\tError: no transformations in port {port=}")    
            for transformation in port['transformations']:
                # self.logger.debug(f"{transformation=}")
                for intf in transformation['interfaces']:
                    # if intf['name'] == intf_name:
                    #     self.logger.debug(f"{intf=}")
                    if intf['name'] == intf_name and intf['speed']['unit'] == speed[-1:] and intf['speed']['value'] == int(speed[:-1]): 
                        # self.logger.warning(f"{intf_name=}, {intf=}")
                        return Ok(transformation['transformation_id'])
        return Err(f"transformation not found for {system_label=} {intf_name=} {speed=}")

    def patch_leaf_server_link(self, link_spec: dict) -> None:
        """
        Patch a leaf-server link.

        Args:
            link_spec: The specification of the leaf-server link.
        """
        url = f"{self.url_prefix}/leaf-server-link-labels"
        self.session.patch_throttled(url, spec=link_spec)

    def patch_obj_policy_batch_apply(self, policy_spec, params=None):
        '''
        Apply policies in a batch
        '''
        return self.session.patch_throttled(f"{self.url_prefix}/obj-policy-batch-apply", spec=policy_spec, params=params)

    def patch_leaf_server_link_labels(self, spec, params=None, print_prefix=None):
        '''
        Update the generic system links
        '''
        if print_prefix:
            self.logger.info(f"{print_prefix}: {spec=}")
        return self.session.patch_throttled(f"{self.url_prefix}/leaf-server-link-labels", spec=spec, params=params)

    def patch_node_single(self, node, patch_spec, params=None):
        '''
        Patch node data
        '''
        return self.session.session.patch(f"{self.url_prefix}/nodes/{node}", json=patch_spec, params=params)

    def patch_item(self, item: str, patch_spec, params=None):
        '''
        Patch an item (generic)
        '''
        return self.session.session.patch(f"{self.url_prefix}/{item}", json=patch_spec, params=params)

    def delete_item(self, item: str, params=None):
        '''
        Patch an item (generic)
        '''
        return self.session.session.delete(f"{self.url_prefix}/{item}", params=params)


    def patch_nodes(self, patch_spec, params=None):
        '''
        Patch node data with patch_spec list
        '''
        params_to_use = params or {'async': 'full'}
        return self.session.session.patch(f"{self.url_prefix}/nodes", json=patch_spec, params=params_to_use)


    def get_virtual_network(self, vni):
        '''
        Get virtual network data from vni or None
        '''
        vn_id_got, error = self.query(f"node('virtual_network', vn_id='{vni}', name='vn')")
        if len(vn_id_got) == 0:
            self.logger.warning(f"{vni=} not found")
            return None
        vn_id = vn_id_got[0]['vn']['id']
        return self.session.get_items(f"blueprints/{self.id}/virtual-networks/{vn_id}")
    
    def patch_virtual_network(self, patch_spec, params=None, svi_requirement=False):
        '''
        Patch virtual network data
        '''
        if params is None:
            params = {
                'comment': 'virtual-network-details',
                'async': 'full',
                'type': 'staging',
                'svi_requirements': 'true'
            }
        patched = self.session.patch_throttled(f"{self.url_prefix}/virtual-networks/{patch_spec['id']}", spec=patch_spec, params=params)
        return patched

    def post_tagging(self, nodes: list, tags_to_add = None, tags_to_remove = None, params=None):
        '''
        Update the tagging
        Args:
            nodes: The list of nodes to be tagged. Can be links. A node (string) can be used.
            tags_to_add: The list of tags to be added
            tags_to_remove: The list of tags to be removed

        tagging_sepc example
            "add": [ "testtest"],
            "tags": [],
            "nodes": [ "atl1tor-r5r14a<->_atl_rack_1_001_sys010(link-000000002)[1]" ],
            "remove": [],
            "assigned_to_all": []        
        '''
        tagging_spec = {
            'add': [],
            # 'tags': [],
            'nodes': [],
            'remove': [],
            'assigned_to_all': [],
        }
        # take string or list 
        the_nodes_list = nodes if isinstance(nodes, list) else [nodes] if isinstance(nodes, str) else []
        if len(the_nodes_list) == 0:
            self.logger.warning(f"{nodes=} is not a list or string")
            return
        # in case of single tags_to_add
        if isinstance(tags_to_add, str):
            tags_to_add = [tags_to_add]
        # no need to check the present of tags in tags_to_add 
        tag_nodes_result = self.query(f"node(id=is_in({the_nodes_list})).in_().node('tag', label=is_in({tags_to_add}), name='tag')")
        are_tags_the_same = len(tag_nodes_result.ok_value) == (len(tags_to_add) * len(nodes))
        self.logger.debug(f"{nodes=} {the_nodes_list=} {tags_to_add=}, {tags_to_remove=}, {are_tags_the_same=} {tag_nodes_result.ok_value}")

        # self.logger.debug(f"{nodes=} {tags_to_add=}, {tags_to_remove=} {are_tags_the_same=}")
        # The tags are the same as the existing tags
        # if are_tags_the_same or (not tags_to_add and not tags_to_remove):
        #     return
        tagging_spec['nodes'] = the_nodes_list
        tagging_spec['add'] = tags_to_add
        tagging_spec['remove'] = tags_to_remove
        return self.session.session.post(f"{self.url_prefix}/tagging", json=tagging_spec, params={'aync': 'full'})

    def post_item(self, item_url: str, post_spec: dict, params={'type': 'staging'}):
        '''
        Post an item
        '''
        return self.session.session.post(f"{self.url_prefix}/{item_url}", json=post_spec, params=params)

    def put_item(self, item_url: str, put_spec: dict, params={'type': 'staging'}):
        '''
        Put an item
        '''
        return self.session.session.put(f"{self.url_prefix}/{item_url}", json=put_spec, params=params)

    def batch(self, batch_spec: dict, params=None) -> dict:
        '''
        Run API commands in batch
        '''
        url = f"{self.url_prefix}/batch"
        result = self.session.session.post(url, json=batch_spec, params=params)
        return result

    # def get_cts_on_generic_system_with_only_ae(self, generic_system_label) -> list:
    #     '''
    #     Get the CTS of generic system with single AE
    #     '''
    #     ct_list_spec = f"""
    #         match(
    #             node('system', label='{generic_system_label}', system_type='server')
    #                 .out().node('interface', if_type='port_channel', name='gs_ae')
    #                 .out().node('link')
    #                 .in_().node(name='switch_ae')
    #                 .out().node('ep_group')
    #                 .in_().node('ep_application_instance')
    #                 .out().node('ep_endpoint_policy', policy_type_name='batch', name='batch')
    #             .where(lambda switch_ae, gs_ae: switch_ae != gs_ae )
    #         ).distinct(['batch'])
    #     """
    #     ct_list = [ x['batch']['id'] for x in self.query(ct_list_spec, multiline=True) ]
    #     return ct_list

    def get_interface_cts(self, interface_id) -> list:
        '''
        Get the CTS of the interface
        '''
        ct_list_spec = f"""
            match(
                node(id='{interface_id}', name='switch_ae')
                    .out().node('ep_group')
                    .in_().node('ep_application_instance')
                    .out().node('ep_endpoint_policy', policy_type_name='batch', name='batch')
            ).distinct(['batch'])
        """
        ct_list = [x['batch']['id']
                   for x, error in self.query(ct_list_spec)]
        return ct_list

    def get_single_vlan_ct_or_create(self, vlan_id: int, is_tagged: bool) -> str:
        """
        Get the single VLAN CT ID or create one if it does not exist
        """
        vlan_name = f"vn{vlan_id}"
        if is_tagged is False:
            vlan_name = f"{vlan_name}-untagged"
        ct_ids = self.get_ct_ids([vlan_name])
        if len(ct_ids) == 1:
            return ct_ids[0]
        new_ct_id = self.add_single_vlan_ct(200000 + vlan_id, vlan_id, is_tagged)
        return new_ct_id

    def add_single_vlan_ct(self, vni: int, vlan_id: int, is_tagged: bool) -> str:
        '''
        Create a single VLAN CT
        '''
        logging.debug(f"{vni=}, {vlan_id=}, {is_tagged=}")
        tagged_type = 'vlan_tagged' if is_tagged else 'untagged'
        ct_label = f"vn{vlan_id}" if is_tagged else f"vn{vlan_id}-untagged"
        uuid_batch = str(uuid.uuid4())
        uuid_pipeline = str(uuid.uuid4())
        uuid_vlan = str(uuid.uuid4())
        found_vn_node, error = self.query(f"node('virtual_network', vn_id='{vni}', name='vn')")
        if len(found_vn_node) == 0:
            self.logger.warning(f"virtual network with {vni=} not found")
            return None
        vn_id = found_vn_node[0]['vn']['id']
        policy_spec = {
            "policies": [
                {
                    "description": f"Single VLAN Connectivity Template for VNI {vni}",
                    "tags": [],
                    "user_data": f"{{\"isSausage\":true,\"positions\":{{\"{uuid_vlan}\":[290,80,1]}}}}",
                    "label": ct_label,
                    "visible": True,
                    "policy_type_name": "batch",
                    "attributes": {
                        "subpolicies": [uuid_pipeline]
                    },
                    "id": uuid_batch
                },
                {
                    "description": "Add a single VLAN to interfaces",
                    "label": "Virtual Network (Single)",
                    "visible": False,
                    "attributes": {
                        "vn_node_id": vn_id,
                        "tag_type": tagged_type
                    },
                    "policy_type_name": "AttachSingleVLAN",
                    "id": uuid_vlan
                },
                {
                    "description": "Add a single VLAN to interfaces",
                    "label": "Virtual Network (Single) (pipeline)",
                    "visible": False,
                    "attributes": {
                        "second_subpolicy": None,
                        "first_subpolicy": uuid_vlan
                    },
                    "policy_type_name": "pipeline",
                    "id": uuid_pipeline
                }
            ]
        }
        url = f"{self.url_prefix}/obj-policy-import"
        result = self.session.session.put(url, json=policy_spec)
        # it will be 204 with b''
        return uuid_batch

    def add_multiple_vlan_ct(self, ct_label: str, untagged_vlan_id: int = None, tagged_vlan_ids: list[int] = []) -> str:
        '''
        Create a multi VLAN CT
        TODO: under construction
        '''
        logging.warning(f"{ct_label=}, {untagged_vlan_id=}, {tagged_vlan_ids=}")
        untagged_vn_id = self.get_virtual_network(200000 + untagged_vlan_id) if untagged_vlan_id else None
        tagged_vn_ids = [self.get_virtual_network(200000 + x) for x in tagged_vlan_ids]
        uuid_batch = str(uuid.uuid4())
        uuid_pipeline = str(uuid.uuid4())
        uuid_vlan = str(uuid.uuid4())
        # found_vn_node = self.query(f"node('virtual_network', vn_id='{vni}', name='vn')")
        if untagged_vn_id is None and len(tagged_vn_ids) == 0:
            self.logger.warning(f"virtual network with {untagged_vlan_id=} and/or {tagged_vlan_ids=} not found")
            return None
        policy_spec = {
            "policies": [
                {
                    "description": f"Multiple VLAN Connectivity Template",
                    "tags": [],
                    "user_data": f"{{\"isSausage\":true,\"positions\":{{\"{uuid_vlan}\":[290,80,1]}}}}",
                    "label": ct_label,
                    "visible": True,
                    "policy_type_name": "batch",
                    "attributes": {
                        "subpolicies": [uuid_pipeline]
                    },
                    "id": uuid_batch
                },
                {
                    "description": "Add a list of VLANs to interfaces, as tagged or untagged.",
                    "label": "Virtual Network (Multiple)",
                    "visible": False,
                    "attributes": {
                        "untagged_vn_node_id": untagged_vn_id,
                        "tagged_vn_node_ids": tagged_vn_ids,
                    },
                    "policy_type_name": "AttachMultipleVLAN",
                    "id": uuid_vlan
                },
                {
                    "description": "Add a list of VLANs to interfaces, as tagged or untagged.",
                    "label": "Virtual Network (Multiple) (pipeline)",
                    "visible": False,
                    "attributes": {
                        "second_subpolicy": None,
                        "first_subpolicy": uuid_vlan
                    },
                    "policy_type_name": "pipeline",
                    "id": uuid_pipeline
                }
            ]
        }
        url = f"{self.url_prefix}/obj-policy-import"
        result = self.session.session.put(url, json=policy_spec)

        # it will be 204 with b''
        return uuid_batch

    def get_cabling_maps(self):
        '''
        Get the cabling maps
        '''
        url = f"{self.url_prefix}/cabling-maps"
        return self.session.session.get(url).json()

    def patch_cable_map(self, cable_map_spec) -> Result[None, str]:
        '''
        Set the cabling map
        '''
        url = f"{self.url_prefix}/cabling-map"
        patched = self.session.session.patch(url, json=cable_map_spec, params={'comment': 'cabling-map-update'})
        if patched.status_code == 204:
            # No Content: a request has succeeded, but that the client doesn't need to navigate away from its current page.
            return Ok(None)
        return Err(patched.text)

    def patch_security_zones_csv_bulk(self, csv_bulk: str, params: dict = {'async': 'full'}):
        '''
        Patch the security zones in bulk
        '''
        url = f"{self.url_prefix}/security-zones-csv-bulk"
        csv_spec = {
            'csv_bulk': csv_bulk,
        }        
        patched = self.session.session.patch(url, json=csv_spec, params=params)
        return patched

    def patch_virtual_networks_csv_bulk(self, csv_bulk: str, params: dict = {'async': 'full'}):
        '''
        Patch the virtual networks in bulk
        '''
        url = f"{self.url_prefix}/virtual-networks-csv-bulk"
        csv_spec = {
            'csv_bulk': csv_bulk,
        }        
        patched = self.session.session.patch(url, json=csv_spec, params=params)
        return patched
    
    def patch_resource_groups(self, resource_group_spec: dict, params: dict = {'async': 'full'}):
        '''
        Patch the resource groups
        '''
        url = f"{self.url_prefix}/resource_groups"
        patched = self.session.session.patch(url, json=resource_group_spec, params=params)
        return patched

    def revert(self):
        '''
        Revert the blueprint
        '''
        url = f"{self.url_prefix}/revert"
        revert_result = self.session.session.post(url,
                                                  json="",
                                                  params={"aync": "full"})
        self.logger.info(f"Revert result: {revert_result.json()}")


    def get_ip_pools(self):
        '''
        Get the IP pools of the controller
        '''
        ip_pools = self.session.get_items('resources/ip-pools')
        # self.logger.debug(f"{ip_pools=}")
        return ip_pools['items']

    def get_lldp_data(self):
        '''
        Get the LLDP data
        '''
        lldp_data = self.session.get_items(f"blueprints/{self.id}/cabling-map/lldp")
        return lldp_data

    def get_item(self, item: str):
        '''
        Get the items of the blueprint
        '''
        items = self.session.get_items(f"blueprints/{self.id}/{item}")
        return items


    def swap_ct_vns(self, from_vn_id, to_vn_id) -> Generator[any, None, None]:
        '''
        Swap the VLANs (VN) of the CT        
        '''
        log_prefix = f"{self.log_prefix}::swap_ct_vns({from_vn_id=}, {to_vn_id=})"
        endpoint_policies = self.get_item('endpoint-policies')['endpoint_policies']
        for ct in endpoint_policies:
            attr = ct['attributes']
            if ct['policy_type_name'] == 'AttachSingleVLAN':
                if attr['vn_node_id'] == from_vn_id:
                    modified_attributes = deep_copy(attr)
                    modified_attributes['vn_node_id'] = to_vn_id
                    patched = self.patch_item(f"endpoint-policies/{ct['id']}", {'attributes': modified_attributes})
                    yield f"{log_prefix} patched: {ct['id']=} {attr=} {patched=}"

                # logger.info(f"CT - not to process: {ct['id']=} {ct['policy_type_name']} {attr=}")
            elif ct['policy_type_name'] == 'AttachMultipleVLAN':
                if from_vn_id in attr['tagged_vn_node_ids']:
                    modified_attributes = deep_copy(attr)
                    modified_attributes['tagged_vn_node_ids'] = [x for x in attr['tagged_vn_node_ids'] if x != from_vn_id]
                    modified_attributes['tagged_vn_node_ids'].append(to_vn_id)
                    patched = self.patch_item(f"endpoint-policies/{ct['id']}", {'attributes': modified_attributes})
                    yield f"{log_prefix} patched: {ct['id']=} {attr=} {patched=}"
                elif from_vn_id == attr['untagged_vn_node_id']:
                    modified_attributes = deep_copy(attr)
                    modified_attributes['untagged_vn_node_id'] = to_vn_id
                    patched = self.patch_item(f"endpoint-policies/{ct['id']}", {'attributes': modified_attributes})
                    yield f"{log_prefix} patched: {ct['id']=} {attr=} {patched=}"
                else:
                    # yield f"{log_prefix} - not to process: {ct['id']=} {ct['policy_type_name']} {attr=}")
                    pass

    def get_temp_vn(self, virtual_network: str) -> Generator[Dict[str, Any], None, None]:
        '''
        Build and return the temporary virtual network from the source virtual network
        '''
        log_prefix = f"{self.log_prefix}::get_temp_vn({virtual_network=})"

        temp_vni_id = 204094
        temp_vlan_id = 4094
        temp_vn_label = None
        temp_vlan_label_index = 4094

        found_vns_dict = self.get_item('virtual-networks')['virtual_networks']
        found_szs_dict = self.get_item('security-zones')['items']

        # pick the target VN data
        target_vn_node = [vn for vn in found_vns_dict.values() if vn['label'] == virtual_network]    
        if len(target_vn_node) == 0:
            yield f"{log_prefix} - Virtual Network not found"
            return

        # select the temporary VNI ID
        vnis = [int(vn['vn_id']) for vn in found_vns_dict.values()]
        vni_in_szs = [sz['vni_id'] for sz in found_szs_dict.values()]
        vnis = sum([vnis, vni_in_szs], [])
        # yield f"{log_prefix} - {vnis=} {temp_vni_id=}"
        while True:
            # yield f"{log_prefix} - {temp_vni_id not in vnis=}"
            if temp_vni_id not in vnis:
                break
            temp_vni_id -= 1 
        else:
            yield f"{log_prefix} - Failed to select Temporary VNI ID"
            return
        
        # select the temporary VLAN ID
        vlans = []
        for vn in found_vns_dict.values():
            if vn.get('reserved_vlan_id', None):
                vlans.append(vn['reserved_vlan_id'])
                continue
            # 'reserved_vlan_id' is not set. append the vlan_id within bound_to
            for bound_to in vn['bound_to']:
                if (vlan_id := bound_to['vlan_id']):
                    if vlan_id not in vlans:
                        vlans.append(bound_to['vlan_id'])
        vlan_in_szs = [sz['vlan_id'] for sz in found_szs_dict.values() if sz['vlan_id']]
        vlans = sum([vlans, vlan_in_szs], [])
        while True:
            if temp_vlan_id not in vlans:
                break
            temp_vlan_id -= 1
        else:
            yield f"{log_prefix} - Failed to select Temporary VLAN ID"
            return

        # select the temporary VLAN Label
        vlan_names = [vn['label'] for vn in found_vns_dict.values()]
        while True:
            name = f"temp-vn-{temp_vlan_label_index}"
            if name not in vlan_names:
                temp_vn_label = name
                break
            temp_vlan_label_index -= 1
        else:
            yield f"{log_prefix} - Failed to select Temporary VLAN ID"
            return
        
        temp_vn_spec = deep_copy(target_vn_node[0])
        temp_vn_spec['label'] = temp_vn_label
        temp_vn_spec['vn_id'] = str(temp_vni_id)
        temp_vn_spec['ipv4_subnet'] = None
        temp_vn_spec['virtual_gateway_ipv4'] = None
        temp_vn_spec['virtual_gateway_ipv4_enabled'] = None
        temp_vn_spec['ipv4_enabled'] = None
        if 'reserved_vlan_id' in temp_vn_spec:
            temp_vn_spec['reserved_vlan_id'] = temp_vlan_id
        # change the bound_to VLAN to TEMP_VN_VLAN
        for bound_to in temp_vn_spec['bound_to']:
            bound_to['vlan_id'] = temp_vlan_id
        del temp_vn_spec['id']
        vn_temp_created = self.post_item('virtual-networks', temp_vn_spec)
        temp_vn_spec['id'] = vn_temp_created.json()['id']
        # yield f"{log_prefix} - {temp_vn_spec=} {vn_temp_created=} {vn_temp_created.content=} {vn_temp_created.json()=}"
        yield temp_vn_spec


    def import_iplink(self, ip_links_in: dict) -> Result[dict, str]:
        '''
        Import the IP link

        Args:
            ip_links_in: The IP link data # the data returned by export_iplink

        Returns:
            Error message or the result of the export
            Ok
        '''
        LABEL_SWITCH = 'switch'
        LABEL_IFL = 'ifl'
        LABEL_GS_IFL = 'gs_ifl'
        LABEL_SERVER = 'server'

        switch_label = ip_links_in[IpLinkEnum.HEADER_SWITCH.value]
        switch_ifl = ip_links_in[IpLinkEnum.HEADER_INTERFACE.value]
        ipv4_switch = ip_links_in[IpLinkEnum.HEADER_IPV4_SWITCH.value]
        ipv4_server = ip_links_in[IpLinkEnum.HEADER_IPV4_SERVER.value]

        iplink_query = f"""
            node('system', system_type='switch', label='{switch_label}', name='{LABEL_SWITCH}')
                .out('hosted_interfaces').node('interface')
                .out('composed_of').node('interface', if_name='{switch_ifl}', name='{LABEL_IFL}')
                .out('link').node('link')
                .in_('link').node('interface', if_type='subinterface', name='{LABEL_GS_IFL}')
                .in_('composed_of').node('interface')
                .in_('hosted_interfaces').node('system', system_type='server', name='{LABEL_SERVER}')
        """
        iplink_result = self.query(iplink_query)
        if isinstance(iplink_result, Err):
            return Err(f"Error: {iplink_result.err_value=}")
        if len(iplink_result.ok_value) == 0:
            return Err(f"Error: {iplink_result.ok_value=}")
        fetched_ipv4_switch = iplink_result.ok_value[0][LABEL_IFL]['ipv4_addr']
        fetched_ipv4_server = iplink_result.ok_value[0][LABEL_GS_IFL]['ipv4_addr']
        fetched_ifl_id = iplink_result.ok_value[0][LABEL_IFL]['id']
        fetched_gs_ifl_id = iplink_result.ok_value[0][LABEL_GS_IFL]['id']
        if fetched_ipv4_switch == ipv4_switch and fetched_ipv4_server == ipv4_server:
            return Ok(f"Skipping - no change: {ip_links_in=}")
        iplink_patch_spec = {
            'subinterfaces': {
                fetched_ifl_id: {
                    'ipv4_addr': ipv4_switch,
                    'ipv4_addr_type': 'numbered'
                },
                fetched_gs_ifl_id: {
                    'ipv4_addr': ipv4_server,
                    'ipv4_addr_type': 'numbered'
                }
            }
        }
        iplink_patch_result = self.patch_item('subinterfaces', iplink_patch_spec)
        if iplink_patch_result.status_code != 204:
            return Err(f"Error: {iplink_patch_result.text=} {ip_links_in=}")
        return Ok(f"patched successfully: {ip_links_in=}")


    def export_iplink(self) -> Result[dict, str]:
        '''
        Export the IP link

        Returns:
            Error message or the result of the export
            Ok
                List of Dict: {
                    'interface': 'ae1.1998',
                    'ipv4_addr 
                    'iplinks': [
                        {
                            'line': 0,
                            'blueprint': 'blueprint_label',
                            'switch': 'switch_label',
                            'interface': 'ifl_label'
                            'server': 'server_label'
                            'ipv4_switch': 'switch_ipv4',
                            'ipv4_server': 'server_ipv4'
                        }
                    ]
                }
        '''
        LABEL_SWITCH = 'switch'
        LABEL_IFL = 'ifl'
        LABEL_GS_IFL = 'gs_ifl'
        LABEL_SERVER = 'server'

        iplink_query = f"""
            node('system', system_type='switch', name='{LABEL_SWITCH}')
                .out('hosted_interfaces').node('interface')
                .out('composed_of').node('interface', if_type='subinterface', name='{LABEL_IFL}')
                .out('link').node('link')
                .in_('link').node('interface', if_type='subinterface', name='{LABEL_GS_IFL}')
                .in_('composed_of').node('interface')
                .in_('hosted_interfaces').node('system', system_type='server', name='{LABEL_SERVER}')
        """
        iplink_result = self.query(iplink_query)
        if isinstance(iplink_result, Err):
            return Err(f"Error: {iplink_result.err_value=}")
        iplink_list = [{
            IpLinkEnum.HEADER_LINE.value: 0,
            IpLinkEnum.HEADER_BLUEPRINT.value: self.label,
            IpLinkEnum.HEADER_SWITCH.value: x[LABEL_SWITCH]['label'],
            IpLinkEnum.HEADER_INTERFACE.value: x[LABEL_IFL]['if_name'],
            IpLinkEnum.HEADER_SERVER.value: x[LABEL_SERVER]['label'],
            IpLinkEnum.HEADER_IPV4_SWITCH.value: x[LABEL_IFL]['ipv4_addr'],
            IpLinkEnum.HEADER_IPV4_SERVER.value: x[LABEL_GS_IFL]['ipv4_addr']
            } for x in iplink_result.ok_value]
        return Ok(iplink_list)
    