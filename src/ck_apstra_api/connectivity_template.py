from dataclasses import dataclass, field, asdict
from enum import StrEnum
from functools import cache
from typing import Dict, Generator, List, Optional
import uuid

from result import Err, Ok, Result
from ck_apstra_api import CkApstraSession, CkApstraBlueprint


class CtCsvKeys(StrEnum):
    BLUEPRINT = 'blueprint'
    CT_LABEL = 'label'
    CT_DESCRIPTION = 'description'
    SECURITY_ZONE = 'security_zone'
    TAGGED = 'tagged'
    VLAN_ID = 'vlan_id'
    L3_MTU = 'l3_mtu'
    IPV4 = 'ipv4'    
    IPV6 = 'ipv6'


@dataclass
class ConnectivityTemplate:
    """
    The base of Connectivity Template
    """
    pass


@dataclass
class IpLinkAttributes:
    security_zone: str
    interface_type: str = 'tagged'
    vlan_id: int = 0
    l3_mtu: int = 9100
    ipv4_addressing_type: str = 'numbered'
    ipv6_addressing_type: str = 'none'

@dataclass
class PolicyIpLink:
    """
    The IP Link Policy Object
    """
    id: str
    attributes: IpLinkAttributes
    label: str = 'IP Link'
    description: str = "Build an IP link between a fabric node and a generic system. This primitive uses AOS resource pool \"Link IPs - To Generic\" by default to dynamically allocate an IP endpoint (/31) on each side of the link. To allocate different IP endpoints, navigate under Routing Zone>Subinterfaces Table. Can be assigned to physical interfaces or single-chassis LAGs (not applicable to ESI LAG or MLAG interfaces)."
    policy_type_name: str = 'AttachLogicalLink'
    visible: bool = False

    def __init__(self, 
                 security_zone: str, 
                 interface_type: str, 
                 vlan_id: int, 
                 l3_mtu: int, 
                 ipv4_addressing_type: str, 
                 ipv6_addressing_type: str):
        self.id = str(uuid.uuid4())
        self.attributes = IpLinkAttributes(security_zone, interface_type, vlan_id, l3_mtu, ipv4_addressing_type, ipv6_addressing_type)


@dataclass
class PipelineAttributes:
    first_subpolicy: str
    second_subpolicy: str = None

    def __init__(self, first_subpolicy):
        self.first_subpolicy = first_subpolicy.id
        self.second_subpolicy = None

@dataclass
class PolicyPipeline:
    """
    The Policy Pipeline Object
    """
    id: str
    label: str
    attributes: PipelineAttributes
    description: str
    policy_type_name: str = 'pipeline'
    visible: bool = False

    def __init__(self, ct_type: str, first_subpolicy):
        self.id = str(uuid.uuid4())
        self.label = f"{ct_type} (pipeline)"
        self.attributes = PipelineAttributes(first_subpolicy)
        self.description = first_subpolicy.description


@dataclass
class SubPolicies:
    subpolicies: List[str]

    def __init__(self, pipeline: PolicyPipeline):
        self.subpolicies = [pipeline.id]

@dataclass
class PolicyBatch:
    """
    The Policy Batch Connectivity Template
    """
    id: str
    label: str
    attributes: SubPolicies
    description: str = ''
    policy_type_name: str = 'batch'
    visible: bool = True
    user_data: dict = None
    tags: List[str] = field(default_factory=list)

    def __init__(self, 
                 label: str, 
                 pipeline: PolicyPipeline, 
                 target_policy, 
                 tags: List[str] = []):
        self.id = str(uuid.uuid4())
        self.label = label
        self.attributes = SubPolicies(pipeline)
        self.user_data = '{\"isSausage\":true,\"positions\":{\"' + target_policy.id + '\":[290,80,1]}}'
        self.tags = tags

    def __post_init__(self):
        self.policy_type_name = 'batch'
        self.visible = True
        self.user_data = self.user_data if self.user_data else {}
        self.tags = self.tags if self.tags else []  # default to empty list



@dataclass
class CtIpLink:
    """
    The IP Link Connectivity Template
    """
    policies: List[Dict]

    def __init__(self, 
                 label: str, 
                 security_zone: str, 
                 interface_type: str, 
                 vlan_id: int, 
                 l3_mtu: int, 
                 ipv4_addressing_type: str, 
                 ipv6_addressing_type: str):
        iplink = PolicyIpLink(security_zone, interface_type, vlan_id, l3_mtu, ipv4_addressing_type, ipv6_addressing_type)
        pipeline = PolicyPipeline('IP Link', iplink)
        batch = PolicyBatch(label, pipeline, iplink)
    
        self.policies = [iplink, pipeline, batch]

@cache
def get_security_zone_id(blueprint: CkApstraBlueprint, security_zone_name: str) -> str:
    """
    Get the Security Zone ID from the name
    """
    security_zones = blueprint.get_item('security-zones')['items']
    security_zone = [x['id'] for x in security_zones.values() if x['label'] == security_zone_name]
    if security_zone:
        return security_zone[0]
    return None



@cache
def get_blueprint(session: CkApstraSession, blueprint_name: str) -> CkApstraBlueprint:
    """
    Get the Blueprint
    """
    blueprint = CkApstraBlueprint(session, blueprint_name)
    return blueprint

def import_ip_link_ct(session: CkApstraSession, ct_data: List[dict]) -> Generator[Result, None, None]:
    """
    Import the IP Link Connectivity Template
    """
    log_prefix = 'import_ct_ip_link()'
    for ct in ct_data:
        # get blueprint
        blueprint = get_blueprint(session, ct[CtCsvKeys.BLUEPRINT])
        if blueprint is None:
            yield Err(f"{log_prefix} {ct[CtCsvKeys.BLUEPRINT]} not found")
            continue
        # see if the connectivity template already exists
        ct_name = ct[CtCsvKeys.CT_LABEL]
        ct_query_result = blueprint.query(f"node('ep_endpoint_policy', policy_type_name='batch', label='{ct_name}', name='batch')")
        if isinstance(ct_query_result, Err):
            yield ct_query_result.err_value
            continue
        if ct_query_result.ok_value:
            yield Err(f"{log_prefix} '{ct_name}' already exists. Skipping.")
            continue
        # get security zone id
        security_zone_id = get_security_zone_id(blueprint, ct[CtCsvKeys.SECURITY_ZONE])
        if security_zone_id is None:
            yield Err(f"{log_prefix} {ct[CtCsvKeys.SECURITY_ZONE]} not found")
            continue
        ct['security_zone'] = security_zone_id

        yield Ok(f"{log_prefix} Creating with: {ct}")
        ct_ip_link_spec = asdict(CtIpLink(ct[CtCsvKeys.CT_LABEL], security_zone_id, ct['interface_type'], int(ct[CtCsvKeys.VLAN_ID]), int(ct[CtCsvKeys.L3_MTU]), ct['ipv4_addressing_type'], ct['ipv6_addressing_type']))
        yield f"{log_prefix} {ct_ip_link_spec=}"
        result = blueprint.put_item("obj-policy-import", ct_ip_link_spec)
        if result.status_code != 204:
            yield Err(f"{log_prefix} {result.text=} {result.status_code=}")
        else:
            yield Ok(f"{log_prefix} {ct_name} created.")

