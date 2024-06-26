
import logging
from math import isnan
from pathlib import Path
from dataclasses import dataclass, fields, field
from types import GeneratorType
from typing import Generator, List, Optional, Any, TypeVar, Annotated, Dict, ClassVar
from collections import Counter, defaultdict
import os
import uuid
import pprint
from enum import Enum, StrEnum, auto

import pandas as pd
import numpy as np
from result import Result, Ok, Err

from ck_apstra_api.apstra_session import CkApstraSession
from ck_apstra_api.apstra_blueprint import CkApstraBlueprint, CkEnum


class GsCsvKeys(StrEnum):
    """The Keys for the Generic System CSV file"""
    LINE = auto()
    """The line number for each entries in CSV file. This value can be used to create dummpy names for other members"""
    BLUEPRINT = auto()
    SERVER = auto()
    EXT = auto()
    """Designates if the generic system is external"""
    TAGS_SERVER = auto()
    """Tags for the generic system itself"""
    AE = auto()
    """The unique id for the link group within the generic system. When absent, it will be assigned '____{line}' to be used as a dummy name"""
    LAG_MODE = auto()
    CT_NAMES = auto()
    TAGS_AE = auto()
    """Tags for the link group"""
    SPEED = auto()
    IFNAME = auto()
    SWITCH = auto()
    SWITCH_IFNAME = auto()
    TAGS_LINK = auto()
    """Tags for the link itself"""
    COMMENT = auto()


@dataclass
class DataInit:
    """Build a data class with the given input dict."""
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize the data class with the given input dict.
        """
        cls_fields = [field.name for field in fields(self)]
        for key, value in data.items():
            if key in cls_fields:
                setattr(self, key, value)


@dataclass
class LeafSwitch:
    """The class to hold the switch data"""
    switch_label: str
    # id: str = None
    nodes: List[Dict[str, Any]] = field(default_factory=list)  # store the node data of the switch
    interfaces: Dict[str, Any] = field(default_factory=dict)  # store the interface data of the switch
    bp: CkApstraBlueprint = None
    log_prefix: str = None
    # class variable to store the switch data
    _switches: ClassVar[Dict[str, Any]] = {}  # Dict[switch name, LeafSwitch]

    def __new__(cls, switch_label: str, bp: CkApstraBlueprint):        
        if switch_label in cls._switches:
            return cls._switches[switch_label]
        else:
            switch = super().__new__(cls)
            cls._switches[switch_label] = switch
            return switch

    def __init__(self, switch_label: str, bp: CkApstraBlueprint):
        """
        Initialize the switch data.
        """
        self.log_prefix = f"LeafSwitch({switch_label})"
        self.switch_label = switch_label
        # log_prefix = f"{self.log_prefix}::init()"
        self.bp = bp
        
        switch_interfaces_nodes_result = self.bp.get_switch_interface_nodes(self.switch_label)
        # logging.warning(f"{self.log_prefix} {switch_interfaces_nodes_result=}")
        if isinstance(switch_interfaces_nodes_result, Err):
            return Err(f"LeafSwitch::__init__ {self.switch_label=} not found in blueprint {self.bp.label}")
        self.nodes = switch_interfaces_nodes_result.ok_value
        # self.id = self.nodes[0][CkEnum.MEMBER_SWITCH]['id']
        # logging.warning(f"{self.log_prefix} {self.switch_label=} {self.nodes=}")
        self.interfaces = {x[CkEnum.MEMBER_INTERFACE]['if_name']: x[CkEnum.MEMBER_INTERFACE] for x in self.nodes}

    @property
    def id(self):
        return self.nodes[0][CkEnum.MEMBER_SWITCH]['id']
    
    # might not be needed
    def interface_id(self, if_name: str) -> str:
        # logging.warning(f"{self.log_prefix} {if_name=} {self.interfaces=}")
        if if_name in self.interfaces:
            return self.interfaces[if_name]['id']
        else:
            return None

@dataclass
class LinkMember(DataInit):
    """
    Data class for a single link in a generic system. Can be part of LinkGroup
    """
    line: int   # the line number in the csv file to be used for matching. Had local use per CSV file
    speed: Optional[str]
    ifname: Optional[str]
    switch: str
    switch_ifname: str
    tags_link: Optional[List[str]]
    comment: Optional[str] = None
    # fetched data
    fetched_server_ifname: Optional[str] = None
    fetched_server_intf_id: Optional[str] = None
    fetched_switch_id: Optional[str] = None
    fetched_switch_intf_id: Optional[str] = None
    fetched_tags_link: Optional[List[str]] = None
    fetched_link_id: Optional[str] = None

    bp: CkApstraBlueprint = field(default=None, repr=False)  # the apstra blueprint to be used for fetching the data
    fetched_evpn_interface: Optional[Dict[str, Any]] = field(default=None, repr=False)   # the evpn_interface node fetched from the apstra controller
    fetched_ae_interface: Optional[Dict[str, Any]] = field(default=None, repr=False)  # the ae_interface node fetched from the apstra controller

    log_prefix: str = field(default='', repr=False)  # not to print in __repr__

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize the link member with the given input dict.
        """
        super().__init__(data)
        if self.tags_link and isinstance(self.tags_link, str):
            self.tags_link = self.tags_link.split(',')
        elif self.tags_link == '':
            self.tags_link = []
        self.speed = self.speed.upper()
        self.log_prefix = f"LinkMember({self.switch}:{self.switch_ifname}:{self.ifname})"

    # TODO: init to [] for fetched_tags_link
    def __post_init__(self):
        self.fetched_tags_link = []


    def fetch_apstra(self, server_links: list, apstra_bp) -> Generator[Result[str, str], Any, Any]:
        """
        Fetch the link member from the apstra controller.        
        """
        log_prefix = f"{self.log_prefix}::fetch_apstra()"
        self.bp = apstra_bp
        # yield Ok(f"{log_prefix} begin")

        # find the server links data staged in Apstra.
        found = [x for x in server_links if x[CkEnum.MEMBER_SWITCH]['label'] == self.switch and x[CkEnum.MEMBER_INTERFACE]['if_name'] == self.switch_ifname]
        if found:
            found = found[0]
            if found[CkEnum.LINK]['speed'] != self.speed:
                yield Err(f"Error: {log_prefix} speed mismatch {found[CkEnum.LINK]['speed']} != {self.speed}")
            self.fetched_server_ifname = found[CkEnum.GENERIC_SYSTEM_INTERFACE]['if_name']
            self.fetched_switch_id = found[CkEnum.MEMBER_SWITCH]['id']
            self.fetched_switch_intf_id = found[CkEnum.MEMBER_INTERFACE]['id'] 
            self.fetched_evpn_interface = found[CkEnum.EVPN_INTERFACE]
            self.fetched_ae_interface = found[CkEnum.AE_INTERFACE]
            self.fetched_link_id = found[CkEnum.LINK]['id']
            self.fetched_server_intf_id = found[CkEnum.GENERIC_SYSTEM_INTERFACE]['id']
            # yield Ok(f"{log_prefix} link present - switch({self.switch}:{self.fetched_switch_id}) {self.switch_ifname}:{self.fetched_switch_intf_id} {self.fetched_server_ifname=}")
        else:
            # not found. Load data from switch links
            switch = LeafSwitch(self.switch, self.bp)
            self.fetched_switch_id = switch.id
            self.fetched_switch_intf_id = switch.interface_id(self.switch_ifname)
            # yield Ok(f"{log_prefix} link absent - switch({self.switch}:{self.fetched_switch_id}) {self.switch_ifname}:{self.fetched_switch_intf_id} {self.fetched_server_ifname=}")
        yield Ok(f"{log_prefix} done {self}")

    def diff(self):
        """
        Diff the loaded data with the apstra controller.
        """
        return_message = ""
        if self.fetched_server_ifname != self.server_ifname:
            return_message += f"LinkMember:diff(), {self.fetched_server_ifname=} != {self.server_ifname=}"
        if self.tags_link != self.fetched_tags_link:
            return_message += f"LinkMember:diff(), {self.switch_label=}:{self.switch_ifname=} tags mismatch {self.tags_link} != {self.fetched_tags_link}"
        yield Ok(return_message)

    @property
    def application_point(self):
        """Return application point to be used to assign the connectivity template"""
        return self.fetched_evpn_interfaces['id'] if self.fetched_evpn_interface else self.fetched_switch_id

    @property
    def link_spec(self):
        """
        Return the link spec for the link member
        """
        transformation_id_result = self.bp.get_transformation_id(self.switch, self.switch_ifname , self.speed)
        link_spec = {
            'switch': {
                'system_id': self.fetched_switch_id,
                'transformation_id': transformation_id_result.ok_value,
                'if_name': self.switch_ifname,
            },
            'system': {
                'system_id': None,
            },
            'lag_mode': None,
            'link_group_label': None
        }
        return link_spec

    @property
    def rename_spec(self):
        """
        Return the rename spec for the link member
        """
        log_prefix = f"{self.log_prefix}::rename_spec()"
        # logging.warning(f"{log_prefix} begin {self=}")
        if self.fetched_server_ifname != self.ifname:
            return {
                'endpoints': [
                    {
                        'interface': {
                            'id': self.fetched_switch_intf_id
                        }
                    },
                    {
                        'interface': {
                            'id': self.fetched_server_intf_id,
                            'if_name': self.ifname
                        }
                    }
                ],
                'id': self.fetched_link_id
            }
        else:
            return None

@dataclass
class LinkGroup(DataInit):
    """
    Data class for a group of links in a generic system. Can be a LAG.
    """
    ae: Optional[str]  # the unique id for the link group within the generic system. When absent, the link will be treated as a non-LAG single link
    lag_mode: Optional[str]  # the LAG mode for the link group. 'lacp_active', 'lacp_passive', for None for static LAG or non-LAG single link
    ct_names: Optional[List[str]]  # the list of connectivity templates for the link group, or non-LAG single link
    tags_ae: Optional[List[str]]  # the list of tags for the link group, or non-LAG single link
    # child
    members: Optional[List[LinkMember]] = field(default=None, repr=False) # the list of links in the link group. optional only during initial creation
    # fetched
    fetched_ae_id: Optional[str] = None  # the fetched ae_id from the apstra controller. It will be the member link id in case of non-lag
    fetched_lag_mode: Optional[str] = None  # the fetched lag mode from the apstra controller
    fetched_ct_names: Optional[List[str]] = None
    fetched_tags: Optional[List[str]] = None  # the fetched tags from the apstra controller

    bp: CkApstraBlueprint = field(default=None, repr=False)  # the apstra blueprint to be used for fetching the data

    log_prefix: str = field(default='', repr=False)  # not to print in __repr__

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        if self.tags_ae and isinstance(self.tags_ae, str):
            self.tags_ae = self.tags_ae.split(',')
        if not self.ae:
            self.ae = f"____{data[GsCsvKeys.LINE]}"
        self.members = [LinkMember(data)]
        self.log_prefix = f"LinkGroup({self.ae})"
        # logging.warning(f"LinkGroup::init added LinkMember {self.members=}")

    def load_link_member(self, data: Dict[str, Any]):
        """
        Load the link member data from input dict into the link group.
        """
        self.members.append(LinkMember(data))
        # logging.warning(f"LinkGroup::load_link_member added LinkMember {self.members=}")

    def fetch_apstra(self, server_links: list, apstra_bp) -> Generator[Result[str, str], Any, Any]:
        """
        Fetch the link group from the apstra controller.
        """
        log_prefix = f"{self.log_prefix}::fetch_apstra()"
        self.bp = apstra_bp
        # yield Ok(f"{log_prefix} begin")
        # interate over the members and see if they have group link associated
        for counter, member in enumerate(self.members):
            for res in member.fetch_apstra(server_links, self.bp):
                yield res
            # member matched. Update the link group, only once
            if counter == 0:
                if member.fetched_evpn_interface:
                    # TODO: decide between this and member.application_point()
                    self.fetched_ae_id = member.fetched_evpn_interface['id']
                if member.fetched_ae_interface:
                    self.ae = member.fetched_ae_interface['if_name']
                    self.fetched_lag_mode = member.fetched_ae_interface['lag_mode']
        yield Ok(f"{log_prefix} done {self}")
        
    def form_lacp(self):
        """
        Form the LACP for the link group
        """
        log_prefix = f"{self.log_prefix}::form_lacp()"

        if not self.lag_mode:
            # None or ''
            yield Ok(f"{log_prefix} {self.ae=} is not for lag. Skipping")
            return
        
        if self.fetched_ae_id:
            yield Ok(f"{log_prefix} {self.ae=} is already lag {self.fetched_ae_id}. Skipping")
            return

        lag_spec = {
            'links': {x.fetched_link_id: {'group_label': self.ae, 'lag_mode': self.lag_mode} for x in self.members}
        }
        # update LACP
        lag_updated = self.bp.patch_leaf_server_link_labels(lag_spec)
        if lag_updated:
            yield Err(f"Unexpected return: LACP updated for link group {self.ae} {self.lag_mode=} in blueprint {self.bp.label}: {lag_updated}")
        else:
            yield Err(f"{log_prefix} {self.ae=} has no ae_id. Skipping")

    @property
    def link_spec(self):
        """
        Return the link spec for the link group gathered from the links
        """
        data = []
        for member in self.members:
            data.append(member.link_spec)
        return data
    
    @property
    def speed_count(self):
        return [x.speed for x in self.members]

    def diff(self):
        """
        Diff the loaded data with the apstra controller.
        """
        return_message = ""
        if self.ae and self.link_group_fetched_ae_id is None:
            return_message += f"LinkGroup:diff(), {self.ae=} is absent in blueprint"
        if self.tags_ae != self.link_group_fetched_tags:
            return_message += f"LinkGroup:diff(), {self.ae=} tags mismatch {self.tags_ae} != {self.link_group_fetched_tags}"
        if self.link_group_lag_mode != self.link_group_fetched_lag_mode:
            return_message += f"LinkGroup:diff(), {self.ae=} lag mode mismatch {self.link_group_lag_mode} != {self.link_group_fetched_lag_mode}"
        for member in self.members:
            member_result = member.diff()
            if isinstance(member_result, Err):
                yield Err(f"LinkGroup:diff(), {self.ae=}, {member.switch_label=}:{member.switch_ifname=}, Error: {member_result.err_value}")
            return_message += member_result.ok_value
        yield Ok(return_message)


    def rename_interfaces(self):
        log_prefix = f"{self.log_prefix}::rename_interfaces()"
        rename_spec = {'links': [member.rename_spec for member in self.members if member.rename_spec]}
        # for member in self.members:
        #     rename_spec.append(member.rename_spec)
        yield Ok(f"{log_prefix} {self.ae=} {rename_spec=}")
        if rename_spec['links']:
            rename_updated = self.bp.patch_cable_map(rename_spec)
            if rename_updated:
                yield Err(f"Unexpected return: Interface renamed for link group {self.ae} in blueprint {self.bp.label}: {rename_updated}")
            else:
                yield Ok(f"{self.log_prefix} {self.ae=} rename done")



@dataclass
class GenericSystem(DataInit):
    """
    Data class for a generic system.
    """
    server: str
    ext: Optional[bool]  # TBD: the external flag for the generic system
    tags_server: Optional[List[str]]
    # child
    link_groups: Optional[List[LinkGroup]] = field(default=None, repr=False)  # optional only during initial creation
    # fetched
    gs_id: Optional[str] = None # generic system node id to be fetched from the blueprint
    fetched_server_tags: Optional[List[str]] = None  # the fetched tags from the apstra controller
    bp: CkApstraBlueprint = field(default=None, repr=False)  # the apstra blueprint to be used for fetching the data

    log_prefix: str = field(default='', repr=False)  # not to print in __repr__
    
    # TODO: node('system', name='system', role='generic').in_('tag').node('tag', name='system_tag')


    def __init__(self, data: Dict[str, Any]):
        """
        Initialize the generic system with the given input dict.
        """
        super().__init__(data)
        if self.tags_server and isinstance(self.tags_server, str):
            self.tags_server = self.tags_server.split(',')
        self.log_prefix = f"GenericSystem({self.server})"
        self.link_groups = []
    
    def load_link_group(self, data):
        """
        Load the link group data from input dict into the generic system.
        """
        if ae := data[GsCsvKeys.AE]:
            the_link_groups = [x for x in self.link_groups if x.ae == ae]
            if the_link_groups:
                the_link_groups[0].load_link_member(data)
                return
        # new AE or non AE. Create it
        self.link_groups.append(LinkGroup(data))

    def fetch_apstra(self, apstra_bp: CkApstraBlueprint) -> Generator[Result[str, str], Any, Any]:
        """
        Fetch the generic system from the apstra controller.
        """
        log_prefix = f"{self.log_prefix}::fetch_apstra()"
        self.bp = apstra_bp
        server_link_result = self.bp.get_server_interface_nodes(self.server)
        server_links = server_link_result.ok_value
        for lg in self.link_groups:
            for res in lg.fetch_apstra(server_links, self.bp):
                lg_fetch_result = res
                if isinstance(lg_fetch_result, Err):
                    yield Err(f"{log_prefix} {lg.ae=}, Error: {lg_fetch_result.err_value}")
                else:
                    yield res
        if len(server_links):
            # yield Ok(f"{log_prefix} present in blueprint {apstra_bp.label}")
            self.gs_id = server_links[0][CkEnum.GENERIC_SYSTEM]['id']
            self.fetched_server_tags = server_links[0][CkEnum.GENERIC_SYSTEM]['tags']  # TODO: fix
            #
            tag_result = apstra_bp.query(f"node('system', name='system', label='{self.server}', role='generic').in_('tag').node('tag', name='system_tag')")
            if isinstance(tag_result, Err):
                yield Err(f"{log_prefix} Error: {tag_result.err_value}")
            tags = tag_result.ok_value
            self.fetched_server_tags = [tag['system_tag']['label'] for tag in tags]
        # if server_links is None or len(server_links) == 0:
        #     yield Ok(f"{log_prefix} not found in blueprint {apstra_bp.label}")
        yield f"{log_prefix} done {self}"


    def diff(self):
        """
        Diff the loaded data with the apstra controller.
        """
        return_message = ""
        if self.gs_id is None:
            yield Ok(f"GenericSystem:diff(), {self.server_label=} is absent in blueprint")
        if self.server_tags != self.fetched_server_tags:
            return_message += f"GenericSystem:diff(), {self.server_label=} tags mismatch {self.server_tags} != {self.fetched_server_tags}"
        for lg in self.link_groups:
            lg_result = lg.diff()
            if isinstance(lg_result, Err):
                yield Err(f"GenericSystem:diff(), {self.server_label=}, {lg.ae=}, Error: {lg_result.err_value}")
            return_message += lg_result.ok_value
        yield Ok(return_message)
    

    @property
    def system_type(self):
        return 'external' if self.ext else 'server'

    def create(self):
        log_prefix = f"{self.log_prefix}::create()"
        if self.gs_id:
            yield Ok(f"{log_prefix} present. No need to create this. Skipping")
            return
        speed_count = []
        for lg in self.link_groups:
            sc = lg.speed_count
            speed_count.extend(sc)
        display_name_list = ['ck-auto']
        port_groups = []
        # yield Ok(f"{log_prefix} {speed_count=} {Counter(speed_count)=}")
        for speed, count in dict(Counter(speed_count)).items():
            port_groups.append({
                "count": count,
                "speed": {
                    "unit": speed[-1],
                    "value": int(speed[:-1])
                },
                "roles": [
                    "leaf",
                    "access"
                ]
            })
            display_name_list.append(f"{count}x{speed[:-1]}")
        generic_system_spec = {
            'links': [],
            'new_systems': [{
                'system_type': self.system_type,
                'label': self.server,
                'port_channel_id_min': 0,
                'port_channel_id_max': 0,
                'logical_device': {
                    'display_name': '-'.join(display_name_list),
                    'id': '-'.join(display_name_list),
                    'panels': [
                        {
                            'panel_layout': {
                                'row_count': 1,
                                'column_count': len(speed_count),
                            },
                            'port_indexing': {
                                'order': 'T-B, L-R',
                                'start_index': 1,
                                'schema': 'absolute'
                            },
                            "port_groups": port_groups
                        }
                    ]
                },

            }],
        }
        for lg in self.link_groups:
            generic_system_spec['links'].extend(lg.link_spec)
        # creating the generic system
        yield Ok(f"{log_prefix} creating {generic_system_spec=}")
        generic_system_created_result = self.bp.add_generic_system(generic_system_spec)
        if isinstance(generic_system_created_result, Err):
            yield Err(f"{log_prefix} failed to create {generic_system_created_result.err_value}")
            return
        yield Ok(f"{log_prefix} created")

    def form_lacp(self):
        """
        Form the LACP for the generic system
        """
        for lg in self.link_groups:
            for res in lg.form_lacp():
                yield res

    def rename_interfaces(self):
        """
        Rename the interfaces for the generic system
        """
        for lg in self.link_groups:
            for res in lg.rename_interfaces():
                yield res


@dataclass
class ServerBlueprint(DataInit):
    """
    Data class for a blueprint for generic system building.
    """
    blueprint: str
    # child
    servers: Dict[str, GenericSystem] = field(default_factory=dict, repr=False) # optional only during initial creation
    #fetched value
    ck_bp: CkApstraBlueprint = field(default=None, repr=False)  # the apstra blueprint to be used for fetching the data
    # class variable to store the server data
    _bps: ClassVar[CkApstraBlueprint] = field(default={}, repr=False)  # Dict[str, ServerBlueprint]

    def __new__(cls, data: Dict[str, Any]):        
        blueprint = data[GsCsvKeys.BLUEPRINT]
        # logging.warning(f"ServerBlueprint::__new__ {data=}")
        if blueprint in cls._bps:
            return cls._bps[blueprint]
        else:
            bp = super().__new__(cls)
            cls._bps[blueprint] = bp
            return bp

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize the server blueprint with the given input data.
        """
        if not hasattr(self, 'servers'):
            super().__init__(data)
            self.servers = {}
        server_label = data[GsCsvKeys.SERVER]        
        # logging.warning(f"ServerBlueprint::init processing GS {server_label=}")
        if server_label not in self.servers:
            self.servers[server_label] = GenericSystem(data)
        this_server = self.servers[server_label]
        this_server.load_link_group(data)

    @classmethod
    def iterate_server_blueprints(cls):
        for k, v in cls._bps.items():
            yield k, v

    def interate_generic_systems(self):
        for k, v in self.servers.items():
            yield k, v

    def fetch_apstra(self, apstra_session: CkApstraSession) -> Result[str, str]:
        """
        Fetch the apstra blueprint from the server.
        """
        yield Ok(f"ServerBlueprint:fetch_apstra() {self.blueprint=}")
        self.ck_bp = CkApstraBlueprint(apstra_session, self.blueprint)
        if self.ck_bp.id is None:
            yield Err(f"ServerBlueprint:fetch_apstra() Error: BP {self.blueprint=} - id not found")
        for server_label, generic_system in self.servers.items():
            for res in generic_system.fetch_apstra(self.ck_bp):
                yield res


    def diff(self): 
        """
        Diff the loaded data with the apstra controller.
        """
        for server_label, generic_system in self.servers.items():
            diff_result = generic_system.diff()
            if isinstance(diff_result, Err):
                return Err(f"ServerBlueprint:diff(), {self.blueprint=}, {server_label=}, Error: {diff_result.err_value}")
            logging.warning(f"ServerBlueprint:diff(), {self.blueprint=}, {server_label=}, {diff_result.ok_value=}")


    def add_generic_systems(self):
        """
        Add the generic system to the apstra server.
        """
        for generic_system in self.servers.values():
            for res in generic_system.create():
                yield res

    def form_lacp(self):
        """
        Form the LACP for the generic system
        """
        for generic_system in self.servers.values():
            for res in generic_system.form_lacp():
                yield res
    
    def rename_interfaces(self):
        """
        Rename the interfaces for the generic system
        """
        for generic_system in self.servers.values():
            for res in generic_system.rename_interfaces():
                yield res

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


def add_generic_systems(apstra_session: CkApstraSession, generic_system_rows: list) -> Result[str, str]:
    """
    Add generic systems to the apstra server.

    Parameters
    ----------
    apstra_session : CkApstraSession
        The apstra session object.

    generic_system_rows : list
        The each list represents a link in the generic system. They keys are GsCsvKeys.

    """
    func_name = "add_generic_systems"

    # build data classes for the server blueprints, the generic systems and the links
    for row in generic_system_rows:
        bp = ServerBlueprint(row)
    yield Ok(f"{func_name} {ServerBlueprint._bps=}")

    # fetch the blueprints from the apstra server and store them in the data classes
    for bp_label, sbp in ServerBlueprint._bps.items():
        # yield Ok(f"{func_name} fetching {bp_label=} {sbp=}")
        for res in sbp.fetch_apstra(apstra_session):
            yield res
    yield Ok(f"{func_name} fetched {ServerBlueprint._bps=}")

    # create the generic systems and the links
    for bp_label, sbp in ServerBlueprint._bps.items():
        # yield Ok(f"{func_name} fetching {bp_label=} {sbp=}")
        for res in sbp.add_generic_systems():
            yield res
    yield Ok(f"{func_name} generic_systems added {ServerBlueprint._bps=}")

    # AGAIN, fetch the blueprints from the apstra server and store them in the data classes
    for bp_label, sbp in ServerBlueprint._bps.items():
        for res in sbp.fetch_apstra(apstra_session):
            yield res
    yield Ok(f"{func_name} after generic system creation - fetched {ServerBlueprint._bps=}")

    # form LACP for the generic systems
    for bp_label, sbp in ServerBlueprint._bps.items():
        for res in sbp.form_lacp():
            yield res
    yield Ok(f"{func_name} lacp formed {ServerBlueprint._bps=}")

    # fix the server interface names
    for bp_label, sbp in ServerBlueprint._bps.items():
        for res in sbp.rename_interfaces():
            yield res
    yield Ok(f"{func_name} interfaces renamed {ServerBlueprint._bps=}")


        # yield Ok(f"{func_name} Reading {bp.blueprint=}")
    # yield Ok(f"{func_name} {ServerBlueprint._bps=}")
    # for bp_label, sbp in ServerBlueprint._bps:
    #     yield Ok(f"{func_name} Reading {bp_label=}")

    # sorted_generic_systems = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    # no_ae_count = 0  # increment for each ae links

    # for item in generic_system_rows:
    #     blueprint = item['blueprint']
    #     server = item['server']
    #     no_ae_count += 1
    #     ae = item['ae'] or f'no_ae_{no_ae_count}'  # Use 'no_ae' if ae is empty

    #     # Server attributes
    #     server_attrs = {
    #         'ext': item['ext'],
    #         'tags_server': item['tags_server']
    #     }

    #     # AE attributes
    #     ae_attrs = {
    #         'lag_mode': item['lag_mode'],
    #         'ct_names': item['ct_names'],
    #         'tags_ae': item['tags_ae'],
    #     }

    #     # Link attributes
    #     link_attrs = {
    #         'speed': item['speed'],
    #         'ifname': item['ifname'],
    #         'switch': item['switch'],
    #         'switch_ifname': item['switch_ifname'],
    #         'tags_link': item['tags_link'],
    #         'comment': item['comment']
    #     }

    #     # Update the sorted data structure            
    #     if server not in sorted_generic_systems[blueprint]:
    #         sorted_generic_systems[blueprint][server] = server_attrs
    #         sorted_generic_systems[blueprint][server]['ae'] = defaultdict(list)

    #     if ae not in sorted_generic_systems[blueprint][server]['ae']:
    #         sorted_generic_systems[blueprint][server]['ae'][ae] = ae_attrs
    #         sorted_generic_systems[blueprint][server]['ae'][ae]['links'] = []

    #     sorted_generic_systems[blueprint][server]['ae'][ae]['links'].append(link_attrs)

    # yield Ok(f"{func_name} Adding {sorted_generic_systems=}")
    # bp_total = len(sorted_generic_systems.keys())
    # bp_count = 0
    # for bp_label, generic_systems in sorted_generic_systems.items():
    #     bp = CkApstraBlueprint(apstra_session, bp_label)
    #     bp_count += 1
    #     gs_total = len(generic_systems.keys())
    #     gs_count = 0
    #     yield Ok(f"{func_name} Adding {gs_total} generic systems to blueprint {bp_label} ({bp_count} of {bp_total})")
    #     for gs_label, gs_data in generic_systems.items():
    #         gs_count += 1
    #         gs_ae_total = len(gs_data['ae'].keys())            
    #         yield Ok(f"{func_name} Adding generic system {gs_label} ({gs_count} of {gs_total}) with {gs_ae_total} AE(s)")
    #         for res in add_single_generic_system(bp, gs_data):
    #             yield res
    #         # if isinstance(add_single_gs_result, Err):
    #         #     logging.warning(f"{func_name} Error for {gs_label=}:\n\tFrom add_single_generic_system: {add_single_gs_result.err_value}")
    #         #     # return None, f"{func_name} {error}"

    #     # ## form LACP in the BP iterating over the generic systems
    #     # for gs_label, gs_links_list in bp_data.items():
    #     #     form_lacp(bp, gs_label, gs_links_list)
    #     #     add_tags_result = add_tags(bp, gs_label, gs_links_list)
    #     #     if isinstance(add_tags_result, Err):
    #     #         logging.warning(f"{func_name} Error for {gs_label=}:\n\tFrom add_tags: {add_tags_result.err_value}")
    #     #         # return None, f"add_generic_system {error}"
    #     #         continue
    #     #     rename_generic_system_intf(bp, gs_label, gs_links_list)

    #     #     # # update connectivity templates - this should be run after lag update
    #     #     # assign_connectivity_templates(job_env, gs_label, gs_links_list)
    #     #     assign_connectivity_templates(bp, gs_label, gs_links_list)

    # return Ok(f"{func_name} {bp_total} blueprints done")


if __name__ == "__main__":
    apstra_server_host = '10.85.192.45'
    apstra_server_port = '443'
    apstra_server_username = 'admin'
    apstra_server_password = 'admin'

    apstra = CkApstraSession(apstra_server_host, apstra_server_port, apstra_server_username, apstra_server_password)
    apstra.print_token()

    the_columns = None
    df = pd.read_csv('./tests/fixtures/sample_generic_system.csv').replace(np.nan, None)
    columns =  [{"name": col, "label": col, "field": col} for col in df.columns]
    logging.warning(f"{columns=}")
    the_rows=[{col: row[col] for col in df.columns} for _, row in df.iterrows()]
    logging.warning(f"{the_rows=}")

    for row in the_rows:
        print(f"{row=}")
        bp = ServerBlueprint(row)
        # logging.warning(f"{bp=}")
        bp.fetch_apstra(apstra)
        pprint.pprint(bp)

    for bp_label, server_bp in ServerBlueprint.iterate_server_blueprints():
        server_bp.diff()

    # for bp_label, server_bp in ServerBlueprint.iterate_server_blueprints():
    #     bp = CkApstraBlueprint(apstra, bp_label)
    #     bp.fetch_blueprint()
    #     # for gs_label, gs_data in bp.iterate_generic_systems():
    #     #     add_generic_system(bp, gs_data)

 