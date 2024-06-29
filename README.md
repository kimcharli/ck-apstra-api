# ck-apstra-api

## prerequisit

python3.11 or higher

[ChangeLog](./ChangeLog.md)


## prepare venv

```
ckim@ckim-mbp:sandbox % mkdir test                                                                                                 
ckim@ckim-mbp:sandbox % cd test             
ckim@ckim-mbp:test % python -m venv .venv                      
ckim@ckim-mbp:test % source .venv/bin/activate
(.venv) ckim@ckim-mbp:test % pip install ck-apstra-api==0.4.0
...                                                                                             
(.venv) ckim@ckim-mbp:test % 
```

## help commands

```
(.venv) ck-apstra-apickim@ckim-mbp:ck-apstra-api % ck-cli          
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
  export-generic-system  Export generic systems to a CSV file
  import-generic-system  Import generic systems from a CSV file
(.venv) ck-apstra-apickim@ckim-mbp:ck-apstra-api % ck-cli --version
ck_apstra_api, 0.4.1
(.venv) ck-apstra-apickim@ckim-mbp:ck-apstra-api % 
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
(.venv) ck-apstra-apickim@ckim-mbp:ck-apstra-api % ck-cli --host-ip 10.85.192.45 --host-password admin import-generic-system --gs-csv-in ~/Downloads/gs_sample.csv
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
(.venv) ck-apstra-apickim@ckim-mbp:ck-apstra-api % 
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


## Misc

This repository is maintained on a best-effort basis. Comments and bug reports are encouraged and welcomed.
