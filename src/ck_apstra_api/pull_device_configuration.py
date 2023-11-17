#!/usr/bin/env python3

import os
import json
import urllib3
import click
import getpass

from ck_apstra_api.cli import CkJobEnv

def write_to_file(file_name, content):
    MIN_SIZE = 2  # might have one \n
    if len(content) > MIN_SIZE:
        with open(file_name, 'w') as f:
            f.write(content)


def order_pull_configurations(order: CkJobEnv):
    begin_configlet = '------BEGIN SECTION CONFIGLETS------'
    begin_set = '------BEGIN SECTION SET AND DELETE BASED CONFIGLETS------'

    output_folder_name = order.config_dir
    blueprint_dir = f"{output_folder_name}/{order.main_blueprint_name}"
    bp = order.main_bp

    if not os.path.isdir(blueprint_dir):
        os.makedirs(blueprint_dir, exist_ok=True)

    for system_node in bp.get_managed_system_nodes():
        system_id = system_node['id']
        system_label = system_node['label']
        system_serial = system_node['system_id']
        print(f"{system_label=}")

        # get pristine config if there is a serial number
        if system_serial:
            print("-- Reading pristine configuration")
            pristine_config = bp.get_pristine(system_serial)[0]['content']
            with open(f"{blueprint_dir}/{system_label}-pristine.txt", 'w') as f:
                f.write(pristine_config)

        rendered_confg = bp.get_item(f"nodes/{system_id}/config-rendering")['config']
        write_to_file(f"{blueprint_dir}/{system_label}-rendered.txt", rendered_confg)

        print("-- Reading rendered configuration")
        config_string = rendered_confg.split(begin_configlet)
        write_to_file(f"{blueprint_dir}/{system_label}.txt", config_string[0])
        if len(config_string) < 2:
            # no configlet. skip
            continue

        configlet_string = config_string[1].split(begin_set)
        write_to_file(f"{blueprint_dir}/{system_label}-configlet.txt", configlet_string[0])
        if len(configlet_string) < 2:
            # no configlet in set type. skip
            continue

        write_to_file(f"{blueprint_dir}/{system_label}-configlet-set.txt", configlet_string[1])

@click.command(name='pull-device-configurations', help='pull produced configurations from Apstra')
def click_pull_configurations():
    order = CkJobEnv()
    order_pull_configurations(order)

if __name__ == '__main__':
    click_pull_configurations()

