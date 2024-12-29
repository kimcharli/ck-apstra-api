import json
import os
import click
import jinja2

from . import cliVar, prep_logging

@click.command()
@click.option('--system', type=str, required=True, help='System label to test against')
@click.option('--configlet-file', type=str, required=True, help='Configlet File (jinjia2)')
@click.option('--bp-name', type=str, envvar='BP_NAME', help='Blueprint name')
@click.pass_context
def test_configlet(ctx, bp_name: str, configlet_file: str, system: str):
    """
    Test the configlet (jinja) against the system

    """
    logger = prep_logging('DEBUG', 'configlet_test()')

    # load the configlet file
    configlet_file_path = os.path.expanduser(configlet_file)
    j2_content = ''
    with open(configlet_file_path, 'r') as f:
        j2_content = f.read()
    if not j2_content:
        logger.error(f"Configlet file {configlet_file_path} is empty")
        return
    template = jinja2.Template(j2_content)

    bp = cliVar.get_blueprint(bp_name, logger)
    if not bp:
        logger.error(f"Blueprint {bp_name} does not exist")
        return
    
    # load the device context
    system_query = f"node('system', label='{system}', name='n')"
    system_nodes = bp.query(system_query)
    if not system_nodes:
        logger.error(f"System {system} not found")
        return
    system_node = system_nodes.ok_value[0]['n']
    device_context = json.loads(bp.get_item(f"nodes/{system_node['id']}/config-context")['context'])

    # apply the template
    device_rendered = template.render(**device_context)
    logger.info(f"Rendered configlet for {system} in {bp_name}")
    print(device_rendered)
    logger.info(f"Rendered configlet for {system} in {bp_name} printed")

