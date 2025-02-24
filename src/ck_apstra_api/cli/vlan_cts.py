import json
import os
from pathlib import Path
import click
from result import Err, Ok

from . import cliVar, prep_logging

@click.command()
# @click.option('--bp-name', type=str, envvar='BP_NAME', help='Blueprint name')
@click.option('--file-name', type=str, envvar='FILE_NAME', help='File name for the vlan CT specs')
@click.pass_context
def add_single_vlan_cts(ctx, file_name: str):
    """
    Create single vlan connectivity templates

    input - yaml file

    \b
    ---
    blueprint: label-of-the-blueprint
    tagged_ct_name_format: vn{vlan_id}
    untagged_ct_name_format: vn{vlan_id}-untagged
    vni_base: 200000
    tagged_vlan_ids:
        - 10
        - 20
    untagged_vlan_ids:
        - 20
        - 21

    Skip if the ct already exists
    """
    func_name = 'add_single_vlan_cts()'
    if file_name:
        cliVar.update(file_name=file_name)
    else:
        cliVar.update(file_folder='tests/fixtures', file_name='mock-vlan-cts.yaml')
    logger = cliVar.gen_logger('DEBUG', func_name)

    data = cliVar.read_file()
    logger.info(f"{cliVar=}")
    logger.info(f"{data=}")

    ck_bp = cliVar.get_blueprint(data['blueprint'], logger)
    if not ck_bp:
        return
    tagged_ct_name_format = data['tagged_ct_name_format']
    untagged_ct_name_format = data['untagged_ct_name_format']
    vni_base = data['vni_base']
    tagged_vlan_ids = data['tagged_vlan_ids']
    untagged_vlan_ids = data['untagged_vlan_ids']

    logger.info(f"tagged_vlan_ids to add {tagged_vlan_ids}")
    for vlan_id in data['tagged_vlan_ids']:
        istagged = True
        ct_label = f"{tagged_ct_name_format.format(vlan_id=vlan_id)}"
        logger.info(f"tagged {vlan_id=}, name = {ct_label}")
        for res in ck_bp.add_single_vlan_ct(vlan_id + vni_base, vlan_id, is_tagged=istagged, ct_label=ct_label):
            if isinstance(res, Err):
                logger.Err(f"{res.err_value}")
            else:
                logger.info(f"{res.ok_value}")
    logger.info("")
    logger.info(f"untagged_vlan_ids to add {untagged_vlan_ids}")
    for vlan_id in data['untagged_vlan_ids']:
        is_tagged = False
        ct_label = f"{untagged_ct_name_format.format(vlan_id=vlan_id)}"
        logger.info(f"tagged {vlan_id=}, name = {ct_label}")
        for res in ck_bp.add_single_vlan_ct(vlan_id + vni_base, vlan_id, is_tagged=is_tagged, ct_label=ct_label):
            if isinstance(res, Err):
                logger.Err(f"{res.err_value}")
                break
            else:
                logger.info(f"{res.ok_value}")
