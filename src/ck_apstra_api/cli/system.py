from dataclasses import dataclass, fields, asdict
import os
import click
import csv
from result import Ok, Err

from ck_apstra_api import add_generic_systems, GsCsvKeys, get_generic_systems
from . import cliVar, prep_logging


@dataclass
class SystemsData:
    system: str
    asn: str
    lo0: str
    rack: str
    device_profile: str

    def __init__(self, system_input: dict):
        self.system = system_input['system']['label']
        self.asn = system_input['domain']['domain_id'] if system_input['domain'] else None
        self.lo0 = system_input['loopback']['ipv4_addr'] if system_input['loopback'] else None
        self.rack = system_input['rack']['label'] if system_input['rack'] else None
        self.device_profile = system_input['interface_map']['device_profile_id'] if system_input['interface_map'] else None

@click.command()
@click.option('--bp-name', type=str, envvar='BP_NAME', help='Blueprint name')
@click.option('--file-folder', type=str, default='', help='File folder')
@click.option('--systems-csv', type=str, required=True, help='The CSV file path to create')
def export_systems_csv(bp_name, systems_csv, file_folder):
    """
    Export systems of a blueprint to a CSV file

    The CSV file will have below columns:
    system, asn, lo0, rack, device_profile
    
    """
    logger = prep_logging('DEBUG', 'export_systems()')

    cliVar.update(file_folder=file_folder, bp_name=bp_name)
    bp = cliVar.get_blueprint()
    if not bp:
        return

    file_folder = file_folder or os.getenv('FILE_FOLDER', '.')
    systems_csv_path = os.path.expanduser(f"{file_folder}/{systems_csv}")
    logger.info(f"{systems_csv_path=} writing to {systems_csv_path}")
    """
    TODO: implement tags
        optional(
            node(name='system').in_('tag').node(name='tag')
            )
    """
    systems_query = """match(
        node('system', name='system'),
        optional(
            node(name='system').in_('composed_of_systems').node('domain', name='domain')
        ),
        optional(
            node(name='system').out('hosted_interfaces').node('interface', if_name='lo0.0', name='loopback')
            ),
        optional(
            node(name='system').out('part_of_rack').node('rack', name='rack')
            ),
        optional(
            node(name='system').out('interface_map').node('interface_map', name='interface_map')
            )
    )"""
    systems_rest = bp.query(systems_query)
    systems = systems_rest.ok_value
    with open(systems_csv_path, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([field.name for field in fields(SystemsData)])
        for system in systems:
            system_data = SystemsData(system)
            # logger.info(f"{system_data}")    
            writer.writerow(asdict(system_data).values())



@click.command()
@click.option('--gs-csv-in', type=str, default='./var/gs_sample.csv', help='Path to the CSV file for generic systems')
def import_generic_system(gs_csv_in: str):
    """
    Import generic systems from a CSV file

    \b
    Sample CSV file: https://github.com/kimcharli/ck-apstra-api/blob/main/tests/fixtures/gs_sample.csv
    """
    logger = prep_logging('DEBUG', 'import_generic_system()')

    session = cliVar.session
    # CkApstraSession(host_ip, host_port, host_user, host_password)
    if session.last_error:
        logger.error(f"Session error: {session.last_error}")
        return
    gs_csv_path = os.path.expanduser(gs_csv_in)

    links_to_add = []
    with open(gs_csv_path, 'r') as csvfile:
        csv_reader = csv.reader(csvfile)
        headers = next(csv_reader)  # Read the header row
        expected_headers = [header.value for header in GsCsvKeys]
        if sorted(headers) != sorted(expected_headers):
            raise ValueError(f"CSV header {headers} mismatch.\n    Expected headers: {expected_headers}")

        for row in csv_reader:
            links_to_add.append(dict(zip(headers, row)))

    logger.info(f"Importing generic systems {links_to_add=}")
    for res in add_generic_systems(session, links_to_add):
        if isinstance(res, Ok):
            logger.info(res.ok_value)
        elif isinstance(res, Err):
            logger.warning(res.err_value)
        else:
            logger.info(res)


@click.command()
@click.option('--gs-csv-out', type=str, default='./var/gs.csv', help='Path to the CSV file for generic systems')
def export_generic_system(gs_csv_out: str):
    """
    Export generic systems to a CSV file
    """
    logger = prep_logging('DEBUG', 'export_generic_system()')

    session = cliVar.session
    if session.last_error:
        logger.error(f"Session error: {session.last_error}")
        return
    gs_csv_path = os.path.expanduser(gs_csv_out)

    for res in get_generic_systems(session, gs_csv_path):
        if isinstance(res, Ok):
            logger.info(res.ok_value)
        elif isinstance(res, Err):
            logger.warning(res.err_value)
        else:
            logger.info(f"text {res}")
