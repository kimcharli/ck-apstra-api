
import click
import logging

from ck_apstra_api.cli import CkJobEnv







def read_prefix_lists_from_set(jobEnv: CkJobEnv, set_file: str):
    """
    Read the prefix lists from a set file
    """
    PREFIX_LIST_PREFIX = 'set policy-options prefix-list '
    ip_endpoints = {
        # 'GTAOK': [
        # {  # label
        #     'endporint_type': None,  # internal, external (may have group - group_type external_endpoints ), vip (may have ep_endpoint_policy - static route)
        #     'ipv4_addr': "10.220.85.0/24",
        #     'id': "ShZdX8LLPnYYBDuH7f8",
        # },
        #]
    }
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
        the_key = prefix_list_key_and_value[0]
        the_value = prefix_list_key_and_value[1]
        # logging.debug(f'{the_key=}, {the_value=}')
        the_prefix_list = ip_endpoints.get(the_key, [])
        the_prefix_list.append({'ipv4_addr': prefix_list_key_and_value[1]})
        ip_endpoints[the_key] = the_prefix_list
        # logging.debug(f'{ip_endpoints[the_key]=}')
    return ip_endpoints


def add_ip_endpoints(jobEnv: CkJobEnv, ip_endpoints_input: dict):
    """
    Add the ip endpoints to the blueprint
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

    # POST bp/external_endpoints?type=staging"
    post_external_endpoint_spec = {
        # 'enforcement_points': [],
        # 'label': 'GTCOLOB-1-of-3',
        # 'ipv4_addr': '10.237.80.0/24',
        # 'tags':  []
    }

    # POST bp/internal_endpoints"
    post_internal_endpoint_spec = {
        # 'vn_id': ['iTMWjf-Zdw-UqIe1B_E'],
        # 'label': 'int-001',
        # 'ipv4_addr': '10.237.183.55/32',
        # 'tags':  []
    }


    # POST bp/groups?type=staging"
    post_group_spec = {
        # 'enforcement_points': [],
        # 'group_type': 'external_endpoints',
        # 'members': [
        #     "OFH_zkZgoQyyQFvwtJk",
        #     "GmGRfL5aDkmRfjLkOF4",
        #     "3_w3RRJjWU1qHtkWcvE"            
        # ],
        # 'label': 'GTCOLOB'
    }

    # POST bp/groups?type=staging"
    post_group_spec = {
        # 'enforcement_points': [],
        # 'group_type': 'internal_endpoints',
        # 'members': [
        #     "PpCQ_-HHQMDnvSTUKKk",
        # ],
        # 'label': 'int-001'
    }

    # put bp/groups/DrbLn5LDECRg4t1nxww"
    post_group_spec = {
        # 'enforcement_points': [],
        # 'group_type': 'external_endpoints',
        # 'members': [
        #     "PpCQ_-HHQMDnvSTUKKk",
        # ],
        # 'label': 'int-001'
        # 'tags':  []
        # 'id': 'DrbLn5LDECRg4t1nxww'
    }



    ip_endpoint_nodes = main_bp.query(endpoint_query)
    ip_endpoint_nodes_no_group = [x for x in ip_endpoint_nodes if x[GROUP_NODE_NAME] is None]
    # if len(ip_endpoint_nodes) == 0:
    #     logging.error('No ip_endpoint nodes found')
    #     return

    # for item in ip_endpoint_nodes:
    #     group_name = item[GROUP_NODE_NAME]['label'] if item[GROUP_NODE_NAME] is not None else None
    #     logging.debug(f"{group_name=}, {item[IP_ENDPOINT_NODE_NAME]['ipv4_addr']=}, {item[IP_ENDPOINT_NODE_NAME]['endpoint_type']=}, {item[IP_ENDPOINT_NODE_NAME]['label']=}")
    for input_label, input_list in ip_endpoints_input.items():
        logging.debug(f"{input_label=}, {input_list=}")
        ipv4_in_bp = [x[IP_ENDPOINT_NODE_NAME]['ipv4_addr'] for x in ip_endpoint_nodes if x[GROUP_NODE_NAME] is not None and x[GROUP_NODE_NAME]['label'] == input_label]
        ipv4_in_set = [x['ipv4_addr'] for x in input_list]
        logging.debug(f"{ipv4_in_bp=}, {ipv4_in_set=}")
        if ipv4_in_bp == ipv4_in_set:
            logging.debug(f"ip_endpoints {input_label} has the same prefix list")
            continue
        the_members_to_add = []

        # if there is no group in the blueprint, create it
        if len(ipv4_in_bp) == 0:
            # iterate ipv4_in_set and create the ip_endpoint nodes
            for ip_v4 in ipv4_in_set:
                # find the node id of the ip_endpoint node with the same ip_v4
                ipv4_node_ids = [x[IP_ENDPOINT_NODE_NAME]['id'] for x in ip_endpoint_nodes_no_group if x[IP_ENDPOINT_NODE_NAME]['ipv4_addr'] == ip_v4]
                if len(ipv4_node_ids) == 0:
                    logging.debug(f"{ip_v4} not found in the blueprint. Need to create it")
                    # TODO:
                    continue
            logging.debug(f"ip_endpoints {input_label} has different prefix list")
            # TODO:
            continue
        the_same_members = []
        the_members_to_add = []
        the_members_to_delete = [x[IP_ENDPOINT_NODE_NAME]['id'] for x in ip_endpoint_nodes if x[GROUP_NODE_NAME] is not None and x[GROUP_NODE_NAME]['label'] == input_label and x[IP_ENDPOINT_NODE_NAME]['ipv4_addr'] not in ipv4_in_set]
        return



@click.command(name='add-ip-endpoints')
@click.option('--set-file', required=True, help='The name of the junos configuration in set format')
def click_add_ip_endpoints(set_file: str):
    job_env = CkJobEnv()
    ip_endpoints = read_prefix_lists_from_set(job_env, set_file)
    # logging.info(f'{ip_endpoints=}')
    add_ip_endpoints(job_env, ip_endpoints)

