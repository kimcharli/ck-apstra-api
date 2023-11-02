#!/usr/bin/env python3

# https://github.com/kimcharli/pull-device-config

import os
import json
import urllib3
import click
import getpass

PROGNAME = 'get-device-configuration'


class CkAosServer:
    # http
    # json_header
    # json_token_header
    # token

    def __init__(self, server, port, user, password ) -> None:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.http = urllib3.HTTPSConnectionPool(server, port=port, cert_reqs='CERT_NONE', assert_hostname=False)

        self.json_header = urllib3.response.HTTPHeaderDict({"Content-Type": "application/json"})
        self._auth(user, password)
        self.json_token_header = urllib3.response.HTTPHeaderDict({"Content-Type": "application/json", "AuthToken": self.token})

    def _auth(self, user, password) -> None:
        auth_url = "/api/aaa/login"
        auth_spec = {
            "username": user,
            "password": password
        }
        resp = self.http_post( auth_url, auth_spec, headers=self.json_header, expected=201)
        self.token = json.loads(resp.data)["token"]

    def http_post(self, path, data, headers=None, expected=None) -> urllib3.response.HTTPResponse:
        print_prefix = "==== AosServer.http_post()"
        if not headers:
            headers = self.json_token_header
        resp = self.http.request('POST', path, body=json.dumps(data), headers=headers)
        if expected:
            if resp.status != expected:
                print(f"{print_prefix} body: {resp.data}")
        else:
            print(f"{print_prefix} status: {resp.status}")
        return resp

    def http_get(self, path) -> urllib3.response.HTTPResponse:
        return self.http.request('GET', path, headers=self.json_token_header)
    
    def http_get_json(self, path):
        resp = self.http_get(path)
        return json.loads(resp.data)


class CkAosBlueprint:
    # server
    # label
    # id
    # systems
    def __init__(self, aos_server, bp_label: str, ) -> None:
        self.server = aos_server
        self.label = bp_label

        resp = self.server.http_get_json("/api/blueprints")
        for i in resp["items"]:
            if i["label"] == self.label:
                self.id = i["id"]

    def get_systems(self):
        resp = self.server.http_get_json(f"/api/blueprints/{self.id}/systems")        
        self.systems = [x['system_id'] for x in resp['items']]
    
    def get_managed_system_nodes(self):
        SYSTEM_NODE_NAME='system'
        system_query = f"node('system', system_type='switch', management_level='full_control', name='{SYSTEM_NODE_NAME}')"
        resp = self.server.http_post(f"/api/blueprints/{self.id}/qe", data={'query': system_query})
        self.managed_system_nodes = [x[SYSTEM_NODE_NAME] for x in resp.json()['items']]
        return self.managed_system_nodes
    
    def get_rendering(self, system):
        resp = self.server.http_get_json(f"/api/blueprints/{self.id}/systems/{system}/config-rendering")
        return resp['config']

    def get_node_rendering(self, node_id):
        resp = self.server.http_get_json(f"/api/blueprints/{self.id}/nodes/{node_id}/config-rendering")
        return resp['config']

    def get_pristine(self, system):
        resp = self.server.http_get_json(f"/api/systems/{system}/pristine-config")
        return resp['pristine_data']

def write_to_file(file_name, content):
    MIN_SIZE = 2  # might have one \n
    if len(content) > MIN_SIZE:
        with open(file_name, 'w') as f:
            f.write(content)

@click.command(name='copy-device-configurations-from-apstra')
@click.option('--server', help='Apstra server IP address')
@click.option('--blueprint', help='Apstra blueprint label')
@click.option('--username', default='admin', help='Apstra username')
@click.option('--password', help='Apstra password')
@click.option('--output-dir', help='Output directory')
def main(server, blueprint, username, password, output_dir):
    begin_configlet = '------BEGIN SECTION CONFIGLETS------'
    begin_set = '------BEGIN SECTION SET AND DELETE BASED CONFIGLETS------'

    server = server or input('Apstra server IP address: ')
    blueprint = blueprint or input('Apstra blueprint name: ')
    username = username or input('Username: ')
    password = password or getpass.getpass(prompt='Password: ')

    server = CkAosServer(server, 443, username, password)
    bp = CkAosBlueprint(server, blueprint)

    output_folder_name = output_dir or input('Output directory: ')
    blueprint_dir = f"{output_folder_name}/{blueprint}"
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

        rendered_confg = bp.get_node_rendering(system_id)
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


@click.group()
def cli():
    pass

cli.add_command(main)

if __name__ == '__main__':
    main()

