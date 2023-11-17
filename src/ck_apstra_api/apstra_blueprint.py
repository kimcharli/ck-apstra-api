#!/usr/bin/env python3

import logging
import uuid

from ck_apstra_api.apstra_session import CkApstraSession
from ck_apstra_api.apstra_session import prep_logging

# def pretty_yaml(data: dict, label: str) -> None:
#     print(f"==== {label}\n{yaml.dump(data)}\n====")


class CkEnum:
    MEMBER_SWITCH = 'member-switch'
    MEMBER_INTERFACE = 'member-interface'
    EVPN_INTERFACE = 'evpn-interface'
    LINK = 'link'
    TAG = 'tag'
    GENERIC_SYSTEM = 'generic-system'
    GENERIC_SYSTEM_INTERFACE = 'gs-intf'
    TAGGED_VLANS = 'tagged-vlans'
    UNTAGGED_VLAN = 'untagged-vlan'
    REDUNDANCY_GROUP = 'redundancy-group'


class CkApstraBlueprint:

    def __init__(self,
                 session: CkApstraSession,
                 label: str,
                 id: str = None) -> None:
        """
        Initialize a CkApstraBlueprint object.

        Args:
            session: The Apstra session object.
            label: The label of the blueprint.
        """
        self.session = session
        self.label = label
        self.id = id
        if id:
            this_blueprint = self.session.get_items(f"blueprints/{id}")
            self.label = this_blueprint['label']
        else:
            self.get_id()
        self.url_prefix = f"{self.session.url_prefix}/blueprints/{self.id}"
        self.logger = logging.getLogger(f"CkApstraBlueprint({label})")

        self.system_label_2_id_cache = {}  # { system_label: { id: id, interface_map_id: id, device_profile_id: id }
        self.system_id_2_label_cache = {}  # { system_label: { id: id, interface_map_id: id, device_profile_id: id }
        self.logger.debug(f"{self.id=}")


    def get_id(self) -> str:
        """
        Get the ID of the blueprint.

        Returns:
            The ID of the blueprint.
        """
        # get summary lists of all the blueprints
        blueprints = self.session.get_items('blueprints')['items']
        self.id = [x['id'] for x in blueprints if x['label'] == self.label][0]
        # for blueprint in blueprints:
        #     if blueprint['label'] == self.label:
        #         self.id = blueprint['id']
        #         break
        if self.id is None:
            raise ValueError(f"Blueprint '{self.label}' not found.")
        return self.id

    # def get_id(self) -> None:
    #     """
    #     Print the ID of the blueprint.
    #     """
    #     return self.id

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

    def query(self, query_string: str, print_prefix: str = None, multiline: bool = False) -> list:
        """
        Query the Apstra API.

        Args:
            query: The query string.
            strip: Strip the query string. Required in case of multi-line query.

        Returns:
            The content of the items, the results of the query.
        """
        query_candidate = query_string.strip()        
        if multiline:
            query_candidate = query_candidate.replace("\n", '')
        if print_prefix:
            self.logger.info(f"{print_prefix}: {query_string}")
        url = f"{self.url_prefix}/qe"
        payload = {
            "query": query_candidate
        }
        response = self.session.session.post(url, json=payload)
        if print_prefix or response.status_code != 200:
            self.logger.warning(f"status_code {response.status_code} != 200: {payload=}, response.text={response.text}")
        # the content should have 'items'. otherwise, the query would be invalid
        elif 'items' not in response.json():
            self.logger.warning(f"items does not exist: {query_string=}, {response.text=}")
        return response.json()['items']
    
    # TODO: integrate with other functions
    def get_managed_system_nodes(self):
        SYSTEM_NODE_NAME='system'
        system_query = f"node('system', system_type='switch', management_level='full_control', name='{SYSTEM_NODE_NAME}')"
        resp = self.query(system_query)
        self.managed_system_nodes = [x[SYSTEM_NODE_NAME] for x in resp]
        return self.managed_system_nodes

    
    # return the first entry for the system
    def get_system_with_im(self, system_label):
        system_im = self.query(f"node('system', label='{system_label}', name='system').out().node('interface_map', name='im')")[0]
        if system_label not in self.system_label_2_id_cache:
            self.system_label_2_id_cache[system_label] = system_im['system']['id']
            self.system_id_2_label_cache[system_im['system']['id']] = system_label
            if  'interface_map_id' not in self.system_label_2_id_cache[system_label]:
                self.system_label_2_id_cache[system_label]['interface_map_id'] = system_im['im']['id']
                self.system_label_2_id_cache[system_label]['device_profile_id'] = system_im['im']['device_profile_id']
        return system_im

    def get_system_node_from_label(self, system_label) -> dict:
        """
        Return the system dict from the system label
        called from move_access_switch
        """
        # cache the id of the system_label if not already cached
        if system_label not in self.system_label_2_id_cache:
            system_query_result = self.query(f"node('system', label='{system_label}', name='system')")
            # skip if the system does not exist
            if len(system_query_result) == 0:
                return None            
            id = system_query_result[0]['system']['id']
            # sn = system_query_result[0]['system']['system_id']
            # deploy_mode = system_query_result[0]['system']['deploy_mode']
            # self.system_label_2_id_cache[system_label] = { 
            #     'id': id,
            #     'sn': sn,
            #     'deploy_mode': deploy_mode
            #     }
            self.system_label_2_id_cache[system_label] = system_query_result[0]['system']
            self.system_id_2_label_cache[id] = system_label
        return self.system_label_2_id_cache[system_label]

    def get_system_label(self, system_id):
        '''
        Get the system label from the system id
        '''
        if system_id not in self.system_id_2_label_cache:
            return None
        return self.system_id_2_label_cache[system_id]

    def get_server_interface_nodes(self, system_label, intf_name=None) -> str:
        """
        Return interface nodes of a system label
            return CkEnum.MEMBER_INTERFACE and CkEnum.MEMBER_SWITCH
                optionally CkEnum.EVPN_INTERFACE if it is a LAG
            It can be used for VLAN CT association
            TODO: implement intf_name in case of multiple link generic system
        TODO: cache generic system interface id
        called by move_access_switch
        """
        interface_query = f"""
            match(
                node('system', system_type='server', label='{system_label}')
                    .out('hosted_interfaces').node('interface', name='{CkEnum.GENERIC_SYSTEM_INTERFACE}')
                    .out('link').node('link', name='{CkEnum.LINK}')
                    .in_('link').node('interface', name='{CkEnum.MEMBER_INTERFACE}')
                    .in_('hosted_interfaces').node('system', system_type='switch', name='{CkEnum.MEMBER_SWITCH}'),
                optional(
                    node('interface', po_control_protocol='evpn', name='{CkEnum.EVPN_INTERFACE}')
                        .out('composed_of').node('interface')
                        .out('composed_of').node(name='{CkEnum.MEMBER_INTERFACE}')
                )
            )
        """
        return self.query(interface_query, multiline=True)

    def get_switch_interface_nodes(self, system_labels, intf_name=None) -> str:
        """
        Return interface nodes of the switches
            system_labels: list of system labels or a str for the single system label
            return CkEnum.MEMBER_INTERFACE and CkEnum.MEMBER_SWITCH
                optionally CkEnum.EVPN_INTERFACE if it is a LAG
            It can be used for VLAN CT association
            TODO: implement intf_name in case of multiple link generic system
        TODO: cache generic system interface id
        """
        the_system_labels = system_labels if isinstance(system_labels, list) else [system_labels] if isinstance(system_labels, str) else []
        if len(the_system_labels) == 0:
            self.logger.warning(f"{system_labels=} is not a list or string")
            return []
        intf_name_filter = f", if_name='{intf_name}'" if intf_name else ""
        interface_query = f"""
            match(
                node('system', system_type='server', name='{CkEnum.GENERIC_SYSTEM}')
                    .out('hosted_interfaces').node('interface', name='{CkEnum.GENERIC_SYSTEM_INTERFACE}')
                    .out('link').node('link', name='{CkEnum.LINK}')
                    .in_('link').node('interface', if_type='ethernet', name='{CkEnum.MEMBER_INTERFACE}'{intf_name_filter})
                    .in_('hosted_interfaces').node('system', system_type='switch', label=is_in({the_system_labels}), name='{CkEnum.MEMBER_SWITCH}'),
                optional(
                    node('redundancy_group')
                        .out('hosted_interfaces').node('interface', po_control_protocol='evpn', name='{CkEnum.EVPN_INTERFACE}')
                        .out('composed_of').node('interface')
                        .out('composed_of').node(name='{CkEnum.MEMBER_INTERFACE}')
                ),
                optional(
                    node('tag', name='tag').out().node(name='{CkEnum.LINK}')
                    )
            )
        """
        # self.logger.debug(f"{interface_query=}")
        interface_nodes = self.query(interface_query, multiline=True)
        # self.logger.debug(f"{interface_nodes=}")
        return interface_nodes


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
        ct_list = self.query(ct_list_spec, multiline=True)
        tagged_nodes = [x for x in ct_list if 'vlan_tagged' in x['ep_endpoint_policy']['attributes']]
        tagged_ct = len(tagged_nodes) and tagged_nodes[0]['ct']['id'] or None
        # tagged_ct = [x['id'] for x in ct_list if x and 'vlan_tagged' in x['ep_endpoint_policy']['attributes']][0] or None
        untagged_nodes = [x for x in ct_list if 'untagged' in x['ep_endpoint_policy']['attributes']]
        untagged_ct = len(untagged_nodes) and untagged_nodes[0]['ct']['id'] or None
        # untagged_ct = [x['id'] for x in ct_list if x and 'untagged' in x['ep_endpoint_policy']['attributes']][0] or None
        return (tagged_ct, untagged_ct)

    def get_ct_ids(self, ct_labels: list) -> list:
        '''
        Get the CT IDs from the CT labels
        '''
        ct_list_query = f"""
            node('ep_endpoint_policy', policy_type_name='batch', label=is_in({ct_labels}), name='ep')
        """
        ct_list = self.query(ct_list_query, multiline=True)
        if len(ct_list) == 0:
            self.logger.debug(f"No CTs found for {ct_labels=}")
            return []
        return [x['ep']['id'] for x in ct_list]
    
    def add_generic_system(self, generic_system_spec: dict) -> list:
        """
        Add a generic system (and access switch pair) to the blueprint.

        Args:
            generic_system_spec: The specification of the generic system.

        Returns:
            The ID of the switch-system-link ids.
        """
        new_generic_system_label = generic_system_spec['new_systems'][0]['label']
        existing_system_query = f"node('system', label='{new_generic_system_label}', name='system')"
        existing_system = self.query(existing_system_query)
        if len(existing_system) > 0:
            # skipping if the system already exists
            return []
        url = f"{self.url_prefix}/switch-system-links"
        created_generic_system = self.session.session.post(url, json=generic_system_spec)
        if created_generic_system.status_code >= 400:
            self.logger.error(f"System not created: {created_generic_system=}, {new_generic_system_label=}, {created_generic_system.text=}")
            return []
        if created_generic_system is None or len(created_generic_system.json()) == 0 or 'ids' not in created_generic_system.json():
            return []
        return created_generic_system.json()['ids']

    def get_transformation_id(self, system_label, intf_name, speed) -> int:
        '''
        Get the transformation ID for the interface

        Args:
            system_label: The label of the system
            intf_name: The name of the interface
            speed: The speed of the interface in the format of '10G'
        '''
        system_im = self.get_system_with_im(system_label)
        device_profile = self.session.get_device_profile(system_im['im']['device_profile_id'])

        for port in device_profile['ports']:
            for transformation in port['transformations']:
                # self.logger.debug(f"{transformation=}")
                for intf in transformation['interfaces']:
                    # if intf['name'] == intf_name:
                    #     self.logger.debug(f"{intf=}")
                    if intf['name'] == intf_name and intf['speed']['unit'] == speed[-1:] and intf['speed']['value'] == int(speed[:-1]): 
                        # self.logger.warning(f"{intf_name=}, {intf=}")
                        return transformation['transformation_id']

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
        vn_id_got = self.query(f"node('virtual_network', vn_id='{vni}', name='vn')")
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
            'tags': [],
            'nodes': [],
            'remove': [],
            'assigned_to_all': [],
        }
        # take string or list 
        the_nodes_list = nodes if isinstance(nodes, list) else [nodes] if isinstance(nodes, str) else []
        if len(the_nodes_list) == 0:
            self.logger.warning(f"{nodes=} is not a list or string")
            return
        # no need to check the present of tags in tags_to_add 
        tag_nodes = self.query(f"node(id=is_in({the_nodes_list})).in_().node('tag', label=is_in({tags_to_add}), name='tag')")
        are_tags_the_same = len(tag_nodes) == (len(tags_to_add) * len(nodes))
        self.logger.debug(f"{nodes=} {the_nodes_list=} {tags_to_add=}, {tags_to_remove=}, {are_tags_the_same=} {tag_nodes}")

        # self.logger.debug(f"{nodes=} {tags_to_add=}, {tags_to_remove=} {are_tags_the_same=}")
        # The tags are the same as the existing tags
        if are_tags_the_same or (not tags_to_add and not tags_to_remove):
            return
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

    def batch(self, batch_spec: dict, params=None) -> None:
        '''
        Run API commands in batch
        '''
        url = f"{self.url_prefix}/batch"
        self.session.session.post(url, json=batch_spec, params=params)

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
                   for x in self.query(ct_list_spec, multiline=True)]
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
        found_vn_node = self.query(f"node('virtual_network', vn_id='{vni}', name='vn')")
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

    def patch_cable_map(self, cable_map_spec):
        '''
        Set the cabling map
        '''
        url = f"{self.url_prefix}/cabling-map"
        patched = self.session.session.patch(url, json=cable_map_spec, params={'comment': 'cabling-map-update'})
        if patched.status_code == 204:
            # No Content: a request has succeeded, but that the client doesn't need to navigate away from its current page.
            return None
        return patched

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


if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()
    log_level = os.getenv('logging_level', 'DEBUG')
    prep_logging(log_level)

    apstra_server_host = os.getenv('apstra_server_host')
    apstra_server_port = os.getenv('apstra_server_port')
    apstra_server_username = os.getenv('apstra_server_username')
    apstra_server_password = os.getenv('apstra_server_password')

    apstra = CkApstraSession(apstra_server_host, apstra_server_port, apstra_server_username, apstra_server_password)
    bp = CkApstraBlueprint(apstra, os.getenv('main_blueprint'))
    print(bp.get_id())
