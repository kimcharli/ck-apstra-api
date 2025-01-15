from typing import Any, Dict
from dataclasses import dataclass, asdict
import json

from ck_apstra_api import CkApstraBlueprint, prep_logging


INTERCONNECT = 'evpn_interconnect_groups'
IC_ROUTING_ZONES = 'interconnect_security_zones'
IC_VIRTUAL_NETWORKS = 'interconnect_virtual_networks'


@dataclass
class DciSettingsInFile:
    esi_mac_msb: int = None

@dataclass
class InterconnectInFile:
    pass

@dataclass
class DciInFile:
    interconnect: Any = None  # {'dc-name': {dc-data}} InterconnectInFile = None
    ott: Any = None
    settings: DciSettingsInFile = None

    def __post_init__(self):
        self.interconnect = {}
        self.settings = DciSettingsInFile()



@dataclass
class PhysicalInFile:
    node: Any = None # { label: { system dict }}

    def __post_init__(self):
        self.node = {}

    def add_node(self, systems_dict: Dict):
        self.node = {k: v for k, v in systems_dict.items()}


@dataclass
class CatalogInFile:
    logical_device: Any = None  # { label: {'panels': [panels] } }
    interface_map: Any = None # InterfaceMapInFile = None


@dataclass
class BpInFile:
    physical: PhysicalInFile = None
    dci: Any = None  # {'dci-name': DciInFile }
    catalog: CatalogInFile = None

    def __post_init__(self):
        self.physical = PhysicalInFile()
        self.dci = DciInFile()
        self.catalog = CatalogInFile()


@dataclass
class DesignInFile:
    rack_type: Any = None

    def __post_init__(self):
        self.rack_type = {}

    def dict(self):
        return {k: v for k, v in asdict(self).items()}

    def add_rack_type(self, rack_name, rack_data):
        if rack_name not in self.rack_type:
            self.rack_type[rack_name] = rack_data




def get_first_last_tuples(data: dict) -> list:
    """get the first and last tuples 'ranges'"""
    return [(x['first'], x['last']) for x in data['ranges']]


def get_subnets(data: dict) -> list:
    """get the network from a list of dicts 'subnets"""
    return [x['network'] for x in data['subnets']]

def get_devices(data: dict) -> list:
    """get the device ids from a list of dicts 'devices'"""
    return [x['id'] for x in data['devices']]

# @dataclass
# class ResourceInFile:
#     asn: Any = None
#     vni: Any = None
#     integer: Any = None
#     ip: Any = None
#     ipv6: Any = None

#     def __post_init__(self):
#         self.asn = {}
#         self.vni = {}
#         self.integer = {}
#         self.ip = {}
#         self.ipv6 = {}
    



@dataclass
class DataInFile:
    blueprint: Any = None  # { bp_name: BpInFile }
    design: DesignInFile = None
    resource: Any = None # { resource_name: { resource_data } }
    # session
    # bp_data: CkApstraBlueprint = None
    # bp_in_file: BpInFile = None
    # rack_type_map: dict = None
    # logical_device_map: dict = None

    def __post_init__(self):
        self.blueprint = {}
        self.design = DesignInFile()
        self.resource = {}

    def as_dict(self):
        return asdict(self)

    def get_blueprint(self, session, bp_name) -> CkApstraBlueprint:
        """ Get the blueprint object. If not found, return None """
        self.logger = prep_logging('DEBUG', f"DataInFile(bp={bp_name})")
        self.session = session
        self.bp_data = CkApstraBlueprint(session, bp_name)
        if not self.bp_data.id:
            self.logger.error(f"Blueprint {bp_name} not found")
            return None
        self.logger.info(f"{bp_name=}, {self.bp_data.id=}")
        if self.bp_data.id:
            self.logger.info(f"Blueprint {bp_name} found")
            # # set the bp_in_file to the blueprint data in th           
            self.bp_in_file = self.blueprint[bp_name] = BpInFile()
            return self.bp_data
        else:
            self.logger.warning(f"Blueprint {bp_name} not found")
            return None

    def get_rack_type_map_from_blueprint(self) -> dict:
        """Get the rack type map from the blueprint"""
        rack_data = self.bp_data.query("node('rack', name='rack')").ok_value
        self.design.rack_type = { x['rack']['label']: json.loads(x['rack']['rack_type_json']) for x in rack_data}
        self.rack_type_map = { x['rack']['id']: x['rack']['label'] for x in rack_data}
        return self.rack_type_map

    def get_logical_device_map_from_blueprint(self) -> dict:
        """Get the logical device map from the blueprint"""
        logical_device_list = self.bp_data.get_experience_web_logical_devices_items()
        self.bp_in_file.catalog.logical_device = { x['display_name']: {'panels': x['panels']} for x in logical_device_list}
        self.logical_device_map = { x['id']: x['display_name'] for x in logical_device_list}
        return self.logical_device_map

    def get_interface_map_map_from_blueprint(self):
        """Get the interface map map from the blueprint"""
        interface_map_list = self.bp_data.get_experience_web_interface_maps_items()
        # if not self.logical_device_map:
        #     self.get_logical_device_map()
        self.bp_in_file.catalog.interface_map = { x['label']: { 
            # 'logical_device': self.logical_device_map[x['logical_device_id']], 
            'logical_device': x['logical_device_id'], 
            'device_profile': x['device_profile_id']} for x in interface_map_list}
        self.interface_map_map = { x['id']: x['label'] for x in interface_map_list}
        return self.interface_map_map

    def get_system_nodes_from_blueprint(self):
        """Get the system nodes from the blueprint"""
        system_info_list = self.bp_data.get_experience_web_system_info_list()
        self.system_map = { x['id']: x['label'] for x in system_info_list}
        try:
            self.bp_in_file.physical.add_node({ x['label']: {
                'label': x['label'],
                'role': x['role'],
                'tags': x['tags'],
                'asn': x['domain_id'],
                'deploy_mode': x['deploy_mode'],
                'external': x['external'],
                'interface_map': self.interface_map_map.get(x.get('interface_map_id', None), None),
                'device_profile': x['device_profile_id'],
                'logical_device': self.logical_device_map.get(x.get('logical_device', None), None),
                'rack': self.rack_type_map.get(x['rack_id'], None),
                'hostname': x['hostname'],
                'loopback_ipv4': (x.get('loopback', {}) or {}).get('ipv4_addr', None),
                'loopback_ipv6': (x.get('loopback', {}) or {}).get('ipv6_addr', None),
                } for x in system_info_list})
        except Exception as e:
            breakpoint()
        return self.system_map


    def pull_resources(self):
        """
        resources = cliVar.data_in_file.resource
        """
        pool_map = {
            'asn-pools': get_first_last_tuples,
            'device-pools': get_devices,
            'ip-pools': get_subnets,
            'ipv6-pools': get_subnets,
            'vni-pools': get_first_last_tuples,
            # 'integet-pools'
            # 'vlan-pools'
        }

        for pool, func in pool_map.items():
            data = self.session.get_items(f'resources/{pool}')['items']
            self.resource[pool] = {x['display_name']: func(x) for x in data}
            # logger.debug(f"{resources[pool]=}")


    def pull_ic_virtual_networks(delf, ic_datum_in_blueprint: dict, ic_datum: dict):
        """
        Retrieve virtual networks

        """
        logger = prep_logging('DEBUG', 'pull_ic_virtual_networks()')

        variables = ['label', 'translation_vni', 'vrf_name', 'vni', 'l2', 'l3']
        ic_datum[IC_VIRTUAL_NETWORKS] = { v1['label']: 
                                    { k2: v2 for k2, v2 in v1.items() if k2 in variables } 
                                    for v1 in ic_datum_in_blueprint[IC_VIRTUAL_NETWORKS].values()}

        return
    

    def pull_ic_routingz_zones(self, ic_datum_in_blueprint: dict, ic_datum: dict):
        """
        Retrieve routing zones

        """
        logger = prep_logging('DEBUG', 'pull_ic_routingz_zones()')

        variables = ['vrf_name', 'routing_policy_label', 'interconnect_route_target', 'enabled_for_l3']
        ic_datum[IC_ROUTING_ZONES] = { v1['vrf_name']: 
            { k2: v2 for k2, v2 in v1.items() if k2 in variables } 
            for v1 in ic_datum_in_blueprint[IC_ROUTING_ZONES].values()}

        return


    def pull_remote_gateway_node_ids(self, ic_rw_node_ids:dict, ic_datum: dict ):
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


    def pull_interconnect(self):
        """
        Pull interconnect data from the blueprint

        """
        logger = prep_logging('DEBUG', 'pull_interconnect()')

        bp = self.bp_data
        ic_tree = self.bp_in_file.dci.interconnect

        variables = ['label', 'interconnect_route_target', 'interconnect_esi_mac']

        # retrieve top level variables
        ic_data_in_blueprint = bp.get_item(INTERCONNECT)[INTERCONNECT]
        if not ic_data_in_blueprint:
            logger.info(f"No DCI interconnect data in blueprint {bp.label}")
            return
        
        # 'evpn_interconnect_groups': [ dci, dci, ...]
        for ic_datum_in_bp in ic_data_in_blueprint:
            ic_datum = { k: v for k, v in ic_datum_in_bp.items() if k in variables  }

            self.pull_remote_gateway_node_ids(ic_datum_in_bp['remote_gateway_node_ids'], ic_datum)
            self.pull_ic_routingz_zones(ic_datum_in_bp, ic_datum)
            self.pull_ic_virtual_networks(ic_datum_in_bp, ic_datum)

            ic_tree[ic_datum['label']] = ic_datum

        return
