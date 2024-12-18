# ck-apstra-api

https://github.com/kimcharli/ck-apstra-api

# prerequisit

## python3.11 or higher

[ChangeLog](./ChangeLog.md)

### Windows environment
install python3.11: https://www.python.org/downloads/windows/


## git

### Windows environment
https://git-scm.com/download/win


# prepare venv

```
ckim@ckim-mbp:sandbox % mkdir test
ckim@ckim-mbp:sandbox % cd test             
ckim@ckim-mbp:test % python -m venv .venv                      
ckim@ckim-mbp:test % source .venv/bin/activate
(.venv) ckim@ckim-mbp:test % pip install ck-apstra-api==0.5.0
...                                                                                             
(.venv) ckim@ckim-mbp:test % 
```

## Windows environment

```
cd test
py -m venv .venv
.venv\Scripts\activate
pip install ck-apstra-api==0.5.0
```


## help commands

```
(.venv) ckim@ckim-mbp:ck-apstra-api % ck-cli --version
ck_apstra_api, 0.5.0
(.venv) ckim@ckim-mbp:ck-apstra-api % 
```

```
(.venv) ckim@ckim-mbp:ck-apstra-api % ck-cli --help   
Usage: ck-cli [OPTIONS] COMMAND [ARGS]...

  A CLI tool for interacting with ck-apstra-api

Options:
  --host-ip TEXT        Host IP address
  --host-port INTEGER   Host port
  --host-user TEXT      Host username
  --host-password TEXT  Host password
  --version             Show the version and exit.
  --help                Show this message and exit.

Commands:
  check-apstra           Test the connectivity to the server
  check-blueprint        Test the connectivity to the blueprint
  export-blueprint       Export a blueprint into a json file
  export-device-configs  Export a device configurations into multiple files
  export-generic-system  Export generic systems to a CSV file
  export-systems         Export systems of a blueprint to a CSV file
  import-blueprint       Import a blueprint from a json file
  import-generic-system  Import generic systems from a CSV file
  relocate-vn            Move a Virtual Network to the target Routing Zone
  test-get-temp-vn       Test get_temp_vn
(.venv) ckim@ckim-mbp:ck-apstra-api % 
```

## build generic system

### CSV file example

|line|blueprint|server       |ext|tags_server|ae   |lag_mode   |ct_names    |tags_ae|speed|ifname|switch  |switch_ifname|tags_link|comment|
|----|---------|-------------|---|-----------|-----|-----------|------------|-------|-----|------|--------|-------------|---------|-------|
|1   |terra    |single-home-1|   |single     |     |           | vn20       |single |10g  |eth0  |server_1|xe-0/0/11    |         |       |
|2   |terra    |dual-home-1  |   |dual       |ae101|lacp_active|vn20 , vn101|dual   |10g  |eth0  |server_1|xe-0/0/12    |forceup  |       |
|3   |terra    |dual-home-1  |   |dual       |ae101|lacp_active|vn20,vn101  |dual   |10g  |eth1  |server_2|xe-0/0/12    |         |       |

[gs_sample.csv](./tests/fixtures/gs_sample.csv)


### run example

```
(.venv) ckim@ckim-mbp:ck-apstra-api % ck-cli import-generic-system --help                                    
Usage: ck-cli import-generic-system [OPTIONS]

  Import generic systems from a CSV file

Options:
  --gs-csv-in TEXT  Path to the CSV file for generic systems
  --help            Show this message and exit.
(.venv) ckim@ckim-mbp:ck-apstra-api % 
(.venv) ckim@ckim-mbp:ck-apstra-api % ck-cli --host-ip 10.85.192.45 --host-password admin import-generic-system --gs-csv-in ~/Downloads/gs_sample.csv
2024-06-29 17:51:43,445 - INFO     - import_generic_system - add_generic_systems ServerBlueprint._bps={'terra': ServerBlueprint(blueprint='terra')} (cli.py:246)
2024-06-29 17:51:43,445 - INFO     - import_generic_system - ServerBlueprint:fetch_apstra() self.blueprint='terra' (cli.py:246)
2024-06-29 17:51:43,956 - INFO     - import_generic_system - LinkMember(server_1:xe-0/0/11:eth0)::fetch_apstra() done LinkMember(line='1', speed='10G', ifname='eth0', switch='server_1', switch_ifname='xe-0/0/11', tags_link=[], comment='', fetched_server_ifname=None, fetched_server_intf_id=None, fetched_switch_id='2QKZLUzqCO0ZJ73Fb1I', fetched_switch_intf_id=None, fetched_tags_link=None, fetched_link_id=None) (cli.py:246)
2024-06-29 17:51:43,956 - INFO     - import_generic_system - LinkGroup(____1)::fetch_apstra() done LinkGroup(ae='____1', lag_mode='', ct_names=['vn20'], tags_ae=['single'], fetched_ae_id=None, fetched_lag_mode=None, fetched_ct_names=[], fetched_tags=None) (cli.py:246)
2024-06-29 17:51:43,956 - INFO     - import_generic_system - text GenericSystem(single-home-1)::fetch_apstra() done GenericSystem(server='single-home-1', ext='', tags_server=['single'], gs_id=None, fetched_server_tags=None) (cli.py:250)
2024-06-29 17:51:44,223 - INFO     - import_generic_system - LinkMember(server_1:xe-0/0/12:eth0)::fetch_apstra() done LinkMember(line='2', speed='10G', ifname='eth0', switch='server_1', switch_ifname='xe-0/0/12', tags_link=['forceup'], comment='', fetched_server_ifname=None, fetched_server_intf_id=None, fetched_switch_id='2QKZLUzqCO0ZJ73Fb1I', fetched_switch_intf_id=None, fetched_tags_link=None, fetched_link_id=None) (cli.py:246)
2024-06-29 17:51:44,374 - INFO     - import_generic_system - LinkMember(server_2:xe-0/0/12:eth1)::fetch_apstra() done LinkMember(line='3', speed='10G', ifname='eth1', switch='server_2', switch_ifname='xe-0/0/12', tags_link=[], comment='', fetched_server_ifname=None, fetched_server_intf_id=None, fetched_switch_id='qCc9ps52vPppDp2b6rk', fetched_switch_intf_id=None, fetched_tags_link=None, fetched_link_id=None) (cli.py:246)
2024-06-29 17:51:44,375 - INFO     - import_generic_system - LinkGroup(ae101)::fetch_apstra() done LinkGroup(ae='ae101', lag_mode='lacp_active', ct_names=['vn20', 'vn101'], tags_ae=['dual'], fetched_ae_id=None, fetched_lag_mode=None, fetched_ct_names=[], fetched_tags=None) (cli.py:246)
2024-06-29 17:51:44,375 - INFO     - import_generic_system - text GenericSystem(dual-home-1)::fetch_apstra() done GenericSystem(server='dual-home-1', ext='', tags_server=['dual'], gs_id=None, fetched_server_tags=None) (cli.py:250)
2024-06-29 17:51:44,375 - INFO     - import_generic_system - add_generic_systems fetched ServerBlueprint._bps={'terra': ServerBlueprint(blueprint='terra')} (cli.py:246)
2024-06-29 17:51:51,000 - INFO     - import_generic_system - GenericSystem(single-home-1)::create() creating generic_system_spec={'links': [{'switch': {'system_id': '2QKZLUzqCO0ZJ73Fb1I', 'transformation_id': 1, 'if_name': 'xe-0/0/11'}, 'system': {'system_id': None}, 'lag_mode': None, 'link_group_label': None}], 'new_systems': [{'system_type': 'server', 'label': 'single-home-1', 'port_channel_id_min': 0, 'port_channel_id_max': 0, 'logical_device': {'display_name': 'ck-auto-1x10', 'id': 'ck-auto-1x10', 'panels': [{'panel_layout': {'row_count': 1, 'column_count': 1}, 'port_indexing': {'order': 'T-B, L-R', 'start_index': 1, 'schema': 'absolute'}, 'port_groups': [{'count': 1, 'speed': {'unit': 'G', 'value': 10}, 'roles': ['leaf', 'access']}]}]}}]} (cli.py:246)
2024-06-29 17:51:52,321 - INFO     - import_generic_system - GenericSystem(single-home-1)::create() created (cli.py:246)
2024-06-29 17:51:52,659 - INFO     - import_generic_system - GenericSystem(dual-home-1)::create() creating generic_system_spec={'links': [{'switch': {'system_id': '2QKZLUzqCO0ZJ73Fb1I', 'transformation_id': 1, 'if_name': 'xe-0/0/12'}, 'system': {'system_id': None}, 'lag_mode': None, 'link_group_label': None}, {'switch': {'system_id': 'qCc9ps52vPppDp2b6rk', 'transformation_id': 1, 'if_name': 'xe-0/0/12'}, 'system': {'system_id': None}, 'lag_mode': None, 'link_group_label': None}], 'new_systems': [{'system_type': 'server', 'label': 'dual-home-1', 'port_channel_id_min': 0, 'port_channel_id_max': 0, 'logical_device': {'display_name': 'ck-auto-2x10', 'id': 'ck-auto-2x10', 'panels': [{'panel_layout': {'row_count': 1, 'column_count': 2}, 'port_indexing': {'order': 'T-B, L-R', 'start_index': 1, 'schema': 'absolute'}, 'port_groups': [{'count': 2, 'speed': {'unit': 'G', 'value': 10}, 'roles': ['leaf', 'access']}]}]}}]} (cli.py:246)
2024-06-29 17:51:53,984 - INFO     - import_generic_system - GenericSystem(dual-home-1)::create() created (cli.py:246)
2024-06-29 17:51:53,985 - INFO     - import_generic_system - add_generic_systems generic_systems added ServerBlueprint._bps={'terra': ServerBlueprint(blueprint='terra')} (cli.py:246)
2024-06-29 17:51:53,985 - INFO     - import_generic_system - ServerBlueprint:fetch_apstra() self.blueprint='terra' (cli.py:246)
2024-06-29 17:51:54,399 - INFO     - import_generic_system - LinkMember(server_1:xe-0/0/11:eth0)::fetch_apstra() done LinkMember(line='1', speed='10G', ifname='eth0', switch='server_1', switch_ifname='xe-0/0/11', tags_link=[], comment='', fetched_server_ifname=None, fetched_server_intf_id='Eoj5YQ2DufOIkAwqJFs', fetched_switch_id='2QKZLUzqCO0ZJ73Fb1I', fetched_switch_intf_id='wHrEU9Ogsu5PT3rX5ZU', fetched_tags_link=None, fetched_link_id='server_1<->single-home-1(link-000000001)[1]') (cli.py:246)
2024-06-29 17:51:54,526 - INFO     - import_generic_system - LinkGroup(____1)::fetch_apstra() done LinkGroup(ae='____1', lag_mode='', ct_names=['vn20'], tags_ae=['single'], fetched_ae_id='wHrEU9Ogsu5PT3rX5ZU', fetched_lag_mode=None, fetched_ct_names=[], fetched_tags=None) (cli.py:246)
2024-06-29 17:51:54,662 - INFO     - import_generic_system - text GenericSystem(single-home-1)::fetch_apstra() done GenericSystem(server='single-home-1', ext='', tags_server=['single'], gs_id='vjdUZp5Bzan9ly5CGMg', fetched_server_tags=[]) (cli.py:250)
2024-06-29 17:51:54,791 - INFO     - import_generic_system - LinkMember(server_1:xe-0/0/12:eth0)::fetch_apstra() done LinkMember(line='2', speed='10G', ifname='eth0', switch='server_1', switch_ifname='xe-0/0/12', tags_link=['forceup'], comment='', fetched_server_ifname=None, fetched_server_intf_id='MxGkufPpO905ZT0vyT4', fetched_switch_id='2QKZLUzqCO0ZJ73Fb1I', fetched_switch_intf_id='92L4PECw70iubqVgl88', fetched_tags_link=None, fetched_link_id='server_1<->dual-home-1(link-000000001)[1]') (cli.py:246)
2024-06-29 17:51:54,791 - INFO     - import_generic_system - LinkMember(server_2:xe-0/0/12:eth1)::fetch_apstra() done LinkMember(line='3', speed='10G', ifname='eth1', switch='server_2', switch_ifname='xe-0/0/12', tags_link=[], comment='', fetched_server_ifname=None, fetched_server_intf_id='619M5CRWBvhqPtzhzsM', fetched_switch_id='qCc9ps52vPppDp2b6rk', fetched_switch_intf_id='FlQxBvVV_uVaV_g1VPI', fetched_tags_link=None, fetched_link_id='server_2<->dual-home-1(link-000000002)[1]') (cli.py:246)
2024-06-29 17:51:54,792 - INFO     - import_generic_system - LinkGroup(ae101)::fetch_apstra() done LinkGroup(ae='ae101', lag_mode='lacp_active', ct_names=['vn20', 'vn101'], tags_ae=['dual'], fetched_ae_id=None, fetched_lag_mode=None, fetched_ct_names=[], fetched_tags=None) (cli.py:246)
2024-06-29 17:51:54,916 - INFO     - import_generic_system - text GenericSystem(dual-home-1)::fetch_apstra() done GenericSystem(server='dual-home-1', ext='', tags_server=['dual'], gs_id='l1zH-lTraCUodsjRCGQ', fetched_server_tags=[]) (cli.py:250)
2024-06-29 17:51:54,916 - INFO     - import_generic_system - add_generic_systems after generic system creation - fetched ServerBlueprint._bps={'terra': ServerBlueprint(blueprint='terra')} (cli.py:246)
2024-06-29 17:51:54,916 - INFO     - import_generic_system - LinkGroup(____1)::form_lacp() self.ae='____1' is not for lag. Skipping (cli.py:246)
2024-06-29 17:51:55,982 - WARNING  - import_generic_system - LinkGroup(ae101)::form_lacp() self.ae='ae101' has no ae_id. Skipping (cli.py:248)
2024-06-29 17:51:55,982 - INFO     - import_generic_system - add_generic_systems lacp formed ServerBlueprint._bps={'terra': ServerBlueprint(blueprint='terra')} (cli.py:246)
2024-06-29 17:51:55,982 - INFO     - import_generic_system - ServerBlueprint:fetch_apstra() self.blueprint='terra' (cli.py:246)
2024-06-29 17:51:56,344 - INFO     - import_generic_system - LinkMember(server_1:xe-0/0/11:eth0)::fetch_apstra() done LinkMember(line='1', speed='10G', ifname='eth0', switch='server_1', switch_ifname='xe-0/0/11', tags_link=[], comment='', fetched_server_ifname=None, fetched_server_intf_id='Eoj5YQ2DufOIkAwqJFs', fetched_switch_id='2QKZLUzqCO0ZJ73Fb1I', fetched_switch_intf_id='wHrEU9Ogsu5PT3rX5ZU', fetched_tags_link=None, fetched_link_id='server_1<->single-home-1(link-000000001)[1]') (cli.py:246)
2024-06-29 17:51:56,469 - INFO     - import_generic_system - LinkGroup(____1)::fetch_apstra() done LinkGroup(ae='____1', lag_mode='', ct_names=['vn20'], tags_ae=['single'], fetched_ae_id='wHrEU9Ogsu5PT3rX5ZU', fetched_lag_mode=None, fetched_ct_names=[], fetched_tags=None) (cli.py:246)
2024-06-29 17:51:56,588 - INFO     - import_generic_system - text GenericSystem(single-home-1)::fetch_apstra() done GenericSystem(server='single-home-1', ext='', tags_server=['single'], gs_id='vjdUZp5Bzan9ly5CGMg', fetched_server_tags=[]) (cli.py:250)
2024-06-29 17:51:56,720 - INFO     - import_generic_system - LinkMember(server_1:xe-0/0/12:eth0)::fetch_apstra() done LinkMember(line='2', speed='10G', ifname='eth0', switch='server_1', switch_ifname='xe-0/0/12', tags_link=['forceup'], comment='', fetched_server_ifname=None, fetched_server_intf_id='MxGkufPpO905ZT0vyT4', fetched_switch_id='2QKZLUzqCO0ZJ73Fb1I', fetched_switch_intf_id='92L4PECw70iubqVgl88', fetched_tags_link=None, fetched_link_id='server_1<->dual-home-1(link-000000001)[1]') (cli.py:246)
2024-06-29 17:51:56,720 - INFO     - import_generic_system - LinkMember(server_2:xe-0/0/12:eth1)::fetch_apstra() done LinkMember(line='3', speed='10G', ifname='eth1', switch='server_2', switch_ifname='xe-0/0/12', tags_link=[], comment='', fetched_server_ifname=None, fetched_server_intf_id='619M5CRWBvhqPtzhzsM', fetched_switch_id='qCc9ps52vPppDp2b6rk', fetched_switch_intf_id='FlQxBvVV_uVaV_g1VPI', fetched_tags_link=None, fetched_link_id='server_2<->dual-home-1(link-000000002)[1]') (cli.py:246)
2024-06-29 17:51:56,840 - INFO     - import_generic_system - LinkGroup(ae101)::fetch_apstra() done LinkGroup(ae='ae1', lag_mode='lacp_active', ct_names=['vn20', 'vn101'], tags_ae=['dual'], fetched_ae_id='QsX0BGRzwmP3ZVcNzYA', fetched_lag_mode='lacp_active', fetched_ct_names=[], fetched_tags=None) (cli.py:246)
2024-06-29 17:51:56,974 - INFO     - import_generic_system - text GenericSystem(dual-home-1)::fetch_apstra() done GenericSystem(server='dual-home-1', ext='', tags_server=['dual'], gs_id='l1zH-lTraCUodsjRCGQ', fetched_server_tags=[]) (cli.py:250)
2024-06-29 17:51:56,974 - INFO     - import_generic_system - add_generic_systems after form lag - fetched ServerBlueprint._bps={'terra': ServerBlueprint(blueprint='terra')} (cli.py:246)
2024-06-29 17:51:56,975 - INFO     - import_generic_system - LinkGroup(____1)::rename_interfaces() self.ae='____1' rename_spec={'links': [{'endpoints': [{'interface': {'id': 'wHrEU9Ogsu5PT3rX5ZU'}}, {'interface': {'id': 'Eoj5YQ2DufOIkAwqJFs', 'if_name': 'eth0'}}], 'id': 'server_1<->single-home-1(link-000000001)[1]'}]} (cli.py:246)
2024-06-29 17:51:57,819 - INFO     - import_generic_system - LinkGroup(____1) self.ae='____1' rename done (cli.py:246)
2024-06-29 17:51:57,819 - INFO     - import_generic_system - LinkGroup(ae101)::rename_interfaces() self.ae='ae1' rename_spec={'links': [{'endpoints': [{'interface': {'id': '92L4PECw70iubqVgl88'}}, {'interface': {'id': 'MxGkufPpO905ZT0vyT4', 'if_name': 'eth0'}}], 'id': 'server_1<->dual-home-1(link-000000001)[1]'}, {'endpoints': [{'interface': {'id': 'FlQxBvVV_uVaV_g1VPI'}}, {'interface': {'id': '619M5CRWBvhqPtzhzsM', 'if_name': 'eth1'}}], 'id': 'server_2<->dual-home-1(link-000000002)[1]'}]} (cli.py:246)
2024-06-29 17:51:58,989 - INFO     - import_generic_system - LinkGroup(ae101) self.ae='ae1' rename done (cli.py:246)
2024-06-29 17:51:58,989 - INFO     - import_generic_system - add_generic_systems interfaces renamed ServerBlueprint._bps={'terra': ServerBlueprint(blueprint='terra')} (cli.py:246)
2024-06-29 17:51:59,267 - INFO     - import_generic_system - GenericSystem(single-home-1) done - 1 vlans (cli.py:246)
2024-06-29 17:51:59,524 - INFO     - import_generic_system - GenericSystem(dual-home-1) done - 1 vlans (cli.py:246)
2024-06-29 17:51:59,524 - INFO     - import_generic_system - add_generic_systems vlans added ServerBlueprint._bps={'terra': ServerBlueprint(blueprint='terra')} (cli.py:246)
(.venv) ckim@ckim-mbp:ck-apstra-api % 
```

### code example

Below is an example code to call add_generic_systems from a script.
```python
def import_generic_system(ctx, gs_csv_in: str):
    """
    Import generic systems from a CSV file
    """
    from ck_apstra_api.generic_system import GsCsvKeys, add_generic_systems
    from ck_apstra_api.apstra_session import CkApstraSession
    from result import Ok, Err
    import logging

    logger = logging.getLogger('import_generic_system')
    logger.setLevel(logging.INFO)
    # logger.addHandler(ch)

    host_ip = ctx.obj['HOST_IP']
    host_port = ctx.obj['HOST_PORT']
    host_user = ctx.obj['HOST_USER']
    host_password = ctx.obj['HOST_PASSWORD']

    # uncomment below for debugging purpose. It prints the username and password
    # logger.info(f"{ctx.obj=}")

    session = CkApstraSession(host_ip, host_port, host_user, host_password)
    gs_csv_path = os.path.expanduser(gs_csv_in)

    links_to_add = []
    with open(gs_csv_path, 'r') as csvfile:
        csv_reader = csv.reader(csvfile)
        headers = next(csv_reader)  # Read the header row
        expected_headers = [header.value for header in GsCsvKeys]
        if headers != expected_headers:
            raise ValueError("CSV header mismatch. Expected headers: " + ', '.join(expected_headers))

        for row in csv_reader:
            links_to_add.append(dict(zip(headers, row)))

    for res in add_generic_systems(session, links_to_add):
        if isinstance(res, Ok):
            logger.info(res.ok_value)
        elif isinstance(res, Err):
            logger.warning(res.err_value)
        else:
            logger.info(f"text {res}")
```


## Move a Virtual Network to other Routing Zone
Currenly only takes care of VLANs.

### help
```
ckim@ckim-mbp:ck-apstra-api % ck-cli relocate-vn --help                                                        
Usage: ck-cli relocate-vn [OPTIONS]

  Move a Virtual Network to the target Routing Zone

  The virtual network move involves deleting and recreating the virtual
  network in the target routing zone. To delete the virtual network, the
  associated CT should be taken care of. Either deassign and delete them and
  later do reverse. This CT handling trouble can be mitigated with a temporary
  VN to replace the original VN in the CT. Later, to be reversed later.

Options:
  --virtual-network TEXT  Subject Virtual Network name  [required]
  --routing-zone TEXT     Destination Routing Zone name  [required]
  --blueprint TEXT        Blueprint name  [required]
  --help                  Show this message and exit.
ckim@ckim-mbp:ck-apstra-api % 
```

### run example
```
(.venv) ckim@ckim-mbp:ck-apstra-api % ck-cli --host-ip 10.85.192.45 --host-password admin relocate-vn --virtual-network vn2222 --blueprint terra --routing-zone vrf
2024-07-03 18:47:07,957 - INFO     - immigrate_vn() - Took order blueprint='terra' virtual_network='vn2222' routing_zone='vrf' (cli.py:333)
2024-07-03 18:47:09,195 - INFO     - immigrate_vn() - Temporary VN x-vn2222 not found. Creating... (cli.py:391)
2024-07-03 18:47:10,208 - INFO     - immigrate_vn() - Temporary VN x-vn2222:the_order.test_vn_id='mTlYxQM-bvG1oP6mhZQ' created vn_temp_created=<Response [201]> (cli.py:408)
2024-07-03 18:47:10,208 - INFO     - immigrate_vn() - Ready execute: Order: self.target_vn='vn2222' self.target_vn_id='BPB80Tuop2qUINeUZOU' self.test_vn='x-vn2222' self.test_vn_id='mTlYxQM-bvG1oP6mhZQ' self.target_rz='vrf' self.terget_rz_id='S2WY6qMrf9J6cvoZfeY' (cli.py:410)
2024-07-03 18:47:12,048 - INFO     - immigrate_vn() - CkApstraBlueprint(terra)::swap_ct_vns(from_vn_id='BPB80Tuop2qUINeUZOU', to_vn_id='mTlYxQM-bvG1oP6mhZQ') patched: ct['id']='1604b264-fa4a-46ec-a47f-1d237b2c5a3f' attr={'tag_type': 'vlan_tagged', 'vn_node_id': 'BPB80Tuop2qUINeUZOU'} patched=<Response [204]> (cli.py:414)
2024-07-03 18:47:13,360 - INFO     - immigrate_vn() - VN vn2222:BPB80Tuop2qUINeUZOU deleted: deleted=<Response [204]> (cli.py:418)
2024-07-03 18:47:14,552 - INFO     - immigrate_vn() - VN vn2222:tzPJy0Myr5_b2pP9x1M created: created=<Response [201]> under RZ:vrf (cli.py:424)
2024-07-03 18:47:14,552 - INFO     - immigrate_vn() - Restoring CTs with new VN x-vn2222:mTlYxQM-bvG1oP6mhZQ (cli.py:427)
2024-07-03 18:47:16,414 - INFO     - immigrate_vn() - CkApstraBlueprint(terra)::swap_ct_vns(from_vn_id='mTlYxQM-bvG1oP6mhZQ', to_vn_id='tzPJy0Myr5_b2pP9x1M') patched: ct['id']='1604b264-fa4a-46ec-a47f-1d237b2c5a3f' attr={'tag_type': 'vlan_tagged', 'vn_node_id': 'mTlYxQM-bvG1oP6mhZQ'} patched=<Response [204]> (cli.py:429)
2024-07-03 18:47:17,538 - INFO     - immigrate_vn() - Temporary VN x-vn2222:mTlYxQM-bvG1oP6mhZQ deleted: deleted=<Response [204]> (cli.py:433)
2024-07-03 18:47:17,538 - INFO     - immigrate_vn() - Order completed: Order: self.target_vn='vn2222' self.target_vn_id='tzPJy0Myr5_b2pP9x1M' self.test_vn='x-vn2222' self.test_vn_id='mTlYxQM-bvG1oP6mhZQ' self.target_rz='vrf' self.terget_rz_id='S2WY6qMrf9J6cvoZfeY' (cli.py:435)
(.venv) ckim@ckim-mbp:ck-apstra-api % 
```


### code example
```python
@cli.command()
@click.option('--virtual-network', type=str, required=True, help='Subject Virtual Network name')
@click.option('--routing-zone', type=str, required=True, help='Destination Routing Zone name')
@click.option('--blueprint', type=str, required=True, help='Blueprint name')
@click.pass_context
def relocate_vn(ctx, blueprint: str, virtual_network: str, routing_zone: str):
    """
    Move a Virtual Network to the target Routing Zone

    The virtual network move involves deleting and recreating the virtual network in the target routing zone.
    To delete the virtual network, the associated CT should be taken care of. Either deassign and delete them and later do reverse.
    This CT handling trouble can be mitigated with a temporary VN to replace the original VN in the CT. Later, to be reversed later.

    """
from ck_apstra_api.apstra_session import CkApstraSession, prep_logging
    from ck_apstra_api.apstra_blueprint import CkApstraBlueprint

    from result import Ok, Err

    logger = prep_logging('INFO', 'relocate_vn()')
    logger.info(f"Took order {blueprint=} {virtual_network=} {routing_zone=}")

    NODE_NAME_RZ = 'rz'

    host_ip = ctx.obj['HOST_IP']
    host_port = ctx.obj['HOST_PORT']
    host_user = ctx.obj['HOST_USER']
    host_password = ctx.obj['HOST_PASSWORD']

    session = CkApstraSession(host_ip, host_port, host_user, host_password)
    bp = CkApstraBlueprint(session, blueprint)

    @dataclass
    class Order(object):
        target_vn: str = virtual_network
        target_vn_id: str = None
        target_vn_spec: dict = None
        test_vn: str = None
        test_vn_id: str = None
        test_vn_spec: dict = None
        target_rz: str = routing_zone
        terget_rz_id: str = None

        def summary(self):
            return f"Order: {self.target_vn=} {self.target_vn_id=} {self.test_vn=} {self.test_vn_id=} {self.target_rz=} {self.terget_rz_id=}"
    the_order = Order()

    # get the target_rz_id
    found_rz = bp.query(f"node('security_zone', name='{NODE_NAME_RZ}', label='{routing_zone}')").ok_value
    the_order.terget_rz_id = found_rz[0][NODE_NAME_RZ]['id']

    # get all the VNs
    found_vns_dict = bp.get_item('virtual-networks')['virtual_networks']

    # pick the target VN data
    target_vn_node = [vn for vn in found_vns_dict.values() if vn['label'] == virtual_network]    
    if len(target_vn_node) == 0:
        logger.error(f"Virtual Network {virtual_network} not found")
        return
    the_order.target_vn_spec = target_vn_node[0]
    the_order.target_vn_id = the_order.target_vn_spec['id']
    # check if the VN is already in the target RZ
    if the_order.target_vn_spec['security_zone_id'] == the_order.terget_rz_id:
        logger.warning(f"Virtual Network {virtual_network} already in the target Routing Zone {routing_zone}")
        return

    for res in bp.get_temp_vn(the_order.target_vn):
        if isinstance(res, dict):
            the_order.test_vn_spec = res
            the_order.test_vn_id = res['id']
            the_order.test_vn = res['label']
        else:
            logger.info(res)

    logger.info(f"Ready to relocate vn {virtual_network}: {the_order.summary()}")

    # replace CTs with test VN
    for res in bp.swap_ct_vns(the_order.target_vn_id, the_order.test_vn_id):
        logger.info(res)

    # delete the original VN
    deleted = bp.delete_item(f"virtual-networks/{the_order.target_vn_id}")
    logger.info(f"VN {the_order.target_vn}:{the_order.target_vn_id} deleted: {deleted=}")

    # create the original VN in the target RZ
    the_order.target_vn_spec['security_zone_id'] = the_order.terget_rz_id
    created = bp.post_item('virtual-networks', the_order.target_vn_spec)
    the_order.target_vn_id = created.json()['id']
    logger.info(f"VN {the_order.target_vn}:{the_order.target_vn_id} created: {created=} under RZ:{the_order.target_rz}")

    # restore the CTs
    logger.info(f"Restoring CTs with new VN {the_order.test_vn}:{the_order.test_vn_id}")
    for res in bp.swap_ct_vns(the_order.test_vn_id, the_order.target_vn_id):
        logger.info(res)

    # remove the temporary VN
    deleted = bp.delete_item(f"virtual-networks/{the_order.test_vn_id}")
    logger.info(f"Temporary VN {the_order.test_vn}:{the_order.test_vn_id} deleted: {deleted=}")

    logger.info(f"Order completed: {the_order.summary()}")
    session.logout()

```

## export device configurations

```
.venv) ckim@ckim-mbp:ck-apstra-api % ck-cli export-device-configs --help
Usage: ck-cli export-device-configs [OPTIONS]

  Export a device configurations into multiple files

  The folder for each device will be created with the device name.
  0_load_override_pristine.txt (if the device is managed)
  0_load_override_freeform.txt (if case of freeform) 1_load_merge_intended.txt
  2_load_merge_configlet.txt (if applicable) 3_load_set_configlet-set.txt (if
  applicable)

Options:
  --bp-name TEXT     Blueprint name
  --out-folder TEXT  Folder name to export
  --help             Show this message and exit.
(.venv) ckim@ckim-mbp:ck-apstra-api % 
(.venv) ckim@ckim-mbp:ck-apstra-api % ck-cli export-device-configs --bp-name dh --out-folder ~/Downloads/dev1
2024-07-17 19:02:23,828 - INFO     - export_device_configs() - bp_name='dh' out_folder='/Users/ckim/Downloads/dev1' (cli.py:280)
2024-07-17 19:02:23,952 - INFO     - export_device_configs() - system_label='dh_border2' (cli.py:301)
2024-07-17 19:02:24,501 - INFO     - export_device_configs() - write_to_file(): rendered.txt (cli.py:291)
2024-07-17 19:02:24,502 - INFO     - export_device_configs() - write_to_file(): 1_load_merge_intended.txt (cli.py:291)
2024-07-17 19:02:24,502 - INFO     - export_device_configs() - write_to_file(): 2_load_merge_configlet.txt (cli.py:291)
2024-07-17 19:02:24,503 - INFO     - export_device_configs() - system_label='spine1' (cli.py:301)
2024-07-17 19:02:24,715 - INFO     - export_device_configs() - write_to_file(): 0_load_override_pristine.txt (cli.py:291)
2024-07-17 19:02:25,173 - INFO     - export_device_configs() - write_to_file(): rendered.txt (cli.py:291)
2024-07-17 19:02:25,174 - INFO     - export_device_configs() - write_to_file(): 1_load_merge_intended.txt (cli.py:291)
2024-07-17 19:02:25,175 - INFO     - export_device_configs() - write_to_file(): 2_load_merge_configlet.txt (cli.py:291)
2024-07-17 19:02:25,175 - INFO     - export_device_configs() - system_label='spine2' (cli.py:301)
2024-07-17 19:02:25,654 - INFO     - export_device_configs() - write_to_file(): rendered.txt (cli.py:291)
2024-07-17 19:02:25,655 - INFO     - export_device_configs() - write_to_file(): 1_load_merge_intended.txt (cli.py:291)
2024-07-17 19:02:25,655 - INFO     - export_device_configs() - write_to_file(): 2_load_merge_configlet.txt (cli.py:291)
2024-07-17 19:02:25,656 - INFO     - export_device_configs() - system_label='dh_border1' (cli.py:301)
2024-07-17 19:02:25,868 - INFO     - export_device_configs() - write_to_file(): 0_load_override_pristine.txt (cli.py:291)
2024-07-17 19:02:26,414 - INFO     - export_device_configs() - write_to_file(): rendered.txt (cli.py:291)
2024-07-17 19:02:26,414 - INFO     - export_device_configs() - write_to_file(): 1_load_merge_intended.txt (cli.py:291)
2024-07-17 19:02:26,415 - INFO     - export_device_configs() - write_to_file(): 2_load_merge_configlet.txt (cli.py:291)
2024-07-17 19:02:26,415 - INFO     - export_device_configs() - write_to_file(): 3_load_set_configlet-set.txt (cli.py:291)
2024-07-17 19:02:26,415 - INFO     - export_device_configs() - system_label='terra-border1' (cli.py:301)
2024-07-17 19:02:26,533 - INFO     - export_device_configs() - system_label='terra-border2' (cli.py:301)
(.venv) ckim@ckim-mbp:ck-apstra-api % ls ~/Downloads/dev1/dh 
dh_border1    dh_border2    spine1        spine2        terra-border1 terra-border2
(.venv) ckim@ckim-mbp:ck-apstra-api % 
```


## list systems (WIP)

```
(.venv) ckim@ckim-mbp:ck-apstra-api % ck-cli export-systems --help       
Usage: ck-cli export-systems [OPTIONS]

  Export systems of a blueprint to a CSV file

  The CSV file will have below columns: system, asn, lo0, rack, device_profile

Options:
  --bp-name TEXT      Blueprint name
  --systems-csv TEXT  The CSV file path to create  [required]
  --help              Show this message and exit.
(.venv) ckim@ckim-mbp:ck-apstra-api % 
(.venv) ckim@ckim-mbp:ck-apstra-api % python src/ck_apstra_api/cli.py export-systems --systems-csv ~/Downloads/system.csv
2024-07-09 19:27:19,866 - INFO     - export_systems() - systems_csv_path='/Users/ckim/Downloads/system.csv' writing to /Users/ckim/Downloads/system.csv (cli.py:276)
(.venv) ckim@ckim-mbp:ck-apstra-api % 
```

## export blueprint
```
(.venv) ckim@ckim-mbp:ck-apstra-api % ck-cli export-blueprint --help                                      
Usage: ck-cli export-blueprint [OPTIONS]

  Export a blueprint into a json file The blueprint label -
  job_env.main_blueprint_name The json file - job_env.bp_json_file

Options:
  --bp-name TEXT    Blueprint name
  --json-file TEXT  Blueprint name
  --help            Show this message and exit.
(.venv) ckim@ckim-mbp:ck-apstra-api % 
(.venv) ckim@ckim-mbp:ck-apstra-api % ck-cli export-blueprint --json-file ~/Downloads/dh.json --bp-name dh 
2024-07-17 18:18:29,465 - INFO     - export_blueprint() - bp_name='dh' json_file='/Users/ckim/Downloads/dh.json' (cli.py:191)
(.venv) ckim@ckim-mbp:ck-apstra-api %
```


## import iplink ct
```
ck-apstra-api-py3.11ckim@ckim-mbp:ck-apstra-api % ck-cli import-iplink-ct --help
Usage: ck-cli import-iplink-ct [OPTIONS]

  Import IpLink CT from a CSV file

Options:
  --csv-in TEXT  Path to the CSV file for iplink CT
  --help         Show this message and exit.
ck-apstra-api-py3.11ckim@ckim-mbp:ck-apstra-api % 
```

[Example csv file](./tests/fixtures/iplink_ct_sample.csv)


## Misc

This repository is maintained on a best-effort basis. Comments and bug reports are encouraged and welcomed.
