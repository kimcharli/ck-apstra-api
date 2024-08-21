
from dataclasses import dataclass, fields, field
import time
from typing import Generator, List, Optional, Any, TypeVar, Annotated, Dict, ClassVar
from collections import Counter, defaultdict
from enum import Enum, StrEnum, auto

from result import Result, Ok, Err

from ck_apstra_api import CkApstraSession, CkApstraBlueprint, CkEnum


class GsCsvKeys(StrEnum):
    """The Keys for the Generic System CSV file"""
    LINE = auto()
    """The line number for each entries in CSV file. This value can be used to create dummpy names for other members"""
    BLUEPRINT = auto()
    SERVER = auto()
    EXT = auto()
    DEPLOY_MODE = auto()
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
    id: str = None
    nodes: List[Dict[str, Any]] = field(default_factory=list)  # store the node data of the switch
    interfaces: Optional[Dict[str, Any]] = field(default_factory=dict)  # store the interface data of the switch
    bp: CkApstraBlueprint = None
    log_prefix: str = None
    # class variable to store the switch data
    _switches: ClassVar[Dict[str, Any]] = {}  # Dict[switch name, LeafSwitch]
    last_error: str = None

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
        self.bp = bp
        
        switch_interfaces_nodes_result = self.bp.get_switch_interface_nodes(self.switch_label)
        if isinstance(switch_interfaces_nodes_result, Err):
            self.last_error = switch_interfaces_nodes_result.err_value
            return Err(f"LeafSwitch::__init__ {self.switch_label=} not found in blueprint {self.bp.label}")
        self.nodes = switch_interfaces_nodes_result.ok_value
        # the leaf switch has existing interfaces
        if self.nodes:
            self.id = self.nodes[0][CkEnum.MEMBER_SWITCH]['id']
            self.interfaces = {x[CkEnum.MEMBER_INTERFACE]['if_name']: x[CkEnum.MEMBER_INTERFACE] for x in self.nodes}
        # the leaf switch is totally empty
        else:
            leaf_switch_query = f"node('system', name='system', label='{self.switch_label}', role='leaf')"
            switch_node_result = self.bp.query(leaf_switch_query)
            if isinstance(switch_node_result, Err):
                self.last_error = switch_node_result.err_value
                return Err(f"LeafSwitch::__init__ {self.switch_label=} not found in blueprint {self.bp.label}")
            self.interfaces = []
            self.id = switch_node_result.ok_value[0]['system']['id']
    
    # might not be needed
    def interface_id(self, if_name: str) -> str:
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
        self.ifname = self.ifname.strip()
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

        # get the tags for the link
        tags_result = self.bp.query(f"node(id='{self.fetched_link_id}').in_('tag').node('tag', name='tag')")
        if isinstance(tags_result, Err):
            yield Err(f"{log_prefix} Error: {tags_result.err_value}")
        else:
            self.fetched_tags_link = [tag['tag']['label'] for tag in tags_result.ok_value]
        yield Ok(f"{log_prefix} done {self}")

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

    def fix_tags(self):
        """
        Fix the tags for the link member
        """
        log_prefix = f"{self.log_prefix}::fix_tags()"
        tags_to_add = [x for x in self.tags_link if x not in self.fetched_tags_link]
        tags_to_remove = [x for x in self.fetched_tags_link if x not in self.tags_link]
        if len(tags_to_add) or len(tags_to_remove):
            patched = self.bp.post_tagging(self.fetched_link_id, tags_to_add, tags_to_remove)
        yield Ok(f"{log_prefix} done - tags {self.tags_link}: added {tags_to_add}, removed {tags_to_remove}")
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
    fetched_ae_id: Optional[str] = None  # The fetched ae_id from evpn-interface or the interface id of the member interface id in case of non-lag
    fetched_lag_mode: Optional[str] = None  # the fetched lag mode from the apstra controller
    fetched_ct_names: Optional[List[str]] = None # the fetched ct_names from the apstra controller
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
        if self.ct_names and isinstance(self.ct_names, str):
            self.ct_names = [x.strip() for x in self.ct_names.split(',')]
        elif not self.ct_names:
            self.ct_names = []
        self.fetched_ct_names = []
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
                if not self.lag_mode:
                    # non lag interface gets ct point to the member
                    self.fetched_ae_id = member.fetched_switch_intf_id
                if member.fetched_ae_interface:
                    self.ae = member.fetched_ae_interface['if_name']
                    self.fetched_lag_mode = member.fetched_ae_interface['lag_mode']

        if self.fetched_ae_id:
            # get any CT attached to the ae_id and update the fetched_ct_names
            ct_query = f"""
                match(
                    node('ep_endpoint_policy', policy_type_name='batch', name='CT_NODE')
                        .in_().node('ep_application_instance', name='EPAE_NODE')
                        .out('ep_affected_by').node('ep_group')
                        .in_('ep_member_of').node('interface', name='INTERFACE_NODE', id='{self.fetched_ae_id}')
                ).distinct(['CT_NODE'])
                """
            ct_result = self.bp.query(ct_query)
            if isinstance(ct_result, Err):              
                yield Err(f"{log_prefix} Error: {ct_result.err_value}")
            self.fetched_ct_names = [x['CT_NODE']['label'] for x in ct_result.ok_value]
        yield Ok(f"{log_prefix} done {self}")
        
    def form_lacp(self):
        """
        Form the LACP for the link group
        """
        log_prefix = f"{self.log_prefix}::form_lacp()"

        if not self.lag_mode:
            # None or ''
            yield Ok(f"{log_prefix} not for lag. Skipping")
            return
        
        if self.fetched_ae_id:
            yield Ok(f"{log_prefix} already lag {self.fetched_ae_id}. Skipping")
            return

        lag_spec = {
            'links': {x.fetched_link_id: {'group_label': self.ae, 'lag_mode': self.lag_mode} for x in self.members}
        }
        if len(lag_spec['links']) == 0:
            yield Err(f"{log_prefix} has no live links. Skipping {lag_spec=}")
            return
        # update LACP
        lag_updated = self.bp.patch_leaf_server_link_labels(lag_spec)
        if lag_updated:
            # It is expected to be None
            yield Err(f"Unexpected return: LACP updated {self.lag_mode=} in blueprint {self.bp.label}: {lag_updated}")
        else:
            yield Ok(f"{log_prefix} done")

    @property
    def link_spec(self) -> List[Dict[str, Any]]:
        """
        Return the link spec for the link group gathered from the links
        """
        data = []
        for member in self.members:
            data.append(member.link_spec)
        return data
    
    @property
    def speed_count(self) -> List[str]:
        return [x.speed for x in self.members]

    def rename_interfaces(self) -> Generator[Result[str, str], Any, Any]:
        log_prefix = f"{self.log_prefix}::rename_interfaces()"
        rename_spec = {'links': [member.rename_spec for member in self.members if member.rename_spec]}
        if rename_spec['links']:
            yield Ok(f"{log_prefix} about to rename: {self.ae=} {rename_spec=}")
            rename_updated = self.bp.patch_cable_map(rename_spec)
            if isinstance(rename_updated, Err):
                yield Err(f"{log_prefix} Error for {self.ae} in blueprint {self.bp.label}: {rename_updated.err_value}")
            else:
                yield Ok(f"{log_prefix} {self.ae=} rename done")

    def _get_ct_ids(self, vn_name_list: list) -> Generator[Result, Any, Any]:
        """
        Get the CT ids for the given CT names
        """
        log_prefix = f"{self.log_prefix}::_get_ct_ids()"
        ct_ids = []
        for vn_name in vn_name_list:
            if vn_name.lower() == 'na':
                continue
            ct_id = self.bp.get_ct_ids(vn_name)
            if ct_id:
                ct_ids.append(ct_id[0])
            else:
                yield Err(f"{log_prefix} CT '{vn_name}' not found in blueprint {self.bp.label}")
        yield Ok(ct_ids)

    def remove_vlans(self) -> Generator[Result[dict, str], Any, Any]:
        """
        Remove the vlans from the link group if they exists while they are not in the request information
        """
        log_prefix = f"{self.log_prefix}::remove_vlans()"
        vlans_to_remove = [x for x in self.fetched_ct_names if x not in self.ct_names]
        yield Ok(f"{log_prefix} {self.ae=} {vlans_to_remove=}")
        if len(vlans_to_remove):
            yield {
                'id': self.fetched_ae_id,
                'policies': [{'policy': self.bp.get_ct_ids(x)[0], 'used': False} for x in vlans_to_remove]
            }

    def add_vlans(self) -> Generator[Result[dict, str], Any, Any]:
        """
        Add the vlans to the link group
        """
        log_prefix = f"{self.log_prefix}::add_vlans()"
        vlans_to_add = [x for x in self.ct_names if x not in self.fetched_ct_names]
        yield Ok(f"{log_prefix} {self.ae=} {vlans_to_add=}")
        ct_ids_to_add = []
        for res in self._get_ct_ids(vlans_to_add):
            if isinstance(res, Err):
                yield res
            elif len(res.ok_value):
                ct_ids_to_add.extend(res.ok_value)
                yield Ok(f"{log_prefix} {ct_ids_to_add=}")
        if ct_ids_to_add:
            yield {
                'id': self.fetched_ae_id,
                'policies': [{'policy': x, 'used': True} for x in ct_ids_to_add]
            }
    
    def fix_tags(self):
        """
        Fix the tags for the link group, and the link

        Nothing in the link group to fix. Only the links
        """        
        for member in self.members:
            for res in member.fix_tags():
                yield res

@dataclass
class GenericSystem(DataInit):
    """
    Data class for a generic system.
    """
    server: str
    ext: Optional[bool]  # TBD: the external flag for the generic system
    deploy_mode: Optional[str] # the deploy flag for the generic system
    tags_server: Optional[List[str]]
    # child
    link_groups: Optional[List[LinkGroup]] = field(default=None, repr=False)  # optional only during initial creation
    # fetched
    gs_id: Optional[str] = None # generic system node id to be fetched from the blueprint
    fetched_server_tags: Optional[List[str]] = None  # the fetched tags from the apstra controller
    fetched_external_flag: Optional[bool] = None  # the fetched external flag from the apstra controller
    fetched_deploy_mode: Optional[bool] = None  # the fetched deploy flag from the apstra controller
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
        self.ext = True if self.ext == 'True' else False
        # it may have training space 
        if self.deploy_mode:
            self.deploy_mode = self.deploy_mode.strip().lower()
        # it should be None if not present
        if not self.deploy_mode:
            self.deploy_mode = None
    
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
            self.fetched_external_flag = server_links[0][CkEnum.GENERIC_SYSTEM]['external']
            self.fetched_deploy_flag = server_links[0][CkEnum.GENERIC_SYSTEM]['deploy_mode']
            #
            tag_result = apstra_bp.query(f"node('system', name='system', label='{self.server}', role='generic').in_('tag').node('tag', name='system_tag')")
            if isinstance(tag_result, Err):
                yield Err(f"{log_prefix} Error: {tag_result.err_value}")
            tags = tag_result.ok_value
            self.fetched_server_tags = [tag['system_tag']['label'] for tag in tags]
        # pull tags of the server
        tags_result = apstra_bp.query(f"node(id='{self.gs_id}').in_('tag').node('tag', name='tag')")
        if isinstance(tags_result, Err):
            yield Err(f"{log_prefix} Error: {tags_result.err_value}")
        else:
             self.fetched_server_tags = [tag['tag']['label'] for tag in tags_result.ok_value]
             yield Ok(f"{log_prefix} {self.fetched_server_tags=}")

        yield f"{log_prefix} done {self}"

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
        time.sleep(1)
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

    def patch_vlans(self, vlan_spec: Dict) -> Generator[Result[str, str], Any, Any]:
        """
        Patch the vlans for the generic system
        """
        log_prefix = f"{self.log_prefix}::patch_vlans()"
        yield Ok(f"{log_prefix} {vlan_spec=}")
        if len(vlan_spec['application_points']):
            ct_assign_updated = self.bp.patch_obj_policy_batch_apply(vlan_spec, params={'async': 'full'})
            task_id = ct_assign_updated['task_id']
            # task may take time to complete
            for i in range(10):
                task_status = self.bp.get_item(f"tasks/{task_id}")
                match task_status['status']:
                    case 'succeeded':
                        yield Ok(f"{log_prefix} done - {len(vlan_spec['application_points'])} vlans. {ct_assign_updated=}")
                        return
                    case 'init':
                        yield Ok(f"{log_prefix} the task in init {task_id}")
                        time.sleep(1)
                        continue
                    case 'in_progress':
                        yield Ok(f"{log_prefix} the task in in_progress {task_id}")
                        time.sleep(1)
                        continue
                    case 'failed':
                        yield Err(f"{log_prefix} failed: {task_status['detailed_status']}")
                        return
                    case _:
                        yield Err(f"{log_prefix} some other {task_id} to complete. {task_status}")

    def add_vlans(self) -> Generator[Result[str, str], Any, Any]:
        """
        Remove then add the vlans to the generic system
        """
        remove_spec = {
            'application_points': []
        }
        for lg in self.link_groups:
            for x in lg.remove_vlans():
                if isinstance(x, dict):
                    remove_spec['application_points'].append(x)
                else:
                    yield x        
        for res in self.patch_vlans(remove_spec):
            yield res
        
        add_spec = {
            'application_points': []
        }
        for lg in self.link_groups:
            for x in lg.add_vlans():
                if isinstance(x, dict):
                    add_spec['application_points'].append(x)
                else:
                    yield x        
        for res in self.patch_vlans(add_spec):
            yield res
        

    def fix_tags(self) -> Generator[Result[str, str], Any, Any]:
        """
        Fix the tags for the generic system, link group, and the link, and update deploy_mode and external flag
        """
        log_prefix = f"{self.log_prefix}::fix_tags()"
        tags_to_add = [x for x in self.tags_server if x not in self.fetched_server_tags]
        tags_to_remove = [x for x in self.fetched_server_tags if x not in self.tags_server]
        if len(tags_to_add) or len(tags_to_remove):
            patched = self.bp.post_tagging(self.gs_id, tags_to_add, tags_to_remove)
        for lg in self.link_groups:
            for res in lg.fix_tags():
                yield res
        patch_spec = {}
        if self.deploy_mode != self.fetched_deploy_mode:
            patch_spec['deploy_mode'] = self.deploy_mode
        if self.ext != self.fetched_external_flag:
            patch_spec['external'] = self.ext
        if patch_spec:
            patched = self.bp.patch_item(f"nodes/{self.gs_id}", patch_spec)
            if patched.status_code == 202:
                yield Ok(f"{log_prefix} patched {patch_spec} result: {patched}")
            else:
                yield Err(f"{log_prefix} failed for {patch_spec} result: {patched.text}")




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

    def add_vlans(self):
        """
        Add the vlans to the generic system
        """
        for generic_system in self.servers.values():
            for res in generic_system.add_vlans():
                yield res

    def fix_tags(self):
        """
        Fix the tags for the generic system, link group, and the link
        """
        for generic_system in self.servers.values():
            for res in generic_system.fix_tags():
                yield res


def add_generic_systems(apstra_session: CkApstraSession, generic_system_rows: list) -> Generator[Result[str, str], Any, Any]:
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
        _ = ServerBlueprint(row)
    blueprints_string = f"blueprints {list(ServerBlueprint._bps.keys())}"
    yield Ok(f"{func_name} {blueprints_string}")

    # fetch the blueprints from the apstra server and store them in the data classes
    for bp_label, sbp in ServerBlueprint._bps.items():
        # yield Ok(f"{func_name} fetching {bp_label=} {sbp=}")
        for res in sbp.fetch_apstra(apstra_session):
            yield res
    yield Ok(f"{func_name} fetched {blueprints_string}")

    # create the generic systems and the links
    for bp_label, sbp in ServerBlueprint._bps.items():
        # yield Ok(f"{func_name} fetching {bp_label=} {sbp=}")
        for res in sbp.add_generic_systems():
            yield res
    yield Ok(f"{func_name} generic_systems added {blueprints_string}")

    # AGAIN, fetch the blueprints from the apstra server and store them in the data classes
    for bp_label, sbp in ServerBlueprint._bps.items():
        for res in sbp.fetch_apstra(apstra_session):
            yield res
    yield Ok(f"{func_name} after generic system creation - fetched {blueprints_string}")

    # form LACP for the generic systems
    for bp_label, sbp in ServerBlueprint._bps.items():
        for res in sbp.form_lacp():
            yield res
    yield Ok(f"{func_name} lacp formed {ServerBlueprint._bps=}")

    # AGAIN YET, fetch the blueprints from the apstra server and store them in the data classes
    for bp_label, sbp in ServerBlueprint._bps.items():
        for res in sbp.fetch_apstra(apstra_session):
            yield res
    yield Ok(f"{func_name} after form lag - fetched {ServerBlueprint._bps=}")

    # fix the server interface names
    for bp_label, sbp in ServerBlueprint._bps.items():
        for res in sbp.rename_interfaces():
            yield res
    yield Ok(f"{func_name} interfaces renamed for blueprints {blueprints_string}")

    # fix the connectivity templates
    for bp_label, sbp in ServerBlueprint._bps.items():
        for res in sbp.add_vlans():
            yield res
    yield Ok(f"{func_name} vlans added {ServerBlueprint._bps=}")

    # fix the tags
    for bp_label, sbp in ServerBlueprint._bps.items():
        for res in sbp.fix_tags():
            yield res
    yield Ok(f"{func_name} tags fixed {ServerBlueprint._bps=}")


def get_generic_systems(apstra_session: CkApstraSession, out_csv: str ) -> Generator[Result[str, str], Any, Any]:
    """
    Get the generic systems from the apstra server and write them to the csv file.

    Parameters
    ----------
    apstra_session : CkApstraSession
        The apstra session object.

    out_csv : str
        The output csv file path.

    """
    func_name = "get_generic_systems"

    yield Ok(f"{func_name} begin")
    yield Err(f"{func_name} not implemented")
    return

    # get the generic systems from the apstra server
    generic_systems = []
    for bp_label, sbp in ServerBlueprint._bps.items():
        for server_label, gs in sbp.interate_generic_systems():
            generic_systems.append(gs)
    yield Ok(f"{func_name} {len(generic_systems)} generic systems found {generic_systems=}")

    # fetch the generic systems from the apstra server
    for gs in generic_systems:
        for res in gs.fetch_apstra(apstra_session):
            yield res
    yield Ok(f"{func_name} fetched {generic_systems=}")

    # write the generic systems to the csv file
    with open(out_csv, 'w') as f:
        f.write(f"{','.join([x.name for x in fields(GenericSystem)])}\n")
        for gs in generic_systems:
            f.write(f"{','.join([str(getattr(gs, x.name)) for x in fields(GenericSystem)])}\n")
    yield Ok(f"{func_name} written to {out_csv=}")

    # return the generic systems
    yield Ok(f"{func_name} done {generic_systems=}")

