import json
import os
from pathlib import Path
import click

from . import cliVar, prep_logging

@click.command()
@click.option('--bp-name', type=str, envvar='BP_NAME', help='Blueprint name')
@click.pass_context
def check_blueprint(ctx, bp_name: str):
    """
    Test the connectivity to the blueprint

    The blueprint name can be specified in the environment variable BP_NAME
    """
    logger = prep_logging('DEBUG', 'check_blueprint()')

    _ = cliVar.get_blueprint(bp_name, logger)        
    cliVar.session.logout()


@click.command()
@click.option('--bp-name', type=str, envvar='BP_NAME', help='Blueprint name')
@click.option('--json-file', type=str, envvar='JSON_FILE', help='Json file name to export to')
@click.pass_context
def export_blueprint_json(ctx, bp_name: str, json_file: str = None):
    """
    Export a blueprint into a json file

    bp-name can be specified in the environment variable BP_NAME
    json-file can be specified in the environment variable JSON_FILE. If not specified, it will be the blueprint name
    """
    if not json_file:
        json_file = f"{bp_name}.json"
    cliVar.update(bp_name=bp_name, file_name=json_file, caller='export_blueprint_json')
    logger = prep_logging('DEBUG', 'export_blueprint()')

    bp = cliVar.get_blueprint(None, logger)

    # if not json_file:
    #     json_file = f"{bp_name}.json"
    # json_path = os.path.expanduser(json_file)

    the_blueprint_data = bp.dump()
    # with open(json_path, 'w') as f:
    #     f.write(json.dumps(the_blueprint_data, indent=2))

    # logger.info(f"blueprint {bp_name} exported to {json_file}")
    cliVar.write_file(json.dumps(the_blueprint_data, indent=2))


@click.command()
@click.option('--bp-name', type=str, envvar='BP_NAME', help='Blueprint name to create')
@click.option('--json-file', type=str, envvar='JSON_FILE', help='Json file name to import from')
@click.pass_context
def import_blueprint_json(ctx, bp_name: str, json_file: str = None):
    """
    Import a blueprint from a json file

    bp-name can be specified in the environment variable BP_NAME
    json-file can be specified in the environment variable JSON_FILE. If not specified, it will be the blueprint name
    """
    if not json_file:
        json_file = f"{bp_name}.json"
    cliVar.update(bp_name=bp_name, file_name=json_file, caller='import_blueprint_json')
    logger = prep_logging('DEBUG', 'import_blueprint_json()')

    checked_bp = cliVar.get_blueprint(None, logger)
    if checked_bp:
        logger.error(f"Blueprint {bp_name} already exists")
        return

    json_path = os.path.expanduser(json_file)
    with open(json_path, 'r') as f:
        bp_json = f.read()

    bp_dict = json.loads(bp_json)
    bp_created = cliVar.session.create_blueprint_json(bp_name, bp_dict)
    logger.info(f"blueprint {bp_name} created: {bp_created}")



@click.command()
@click.option('--bp-name', type=str, envvar='BP_NAME', help='Blueprint name')
@click.pass_context
def print_lldp_data(ctx, bp_name: str = 'terra'):
    """
    Print the LLDP data of the blueprint
    """
    logger = prep_logging('DEBUG', 'export_device_configs()')

    bp = cliVar.get_blueprint(bp_name, logger)
    if not bp:
        return

    lldp_data = bp.get_lldp_data()
    for link in lldp_data['links']:
        logger.info(f"{link['id']=} {link['endpoints'][0]['system']['label']}:{link['endpoints'][0]['interface']['if_name']} {link['endpoints'][1]['system']['label']}:{link['endpoints'][1]['interface']['if_name']}")
        
    return lldp_data


@click.command()
@click.option('--bp-name', type=str, envvar='BP_NAME', help='Blueprint name')
@click.option('--file-folder', type=str, envvar='FILE_FOLDER', help='Folder name to export')
@click.pass_context
def export_device_configs(ctx, bp_name: str, file_folder: str):
    """
    Export a device configurations into multiple files

    The folder for each device will be created with the device name.
    0_load_override_pristine.txt (if the device is managed)
    0_load_override_freeform.txt (if case of freeform)
    1_load_merge_intended.txt
    2_load_merge_configlet.txt (if applicable)
    3_load_set_configlet-set.txt (if applicable)
    """
    logger = prep_logging('DEBUG', 'export_device_configs()')

    cliVar.update(file_folder=file_folder, bp_name=bp_name)
    bp = cliVar.get_blueprint(bp_name, logger)
    if not bp:
        return
    
    logger.info(f"Configuration files will be written under {file_folder}/{bp_name}/<device-label>")
    bp_folder_path = os.path.expanduser(f"{file_folder}/{bp_name}")
    Path(bp_folder_path).mkdir(parents=True, exist_ok=True)


    def write_to_file(file_name, content):
        MIN_SIZE = 2  # might have one \n
        if len(content) > MIN_SIZE:
            with open(file_name, 'w') as f:
                f.write(content)
            logger.info(f"write_to_file(): {os.path.basename(file_name)}")


    # switch for reference architecture, internal for freeform
    for switch in [x['switch'] for x in bp.query("node('system', system_type=is_in(['switch', 'internal']), name='switch')").ok_value]:
        system_label = switch['label']
        system_id = switch['id']
        system_serial = switch['system_id']
        system_dir = f"{bp_folder_path}/{system_label}"
        Path(system_dir).mkdir(exist_ok=True)
        logger.info(f"{system_label=}")

        if system_serial:
            pristine_config = cliVar.session.get_items(f"systems/{system_serial}/pristine-config")['pristine_data'][0]['content']
            write_to_file(f"{system_dir}/0_load_override_pristine.txt", pristine_config)

        rendered_confg = bp.get_item(f"nodes/{system_id}/config-rendering")['config']
        write_to_file(f"{system_dir}/rendered.txt", rendered_confg)

        begin_configlet = '------BEGIN SECTION CONFIGLETS------'
        begin_set = '------BEGIN SECTION SET AND DELETE BASED CONFIGLETS------'

        config_string = rendered_confg.split(begin_configlet)
        if bp.design == 'freeform':
            write_to_file(f"{system_dir}/0_load_override_freeform.txt", config_string[0])
        else:
            write_to_file(f"{system_dir}/1_load_merge_intended.txt", config_string[0])
        if len(config_string) < 2:
            # no configlet. skip
            continue

        configlet_string = config_string[1].split(begin_set)
        write_to_file(f"{system_dir}/2_load_merge_configlet.txt", configlet_string[0])
        if len(configlet_string) < 2:
            # no configlet in set type. skip
            continue

        write_to_file(f"{system_dir}/3_load_set_configlet-set.txt", configlet_string[1])

