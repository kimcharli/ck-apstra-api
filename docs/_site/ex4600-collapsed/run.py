import jinja2
import yaml

template_file = '../template.conf.j2'
inventory_file = '../inventory.yml'
out_folder = '../../temp'

def main():
    with open(template_file) as f:
        template = jinja2.Template(f.read())
    inventory = yaml.load(open(inventory_file), Loader=yaml.CLoader)
    for rack_name, rack in inventory.items():
        print(f"Creating configurations for Rack: {rack_name}")
        for device_name, device in rack['hosts'].items():            
            print(f"######## Creating Configuration for Device: {device_name}")
            peer = device['peer']
            vars = {
                'local_lo0_ip': rack['vars']['lo0_ip'][device_name],
                'peer_lo0_ip': rack['vars']['lo0_ip'][peer],
                'local_ae0_ip': rack['vars']['ae0_ip'][device_name],
                'peer_ae0_ip': rack['vars']['ae0_ip'][peer],
                'local_bgp_as': rack['vars']['bgp_as'][device_name],
                'peer_bgp_as': rack['vars']['bgp_as'][peer],
            }
            conf_file_path = f"{out_folder}/{device_name}.conf"
            with open(conf_file_path, 'w') as f:
                f.write(template.render(**device, **rack['vars'], **vars))

if __name__ == '__main__':
    main()