import click
import yaml

from . import cliVar, prep_logging

@click.command()
@click.option('--bp-name', type=str, envvar='BP_NAME', help='Blueprint name')
@click.pass_context
def export_dci(ctx, bp_name: str):
    """
    Export the DCI information

    \b
    The headers:
    """
    logger = prep_logging('DEBUG', 'export_iplink()')

    TOP_LEVEL = 'evpn_interconnect_groups'
    ROUTING_ZONES = 'interconnect_security_zones'
    VIRTUAL_NETWORKS = 'interconnect_virtual_networks'


    bp = cliVar.get_blueprint(bp_name, logger)
    if not bp:
        return

    # retrieve top level variables
    dci_data_in = bp.get_item(TOP_LEVEL)[TOP_LEVEL][0]
    dci_data = { k: v for k, v in dci_data_in.items() if k != 'id' and not isinstance(v, dict)  }
    dci_data['remote_gateway_node_ids'] = [ x['gw_name'] for _, x in dci_data_in['remote_gateway_node_ids'].items() ]

    # retrieve routing zones
    dci_data[ROUTING_ZONES] = { v1['vrf_name']: 
                               { k2: v2 for k2, v2 in v1.items() if k2 in ['routing_policy_label', 'interconnect_route_target', 'enabled_for_l3'] } 
                               for k1, v1 in dci_data_in[ROUTING_ZONES].items()}

    # retrieve virtual networks
    dci_data[VIRTUAL_NETWORKS] = { v1['label']: 
                               { k2: v2 for k2, v2 in v1.items() if k2 in ['translation_vni', 'vrf_name', 'vni', 'l2', 'l3'] } 
                               for k1, v1 in dci_data_in[VIRTUAL_NETWORKS].items()}

    cliVar.export_data['blueprint'][bp_name]['dci'] = dci_data

    print(yaml.dump(cliVar.export_data))
