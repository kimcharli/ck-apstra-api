from typing import Any, Dict
from dataclasses import dataclass

from ck_apstra_api import prep_logging

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


    def pull_ic_virtual_networks(self, ic_datum_in_blueprint: dict, ic_datum: dict):
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


    def pull_interconnect(self, bp):
        """
        Pull interconnect data from the blueprint

        """
        logger = prep_logging('DEBUG', 'pull_interconnect()')

        ic_tree = self.interconnect

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
    # ck_bp  # set from data_in_file

    def __post_init__(self):
        self.physical = PhysicalInFile()
        self.dci = DciInFile()
        self.catalog = CatalogInFile()
