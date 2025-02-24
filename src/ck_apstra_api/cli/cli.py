import click
import sys

from ck_apstra_api import CkApstraSession, prep_logging

from . import cliVar

from .blueprint import check_blueprint, export_blueprint_json, import_blueprint_json, print_lldp_data, export_device_configs
from .virtual_network import export_virtual_network_csv, import_virtual_network_csv, relocate_vn, test_get_temp_vn, assign_vn_to_leaf
from .system import export_systems, export_generic_system, import_generic_system
from .ip_link import export_iplink, import_iplink
from .dci import export_dci, import_dci
from .configlet_validate import validate_configlet
from .vlan_cts import add_single_vlan_cts



@click.group()
@click.option('--host-ip', type=str, envvar='HOST_IP', help='Host IP address')
@click.option('--host-port', type=int, envvar='HOST_PORT', help='Host port')
@click.option('--host-user', type=str, envvar='HOST_USER', help='Host username', default='admin')
@click.option('--host-password', type=str, envvar='HOST_PASSWORD', help='Host password')
@click.option('--file-folder', type=str, envvar='FILE_FOLDER', help='Folder path to read files from and write files to')
@click.option('--log-folder', type=str, envvar='LOG_FOLDER', help='Folder path to write log files to')
@click.version_option(message='%(package)s, %(version)s')
@click.pass_context
def cli(ctx, host_ip: str, host_port: str, host_user: str, host_password: str, file_folder: str, log_folder: str):
    """
    A CLI tool for interacting with ck-apstra-api.

    The options that can be specified in .env file: HOST_IP, HOST_PORT, HOST_USER, HOST_PASSWORD
    """
    ctx.ensure_object(dict)
    ctx.obj['HOST_IP'] = host_ip
    ctx.obj['HOST_PORT'] = host_port
    ctx.obj['HOST_USER'] = host_user
    ctx.obj['HOST_PASSWORD'] = host_password
    ctx.obj['FILE_FOLDER'] = file_folder

    cliVar.update(file_folder=file_folder, log_folder=log_folder)
    logger = cliVar.gen_logger('DEBUG', 'cli()')

    cliVar.session = CkApstraSession(host_ip, host_port, host_user, host_password)
    if cliVar.session.last_error:
        logger.error(f"Session error: {cliVar.session.last_error}")
        return

    pass


@cli.command()
@click.pass_context
def debug_context(ctx):
    """
    Debug the context
    """
    print(f"{ctx.obj=}")


@cli.command()
@click.pass_context
def check_apstra(ctx):
    """
    Test the connectivity to the server
    """
    print(f"version {cliVar.session.version=} {cliVar.session.token=}")
    cliVar.session.logout()


cli.add_command(check_blueprint)
cli.add_command(export_blueprint_json)
cli.add_command(import_blueprint_json)
cli.add_command(print_lldp_data)
cli.add_command(export_device_configs)

cli.add_command(export_virtual_network_csv)
cli.add_command(import_virtual_network_csv)
cli.add_command(relocate_vn)
cli.add_command(test_get_temp_vn)
cli.add_command(assign_vn_to_leaf)

cli.add_command(export_systems)
cli.add_command(export_generic_system)
cli.add_command(import_generic_system)

cli.add_command(export_iplink)
cli.add_command(import_iplink)

cli.add_command(export_dci)
cli.add_command(import_dci)

cli.add_command(validate_configlet)

cli.add_command(add_single_vlan_cts)


if __name__ == "__main__":
    cli()
