
import click
import logging

from ck_apstra_api.cli import CkJobEnv



class PrefixList:
    # name
    # ipv4_addr[]

    def __init__(self, name: str, ipv4_addr: str):
        self.name = name
        self.ipv4_addr = [ipv4_addr]

    def add(self, ipv4_addr: str):
        self.ipv4_addr.append(ipv4_addr)


class PrefixListCollection:
    """
    A class to hold the prefix list data
    """
    # prefix_list_dict = {}  # { name: PrefixListData, ...}
    # name
    # logger

    def __init__(self):
        self.prefix_list_dict = {}
        self.logger = logging.getLogger(__name__)

    def __init__(self):
        self.prefix_list_dict = {}

    def add(self, prefix_list_name: str, ipv4_addr: str):
        """
        Add a prefix list
        """
        if prefix_list_name in self.prefix_list_dict:
            self.prefix_list_dict[prefix_list_name].add(ipv4_addr)
        else:
            self.prefix_list_dict[prefix_list_name] = PrefixList(prefix_list_name, ipv4_addr)
    
    def iteritems(self):
        for name, value in self.prefix_list_dict.items():
            yield name, value.ipv4_addr




def read_prefix_lists_from_set(jobEnv: CkJobEnv, set_file: str):
    """
    Read the prefix lists from a set file
    """
    plc = PrefixListCollection()

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
        plc.add(prefix_list_key_and_value[0], prefix_list_key_and_value[1])
    return plc


def create_ip_endpoint(jobEnv: CkJobEnv, ipv4_addr: str, prefix: str) -> str:
    """
    Create an ip endpoint and return the node id
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
        # 'vn_id': ['iTMWjf-Zdw-UqIe1B_E'],
        # 'label': 'int-001',
        # 'ipv4_addr': '10.237.183.55/32',
        # 'tags':  []
    }
    ipv4_addr_ip_only = ipv4_addr.split('/')[0]
    post_external_endpoint_spec['ipv4_addr'] = ipv4_addr
    # trim the label to max 32 characters
    label_max_32 = f"{prefix[:32 - len(ipv4_addr_ip_only) -1]}-{ipv4_addr_ip_only}"
    post_external_endpoint_spec['label'] = label_max_32
    result = jobEnv.main_bp.post_item('external_endpoints', post_spec=post_external_endpoint_spec, params={'type': 'staging'})
    if result.status_code == 201:
        return result.json()['id']
    logging.debug(f"{result=} {result.text=}")
    return

def update_group(jobEnv: CkJobEnv, group_type: str, members: list, label: str, the_group_id: str = None):
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

    # no group exists
    if the_group_id is None:
        post_group_spec['group_type'] = group_type
        post_group_spec['members'] = members
        post_group_spec['label'] = label
        result = jobEnv.main_bp.post_item('groups', post_spec=post_group_spec, params={'type': 'staging'})
        if result.status_code != 201:
            logging.error(f"{result=} {result.text=}}")
        return result
    put_group_spec['group_type'] = group_type
    put_group_spec['members'] = members
    put_group_spec['label'] = label
    put_group_spec['id'] = the_group_id
    result = jobEnv.main_bp.put_item(f'groups/{the_group_id}', put_spec=put_group_spec, params={'type': 'staging'})
    return result


def add_ip_endpoints(jobEnv: CkJobEnv, plc: PrefixList):
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
    logging.debug(f"{ip_endpoint_nodes=}")
    ip_endpoint_nodes_no_group = [x for x in ip_endpoint_nodes if x[GROUP_NODE_NAME] is None]
    # if len(ip_endpoint_nodes) == 0:
    #     logging.error('No ip_endpoint nodes found')
    #     return

    # for item in ip_endpoint_nodes:
    #     group_name = item[GROUP_NODE_NAME]['label'] if item[GROUP_NODE_NAME] is not None else None
    #     logging.debug(f"{group_name=}, {item[IP_ENDPOINT_NODE_NAME]['ipv4_addr']=}, {item[IP_ENDPOINT_NODE_NAME]['endpoint_type']=}, {item[IP_ENDPOINT_NODE_NAME]['label']=}")
    for prefix_name, ipv4_in_set in plc.iteritems():
        logging.debug(f"{prefix_name=}, {ipv4_in_set=}")
        # ipv4_in_bp = [x[IP_ENDPOINT_NODE_NAME]['ipv4_addr'] for x in ip_endpoint_nodes if x[GROUP_NODE_NAME] is not None and x[GROUP_NODE_NAME]['label'] == prefix_name]
        # logging.debug(f"{ipv4_in_bp=}, {ipv4_in_set=}")
        # if ipv4_in_bp == ipv4_in_set:
        #     logging.debug(f"{prefix_name}= has the same prefix list")
        #     continue
        the_member_ids_to_add = []
        existing_member_ids = [] 
        the_group_id = None

        # iterate ipv4_in_set and compare with ipv4_in_bp
        for ipv4 in ipv4_in_set:

            logging.debug(f"{prefix_name=} {ipv4}")
            
            # see if the bp has the same ip_v4 under the same group. Then add the node id to the list of existing_member_ids
            the_node_in_bp = [x[IP_ENDPOINT_NODE_NAME] for x in ip_endpoint_nodes if x[GROUP_NODE_NAME] is not None and x[GROUP_NODE_NAME]['label'] == prefix_name and x[IP_ENDPOINT_NODE_NAME]['ipv4_addr'] == ipv4]
            if len(the_node_in_bp) > 0:
                existing_member_ids.append(the_node_in_bp[0]['id'])
                if the_group_id is None:                    
                    the_group_id = [x[GROUP_NODE_NAME]['id'] for x in ip_endpoint_nodes if x[GROUP_NODE_NAME] is not None and x[GROUP_NODE_NAME]['label'] == prefix_name][0]
                continue

            # the bp does not have the same ip_v4 under the same group. Then find the node id of not grouped ip_v4
            the_node_in_bp = [x[IP_ENDPOINT_NODE_NAME] for x in ip_endpoint_nodes if x[GROUP_NODE_NAME] is None and x[IP_ENDPOINT_NODE_NAME]['ipv4_addr'] == ipv4]
            if len(the_node_in_bp) > 0:
                the_member_ids_to_add.append(the_node_in_bp[0]['id'])
                continue

            # no ip_endpoint node for the ipv4_addr in the bp. Need to create it
            new_id = create_ip_endpoint(jobEnv, ipv4, prefix_name)
            if new_id:
                the_member_ids_to_add.append(new_id)
            else:
                continue

        # if there is no member to add, all good. Continue to the next prefix
        # TODO: need to check if there is any member to delete
        if len(the_member_ids_to_add) == 0:
            continue

        updated_result = update_group(jobEnv, 'external_endpoints', the_member_ids_to_add + existing_member_ids, prefix_name, the_group_id)
        logging.debug(f"{updated_result=}")


@click.command(name='add-ip-endpoints')
@click.option('--set-file', required=True, help='The name of the junos configuration in set format')
def click_add_ip_endpoints(set_file: str):
    job_env = CkJobEnv()
    plc = read_prefix_lists_from_set(job_env, set_file)
    # logging.info(f'{ip_endpoints=}')
    add_ip_endpoints(job_env, plc)

