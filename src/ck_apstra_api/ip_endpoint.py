
import click
import logging
import ipaddress

from ck_apstra_api.cli import CkJobEnv




class EndpointWithVnId:
    """
    """
    # endpoint_id
    # vn_id

    def __init__(self, endpoint_id: str, vn_id: str):
        self.endpoint_id = endpoint_id
        self.vn_id = vn_id

    def __repr__(self):
        return f"{self.endpoint_id=} {self.vn_id=}"


class PrefixListMember:
    """
    A class to hold the prefix with vn_id
    """
    # prefix
    # vn_id

    def __init__(self, prefix: str, vn_id: str):
        self.prefix = prefix
        self.vn_id = vn_id
    
    def get_address(self):
        return self.prefix.split('/')[0]

    def __repr__(self):
        return f"{self.prefix=} {self.vn_id=}"


class NamedPrefixList:
    """
    A class to hold the named prefix list
    """
    # name
    # members{ ipv4_addr: PrefixListMember  }

    def __init__(self, name: str, ipv4_addr: str, vn_id: str):
        self.name = name
        self.members = {}
        self.add(ipv4_addr, vn_id)

    def add(self, ipv4_addr: str, vn_id: bool):
        self.members[ipv4_addr] = PrefixListMember(ipv4_addr, vn_id)

    def iteritems(self):
        for ipv4_addr, prefix_list_member in self.members.items():
            yield ipv4_addr, prefix_list_member


class PrefixListCollection:
    """
    A class to translate and hold the prefix list data from the network deivce    
    """
    # named_prefix_lists = {}  # { name: NamedPrefixList, ...}
    # vn_nodes = []  # to identify internal ip addresses
    #    ip_network_obj has the ipaddress.ip_network object
    # logger

    def __init__(self, main_bp):
        VN_NODE_NAME = 'vn'
        self.named_prefix_lists = {}
        self.logger = logging.getLogger('PrefixListCollection')
        # pull the vn nodes with the ipv4_subnet
        self.vn_nodes = [x[VN_NODE_NAME] for x in main_bp.query(f"node('virtual_network',name='{VN_NODE_NAME}')") if x[VN_NODE_NAME]['ipv4_subnet'] is not None]
        for vn_node in self.vn_nodes:
            vn_node['ip_network_obj'] = ipaddress.ip_network(vn_node['ipv4_subnet'])
        self.logger.info(f"There are {len(self.vn_nodes)} vn nodes")

    def add(self, prefix_list_name: str, ipv4_addr: str):
        """
        Add a prefix list item into a named prefix list
        """
        vn_id = None
        this_ip_network = ipaddress.ip_network(ipv4_addr)
        for vn_node in self.vn_nodes:
            if this_ip_network.subnet_of(vn_node.get('ip_network_obj')):
                vn_id = vn_node['id']
                self.logger.warning(f"{ipv4_addr=} is internal")
                break
        # update existing named prefix list
        if prefix_list_name in self.named_prefix_lists:
            self.named_prefix_lists[prefix_list_name].add(ipv4_addr, vn_id)
        # create a new named prefix list
        else:
            self.named_prefix_lists[prefix_list_name] = NamedPrefixList(prefix_list_name, ipv4_addr, vn_id)
    
    def iteritems(self):
        for name, named_prefix_list in self.named_prefix_lists.items():
            yield name, named_prefix_list

    def read_from_set(self, set_file: str):
        """
        Read the prefix lists from a set file
        """

        PREFIX_LIST_PREFIX = 'set policy-options prefix-list '
        with open(set_file, 'r') as f:
            set_lines = f.readlines()
        for set_line in set_lines:
            if not set_line.startswith(PREFIX_LIST_PREFIX):
                continue
            prefix_list_line = set_line.split(PREFIX_LIST_PREFIX)[1].rstrip('\n')
            prefix_list_key_and_value = prefix_list_line.split(' ')
            if len(prefix_list_key_and_value) < 2:
                # no value - skip
                continue
            self.add(prefix_list_key_and_value[0], prefix_list_key_and_value[1])


def create_ip_endpoint(jobEnv: CkJobEnv, prefix_name: str, prefix_with_vnid: PrefixListMember) -> EndpointWithVnId:
    """
    Create an ip endpoint
     Return the tuple of (str: node_id, bool: vn_id)
    """
    # POST bp/external_endpoints?type=staging"
    post_external_endpoint_spec = {
        'enforcement_points': [],
        # 'label': 'GTCOLOB-1-of-3',
        # 'ipv4_addr': '10.237.80.0/24',
        'tags':  []
    }

    # POST bp/internal_endpoints"
    post_internal_endpoint_spec = {
        # 'vn_id': 'iTMWjf-Zdw-UqIe1B_E',
        # 'label': 'int-001',
        # 'ipv4_addr': '10.237.183.55/32',
        # 'tags':  []
    }

    post_spec = {

    }

    logging.debug(f"{prefix_with_vnid=}")

    ipv4_addr_ip_only = prefix_with_vnid.get_address()
    # trim the label to max 32 characters
    label_max_32 = f"{prefix_name[:32 - len(ipv4_addr_ip_only) -1]}-{ipv4_addr_ip_only}"
    post_url = None
    vn_id = prefix_with_vnid.vn_id

    if vn_id:
        # internal endpoint
        post_spec['vn_id'] = vn_id
        post_spec['label'] = label_max_32
        post_spec['ipv4_addr'] = prefix_with_vnid.prefix
        post_spec['tags'] = []
        post_url = 'internal_endpoints'
    else:
        post_spec['ipv4_addr'] = prefix_with_vnid.prefix
        post_spec['label'] = label_max_32
        post_spec['tags'] = [] 
        post_spec['enforcement_points'] = []
        post_url = 'external_endpoints'

    # post_external_endpoint_spec['ipv4_addr'] = ipv4_addr
    result = jobEnv.main_bp.post_item(post_url, post_spec=post_spec, params={'type': 'staging'})
    if result.status_code == 201:
        return EndpointWithVnId(result.json()['id'], vn_id)
    logging.warning(f"{result=} {result.text=} {prefix_with_vnid=} {post_spec=} {post_url=}")
    return None

def update_group(jobEnv: CkJobEnv, members: list, prefix_name: str, the_group_id: str):
    """
    Create or update a group
    members is a list of EndpointWithVnId
    """
    # POST bp/groups?type=staging"
    post_group_spec = {
        'enforcement_points': [],
        # 'group_type': 'external_endpoints',
        # 'members': [
        #     "OFH_zkZgoQyyQFvwtJk",
        #     "GmGRfL5aDkmRfjLkOF4",
        #     "3_w3RRJjWU1qHtkWcvE"            
        # ],
        # 'label': 'GTCOLOB'
    }

    # # POST bp/groups?type=staging"
    # post_group_spec = {
    #     # 'enforcement_points': [],
    #     # 'group_type': 'internal_endpoints',
    #     # 'members': [
    #     #     "PpCQ_-HHQMDnvSTUKKk",
    #     # ],
    #     # 'label': 'int-001'
    # }

    # put bp/groups/DrbLn5LDECRg4t1nxww"
    put_group_spec = {
        'enforcement_points': [],
        # 'group_type': 'external_endpoints',
        # 'members': [
        #     "PpCQ_-HHQMDnvSTUKKk",
        # ],
        # 'label': 'int-001'
        'tags':  []
        # 'id': 'DrbLn5LDECRg4t1nxww'
    }

    logging.debug(f"{members=} {prefix_name=} {the_group_id=}")
    vn_id = None
    for member in members:
        if type(member) != EndpointWithVnId:
            logging.warning(f"member is not EndpointWithVnId {member=}")
            continue
        vn_id = member.vn_id
    # TODO: update via put
    # TODO: VGA handling

    # TODO: check all members
    # if vn_id is not None, then the_group_type is internal_endpoints
    the_group_type = 'internal_endpoints' if vn_id is not None else 'external_endpoints'
    members_ids = [x.endpoint_id for x in members]

    # no group exists - doing post
    if the_group_id is None:
        post_group_spec['group_type'] = the_group_type
        post_group_spec['members'] = members_ids
        post_group_spec['label'] = prefix_name
        result = jobEnv.main_bp.post_item('groups', post_spec=post_group_spec, params={'type': 'staging'})
        if result.status_code != 201:
            logging.error(f"{result=} {result.text=} {post_group_spec=}, {members=}")
        return result
    put_group_spec['group_type'] = the_group_type
    put_group_spec['members'] = members_ids
    put_group_spec['label'] = prefix_name
    put_group_spec['id'] = the_group_id
    result = jobEnv.main_bp.put_item(f'groups/{the_group_id}', put_spec=put_group_spec, params={'type': 'staging'})
    if result.status_code != 201:
        logging.error(f"{result=} {result.text=} {put_group_spec=}")
    return result


def add_ip_endpoints(jobEnv: CkJobEnv, prefix_list_collection: PrefixListCollection):
    """
    Add the ip endpoints to the blueprint from the prefix list
    """
    main_bp = jobEnv.main_bp

    IP_ENDPOINT_NODE_NAME = 'ip_endpoint'
    GROUP_NODE_NAME = 'group'
    
    endpoint_query = f"""
        match(
            node('ip_endpoint', endpoint_type=is_in(['internal', 'external']),  name='{IP_ENDPOINT_NODE_NAME}'),
            optional(
                node(name='{IP_ENDPOINT_NODE_NAME}').out().node('group', name='{GROUP_NODE_NAME}')
            )
        )
    """

    ip_endpoint_nodes = main_bp.query(endpoint_query, multiline=True)
    ip_endpoint_nodes_no_group = [x for x in ip_endpoint_nodes if x[GROUP_NODE_NAME] is None]

    for prefix_name, named_prefix_list in prefix_list_collection.iteritems():
        logging.debug(f"{prefix_name=}, {named_prefix_list=}")
        the_member_ids_to_add = []  # list of EndpointWithVnId
        existing_member_ids = [] # list of EndpointWithVnId
        the_group_id = None

        # iterate named_prefix_list and compare with ipv4_in_bp
        for ipv4, prefix_list_member in named_prefix_list.iteritems():

            logging.debug(f"{prefix_name=} {ipv4} {type(prefix_list_member)=} {prefix_list_member=}")
            
            # see if the bp has the same ip_v4 under the same group. Then add the node id to the list of existing_member_ids
            the_endpoint_node_in_bp = [x[IP_ENDPOINT_NODE_NAME] for x in ip_endpoint_nodes if x[GROUP_NODE_NAME] is not None and x[GROUP_NODE_NAME]['label'] == prefix_name and x[IP_ENDPOINT_NODE_NAME]['ipv4_addr'] == ipv4]
            if len(the_endpoint_node_in_bp) > 0:
                existing_member_ids.append(EndpointWithVnId(the_endpoint_node_in_bp[0]['id'], prefix_list_member.vn_id))
                if the_group_id is None:                    
                    the_group_id = [x[GROUP_NODE_NAME]['id'] for x in ip_endpoint_nodes if x[GROUP_NODE_NAME] is not None and x[GROUP_NODE_NAME]['label'] == prefix_name][0]
                continue

            # the bp does not have the same ip_v4 under the same group. Then find the node id of not grouped ip_v4
            the_endpoint_node_in_bp = [x[IP_ENDPOINT_NODE_NAME] for x in ip_endpoint_nodes if x[GROUP_NODE_NAME] is None and x[IP_ENDPOINT_NODE_NAME]['ipv4_addr'] == ipv4]
            if len(the_endpoint_node_in_bp) > 0:
                the_member_ids_to_add.append(EndpointWithVnId(the_endpoint_node_in_bp[0]['id'], prefix_list_member.vn_id))
                continue

            # no ip_endpoint node for the ipv4_addr in the bp. Need to create it
            new_id = create_ip_endpoint(jobEnv, prefix_name, prefix_list_member)
            if new_id:
                the_member_ids_to_add.append(new_id)
            else:
                continue

        # if there is no member to add, all good. Continue to the next prefix
        # TODO: need to check if there is any member to delete
        if len(the_member_ids_to_add) == 0:
            continue

        updated_result = update_group(jobEnv, the_member_ids_to_add + existing_member_ids, prefix_name, the_group_id)
        if updated_result.status_code != 201:
            logging.error(f"{updated_result=} {updated_result.text=} {prefix_name=}")
        logging.debug(f"{prefix_name=} Created")

@click.command(name='add-ip-endpoints')
@click.option('--set-file', required=True, help='The name of the junos configuration in set format')
def click_add_ip_endpoints(set_file: str):
    job_env = CkJobEnv()
    prefix_list_collection = PrefixListCollection(job_env.main_bp)
    prefix_list_collection.read_from_set(set_file)
    add_ip_endpoints(job_env, prefix_list_collection)

