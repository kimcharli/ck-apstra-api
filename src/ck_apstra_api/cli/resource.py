
import click

from . import cliVar, prep_logging



def get_first_last_tuples(data: dict) -> list:
    """get the first and last tuples 'ranges'"""
    return [(x['first'], x['last']) for x in data['ranges']]


def get_subnets(data: dict) -> list:
    """get the network from a list of dicts 'subnets"""
    return [x['network'] for x in data['subnets']]

def get_devices(data: dict) -> list:
    """get the device ids from a list of dicts 'devices'"""
    return [x['id'] for x in data['devices']]

@click.command()
@click.option('--file-format', type=click.Choice(['yaml', 'json']), default='yaml', help='File format')
@click.option('--file-folder', type=str, default='.', help='File folder')
@click.pass_context
def export_resources(ctx, file_format: str, file_folder: str):
    """
    Export the Resources in yaml, json format

    """
    logger = prep_logging('DEBUG', 'export_resources()')

    resources = cliVar.data_in_file['resources'] = {}

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
        data = cliVar.session.get_items(f'resources/{pool}')['items']
        resources[pool] = {x['display_name']: func(x) for x in data}
        logger.debug(f"{resources[pool]=}")

    cliVar.export_file(file_folder, file_format)
    

