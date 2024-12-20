import os
from dataclasses import dataclass
import click

from . import cliVar, prep_logging

@click.command()
@click.option('--bp-name', type=str, envvar='BP_NAME', help='Blueprint name')
@click.option('--vn-csv', type=str, required=True, help='The CSV file path of virtual networks to import from')
@click.pass_context
def import_virtual_network(ctx, bp_name, vn_csv: str):
    """
    Import virtual networks from a CSV file
    """
    logger = prep_logging('DEBUG', 'import_virtual_network()')

    bp = cliVar.get_blueprint(bp_name, logger)
    if not bp:
        return
 
    logger.info(f"{bp_name=} {vn_csv=}")

    vn_csv_path = os.path.expanduser(vn_csv)

    # # get the list of dictionaries per each virtual network from the Apstra
    # vn_csv_string = bp.get_item('virtual-networks-csv-bulk')['csv_bulk']
    # csv_reader = csv.DictReader(io.StringIO(vn_csv_string))
    # current_vn_dict = [row for row in csv_reader]

    links_to_add = []
    with open(vn_csv_path, 'r') as csvfile:        
        # csv_reader = csv.reader(csvfile)
        # input_vn_dict = [row for row in csv_reader]

        # for row in csv_reader:
        #     links_to_add.append(dict(zip(headers, row)))
        csv_string = csvfile.read()
        imported = bp.patch_virtual_networks_csv_bulk(csv_string)
        logger.info(f"Virtual Networks of blueprint {bp_name} imported from {vn_csv_path}")


@click.command()
@click.option('--bp-name', type=str, envvar='BP_NAME', help='Blueprint name')
@click.option('--vn-csv', type=str, envvar='VN_CSV', help='The CSV file path of virtual networks to export to')
@click.pass_context
def export_virtual_network(ctx, bp_name, vn_csv: str):
    """
    Import virtual networks from a CSV file
    """
    logger = prep_logging('DEBUG', 'export_virtual_network()')

    bp = cliVar.get_blueprint(bp_name, logger)
    if not bp:
        return

    logger.info(f"{bp_name=} {vn_csv=}")

    vn_csv_path = os.path.expanduser(vn_csv or f"{bp_name}-vn.csv")
    csv_string = bp.get_item('virtual-networks-csv-bulk')['csv_bulk']
    with open(vn_csv_path, 'w') as csvfile:
        csvfile.write(csv_string)
    logger.info(f"Virtual Networks of blueprint {bp_name} exported to {vn_csv_path}")



@click.command()
@click.option('--virtual-network', type=str, required=True, help='Subject Virtual Network name')
@click.option('--routing-zone', type=str, required=True, help='Destination Routing Zone name')
@click.option('--blueprint', type=str, envvar='BP_NAME', help='Blueprint name')
@click.pass_context
def relocate_vn(ctx, blueprint: str, virtual_network: str, routing_zone: str):
    """
    Move a Virtual Network to the target Routing Zone

    The virtual network move involves deleting and recreating the virtual network in the target routing zone.
    To delete the virtual network, the associated CT should be taken care of. Either deassign and delete them and later do reverse.
    This CT handling trouble can be mitigated with a temporary VN to replace the original VN in the CT. Later, to be reversed later.

    """
    logger = prep_logging('INFO', 'relocate_vn()')
    logger.info(f"Took order {blueprint=} {virtual_network=} {routing_zone=}")

    NODE_NAME_RZ = 'rz'

    bp = cliVar.get_blueprint(bp_name, logger)
    if not bp:
        return

    @dataclass
    class Order(object):
        target_vn: str = virtual_network
        target_vn_id: str = None
        target_vn_spec: dict = None
        test_vn: str = None
        test_vn_id: str = None
        test_vn_spec: dict = None
        target_rz: str = routing_zone
        terget_rz_id: str = None

        def summary(self):
            return f"Order: {self.target_vn=} {self.target_vn_id=} {self.test_vn=} {self.test_vn_id=} {self.target_rz=} {self.terget_rz_id=}"
    the_order = Order()

    # get the target_rz_id
    found_rz = bp.query(f"node('security_zone', name='{NODE_NAME_RZ}', label='{routing_zone}')").ok_value
    the_order.terget_rz_id = found_rz[0][NODE_NAME_RZ]['id']

    # get all the VNs
    found_vns_dict = bp.get_item('virtual-networks')['virtual_networks']

    # pick the target VN data
    target_vn_node = [vn for vn in found_vns_dict.values() if vn['label'] == virtual_network]    
    if len(target_vn_node) == 0:
        logger.error(f"Virtual Network {virtual_network} not found")
        return
    the_order.target_vn_spec = target_vn_node[0]
    the_order.target_vn_id = the_order.target_vn_spec['id']
    # check if the VN is already in the target RZ
    if the_order.target_vn_spec['security_zone_id'] == the_order.terget_rz_id:
        logger.warning(f"Virtual Network {virtual_network} already in the target Routing Zone {routing_zone}")
        return

    for res in bp.get_temp_vn(the_order.target_vn):
        if isinstance(res, dict):
            the_order.test_vn_spec = res
            the_order.test_vn_id = res['id']
            the_order.test_vn = res['label']
        else:
            logger.info(res)

    logger.info(f"Ready to relocate vn {virtual_network}: {the_order.summary()}")

    # replace CTs with test VN
    for res in bp.swap_ct_vns(the_order.target_vn_id, the_order.test_vn_id):
        logger.info(res)

    # delete the original VN
    deleted = bp.delete_item(f"virtual-networks/{the_order.target_vn_id}")
    logger.info(f"VN {the_order.target_vn}:{the_order.target_vn_id} deleted: {deleted=}")

    # create the original VN in the target RZ
    the_order.target_vn_spec['security_zone_id'] = the_order.terget_rz_id
    created = bp.post_item('virtual-networks', the_order.target_vn_spec)
    the_order.target_vn_id = created.json()['id']
    logger.info(f"VN {the_order.target_vn}:{the_order.target_vn_id} created: {created=} under RZ:{the_order.target_rz}")

    # restore the CTs
    logger.info(f"Restoring CTs with new VN {the_order.test_vn}:{the_order.test_vn_id}")
    for res in bp.swap_ct_vns(the_order.test_vn_id, the_order.target_vn_id):
        logger.info(res)

    # remove the temporary VN
    deleted = bp.delete_item(f"virtual-networks/{the_order.test_vn_id}")
    logger.info(f"Temporary VN {the_order.test_vn}:{the_order.test_vn_id} deleted: {deleted=}")

    logger.info(f"Order completed: {the_order.summary()}")
    cliVar.session.logout()


@click.command()
@click.option('--virtual-network', type=str, required=True, help='Subject Virtual Network name')
@click.option('--routing-zone', type=str, required=True, help='Destination Routing Zone name')
@click.option('--blueprint', type=str, envvar='BP_NAME', help='Blueprint name')
@click.pass_context
def test_get_temp_vn(ctx, bp_name: str, virtual_network: str, routing_zone: str):
    """
    Test get_temp_vn
    """
    logger = prep_logging('INFO', 'test_get_temp_vn()')

    bp = cliVar.get_blueprint(bp_name, logger)
    if not bp:
        return

    for res in bp.get_temp_vn(virtual_network):
        if isinstance(res, dict):
            temp_vn = res
        else:
            logger.info(res)


@click.command()
@click.option('--virtual-network', type=str, default='ESX-Replication', help='Subject Virtual Network name')
@click.option('--bound-to', type=str, default='CHA08P25LP01', help='The leaf pair label to bound to')
@click.option('--blueprint', type=str, envvar='BP_NAME', help='Blueprint name')
@click.pass_context
def assign_vn_to_leaf(ctx, bp_name: str, virtual_network: str, bound_to: str):
    """
    Test to patch vn for the bound_to
    """
    logger = prep_logging('INFO', 'assign_vn_to_leaf()')

    bp = cliVar.get_blueprint(bp_name, logger)
    if not bp:
        return

    logger.info(f"Bound to {bp_name}:{virtual_network} to {bound_to}")

    vns = bp.query(f"node('virtual_network', label='{virtual_network}', name='vn')").ok_value
    logger.info(f"{vns=}")
    vn_id = vns[0]['vn']['id']
    vn_data = bp.get_item(f"virtual-networks/{vn_id}")
    if 'reserved_vlan_id' in vn_data and vn_data['reserved_vlan_id']:
        vlan_id = vn_data['reserved_vlan_id']
    else:
        vlan_id = vn_data['bound_to'][0]['vlan_id']

    logger.info(f"{vn_data=}")
    system = bp.query(f"node('redundancy_group', label='{bound_to}', name='system')").ok_value
    system_id = system[0]['system']['id']
    logger.info(f"{system=}")
    bound_to = [x for x in vn_data['bound_to'] if x['system_id'] == system_id]
    if len(bound_to) > 0:
        logger.info(f"Already bound to {bound_to}")
        return
    vn_patch_spec = {
        'bound_to': vn_data['bound_to']
    }
    vn_patch_spec['bound_to'].append({
        'system_id': system[0]['system']['id'],
        'vlan_id': vlan_id
    })  
    vn_patched = bp.patch_item(f"virtual-networks/{vn_id}", vn_patch_spec)
    logger.info(f"{vn_patched=} {vn_patched.text=}")

