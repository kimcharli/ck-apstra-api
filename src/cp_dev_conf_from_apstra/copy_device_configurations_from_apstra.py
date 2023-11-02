#!/usr/bin/env python3

import os
import json
import urllib3
import click
import getpass

# python3 $0 -s <apstra-IP> -b <blueprint-label> [-u <user-name>] [-p <password>] -o <output-dir> 
# python3 src/ps_apstra_python/copy_device_configurations_from_apstra.py -s 10.85.192.61 -b pslab -o ~/Downloads/test2_dir 
# python3 src/ps_apstra_python/copy_device_configurations_from_apstra.py -s 10.85.192.61 -b pslab  -o ~/Downloads/test2_dir -u admin -p admin
PROGNAME = 'get-device-configuration'



class CkAosServer:
    # http
    # json_header
    # json_token_header
    # token

    def __init__(self, server, port, user, password ) -> None:
        # urllib3.disable_warnings()
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
        # print(f"== auth_spec: {auth_spec}")
        resp = self.http_post( auth_url, auth_spec, headers=self.json_header, expected=201)
        self.token = json.loads(resp.data)["token"]
        # print(f"== token: {self.token}")

    def http_post(self, path, data, headers=None, expected=None) -> urllib3.response.HTTPResponse:
        print_prefix = "==== AosServer.http_post()"
        if not headers:
            headers = self.json_token_header
        # print(f"{print_prefix} {path}\n{data}")
        resp = self.http.request('POST', path, body=json.dumps(data), headers=headers)
        if expected:
            # print(f"{print_prefix} status (expect {expected}): {resp.status}")
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
        # print_prefix = "==== AosBp.__init():"
        self.server = aos_server
        self.label = bp_label

        resp = self.server.http_get_json("/api/blueprints")
        for i in resp["items"]:
            if i["label"] == self.label:
                self.id = i["id"]

    def get_systems(self):
        resp = self.server.http_get_json(f"/api/blueprints/{self.id}/systems")        
        self.systems = [x['system_id'] for x in resp['items']]
        # print(f"{self.systems=}")
    
    def get_rendering(self, system):
        resp = self.server.http_get_json(f"/api/blueprints/{self.id}/systems/{system}/config-rendering")
        # print(f"{resp['config']=}")
        return resp['config']

    def get_pristine(self, system):
        resp = self.server.http_get_json(f"/api/systems/{system}/pristine-config")
        # print(f"{resp['config']=}")
        return resp['pristine_data']

@click.command(name='copy-device-configurations-from-apstra')
@click.option('--server', help='Apstra server IP address')
@click.option('--blueprint', help='Apstra blueprint label')
@click.option('--username', default='admin', help='Apstra username')
@click.option('--password', help='Apstra password')
@click.option('--output-dir', help='Output directory')
def main(server, blueprint, username, password, output_dir):
    # parser = argparse.ArgumentParser(prog=PROGNAME)
    # parser.add_argument(
    #     "-s", "--server", help="Provide the hostname of the Apstra Controller"
    # )
    # parser.add_argument(
    #     "-b", "--blueprint", help="Provide the blueprint label"
    # )
    # parser.add_argument(
    #     "-u", "--username", help="Provide the username of the Apstra Controller"
    # )
    # parser.add_argument(
    #     "-p", "--password", help="Provide the password"
    # )
    # parser.add_argument(
    #     "-o", "--output-dir", default=".", help="Provide the output dir to save configurations"
    # )
    # options = parser.parse_args(args_test) if args_test else parser.parse_args()

    begin_configlet = '------BEGIN SECTION CONFIGLETS------'
    begin_set = '------BEGIN SECTION SET AND DELETE BASED CONFIGLETS------'
    show_tech_config_path = 'main_sysdb_dump/device/deployment/config'
    show_tech_pristine_path = 'main_sysdb_dump/device/deployment/pristine'
    pristine_begin_mark = '<PRISTINE CONFIG BEGIN>'

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

    # print(f"{bp=}")
    bp.get_systems()
    for system in bp.systems:
        print(f"{system=}")
        rendered_confg = bp.get_rendering(system)
        with open(f"{blueprint_dir}/{system}-rendered.txt", 'w') as f:
            f.write(rendered_confg)
        print("-- Reading rendered configuration")
        config_string = rendered_confg.split(begin_configlet)
        with open(f"{blueprint_dir}/{system}.txt", 'w') as f:
            f.write(config_string[0])
        if len(config_string) < 2:
            # no configlet. skip
            continue
        configlet_string = config_string[1].split(begin_set)
        with open(f"{blueprint_dir}/{system}-configlet.txt", 'w') as f:
            f.write(configlet_string[0])
        if len(configlet_string) < 2:
            # no configlet in set type. skip
            continue
        with open(f"{blueprint_dir}/{system}-configlet-set.txt", 'w') as f:
            f.write(configlet_string[1])

        print("-- Reading pristine configuration")
        pristine_config = bp.get_pristine(system)[0]['content']
        # print(f"{pristine_config=}")
        with open(f"{blueprint_dir}/{system}-pristine.txt", 'w') as f:
            f.write(pristine_config)

        # sys.exit()


@click.group()
def cli():
    pass

cli.add_command(main)

if __name__ == '__main__':
    main()

