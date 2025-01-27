"""
This module is used to read and write the data between the blueprint in the server and the file and store it in the DataInFile object
"""

from typing import Any, Dict
from dataclasses import dataclass
import json

from ck_apstra_api import CkApstraBlueprint, prep_logging
from .blueprint import BpInFile

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
    # logger: Any = None
    # session
    # bp_name: str = None
    ## moved to property ck_bp: CkApstraBlueprint = None
    # bp_in_file: BpInFile = None
    # rack_type_map: dict = None
    # logical_device_map: dict = None

    def __post_init__(self):
        self.blueprint = {}
        self.design = DesignInFile()
        self.resource = {}
        self.rack_type_map = {}
        self.logger = prep_logging('DEBUG', "DataInFile")

    @property
    def ck_bp(self) -> CkApstraBlueprint:
        return self.bp_in_file.ck_bp

    def get_blueprint(self, session, bp_name) -> CkApstraBlueprint:
        """ Get the blueprint object. If not found, return None """
        self.logger = prep_logging('DEBUG', f"DataInFile(bp={bp_name})")
        self.session = session
        self.bp_name = bp_name
        ck_bp = CkApstraBlueprint(self.session, self.bp_name)
        if not ck_bp.id:
            self.logger.error(f"Blueprint {bp_name} not found")
            return None
        self.logger.info(f"Blueprint {bp_name=}, id: {ck_bp.id}")
        self.bp_in_file = self.blueprint[bp_name] = BpInFile()
        self.bp_in_file.ck_bp = ck_bp
        return ck_bp
 
    def get_rack_type_map_from_blueprint(self) -> dict:
        """Get the rack type map from the blueprint"""
        rack_data = self.ck_bp.query("node('rack', name='rack')").ok_value
        self.design.rack_type = { x['rack']['label']: json.loads(x['rack']['rack_type_json']) for x in rack_data}
        self.rack_type_map = { x['rack']['id']: x['rack']['label'] for x in rack_data}
        return self.rack_type_map

    def get_logical_device_map_from_blueprint(self) -> dict:
        """Get the logical device map from the blueprint"""
        logical_device_list = self.ck_bp.get_experience_web_logical_devices_items()
        self.bp_in_file.catalog.logical_device = { x['display_name']: {'panels': x['panels']} for x in logical_device_list}
        self.logical_device_map = { x['id']: x['display_name'] for x in logical_device_list}
        return self.logical_device_map

    def get_interface_map_map_from_blueprint(self):
        """Get the interface map map from the blueprint"""
        interface_map_list = self.ck_bp.get_experience_web_interface_maps_items()
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
        system_info_list = self.ck_bp.get_experience_web_system_info_list()
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
                # 'interface_map': x.get('interface_map_id', None),
                'device_profile': x['device_profile_id'],
                'logical_device': self.logical_device_map.get(x.get('logical_device', None), None),
                'rack': self.rack_type_map.get(x['rack_id'], None),
                'hostname': x['hostname'],
                'loopback_ipv4': (x.get('loopback', {}) or {}).get('ipv4_addr', None),
                'loopback_ipv6': (x.get('loopback', {}) or {}).get('ipv6_addr', None),
                } for x in system_info_list})
        except Exception as e:            
            self.logger.error(f"Error: {e}")
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


