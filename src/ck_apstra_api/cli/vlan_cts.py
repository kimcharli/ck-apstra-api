import json
import os
from pathlib import Path
import click

from . import cliVar, prep_logging

@click.command()
@click.option('--bp-name', type=str, envvar='BP_NAME', help='Blueprint name')
@click.option('--file-name', type=str, envvar='FILE_NAME', help='File name for the vlan CT specs')
@click.pass_context
def create_single_vlan_connectivity_template(ctx, bp_name: str, file_name: str):
    """
    Create single vlan connectivity templates

    input - yaml file
    tagged_ct_name_format: vn{vlan_id}
    untagged_ct_name_format: vn{vlan_id}-untagged
    tagged_vlan_ids:
        - 10
        - 20
    untagged_vlan_ids:
        - 20
        - 21

    Skip if the ct already exists
    """
    cliVar.update(bp_name=bp_name, file_name=file_name, caller='create_single_vlan_connectivity_template')
    logger = cliVar.gen_logger('DEBUG', 'create_single_vlan_connectivity_template()')

    bp = cliVar.get_blueprint(bp_name, logger)
    if not bp:
        return

    logger.info(f"{cliVar}")


