# ck-apstra-api

## prerequisit

python3.11 or higher

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
(.venv) ckim@ckim-mbp:test % ck-cli --help
Usage: ck-cli [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  generic-system  Add generic systems from a CSV file
(.venv) ckim@ckim-mbp:test % 
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
(.venv) ckim@ckim-mbp:test % ck-cli generic-system 10.85.192.45 443 admin admin ~/Downloads/gs_sample.csv
2024-06-27 21:53:17,719 [INFO] host_ip='10.85.192.45' host_port='443' host_user='admin' host_password='admin' gs_csv='/Users/ckim/Downloads/gs_sample.csv'
2024-06-27 21:53:18,361 [INFO] add_generic_systems ServerBlueprint._bps={'terra': ServerBlueprint(blueprint='terra')}
2024-06-27 21:53:18,361 [INFO] ServerBlueprint:fetch_apstra() self.blueprint='terra'
2024-06-27 21:53:19,280 [INFO] LinkMember(server_1:xe-0/0/11:eth0)::fetch_apstra() done LinkMember(line='1', speed='10G', ifname='eth0', switch='server_1', switch_ifname='xe-0/0/11', tags_link=[], comment='', fetched_server_ifname='eth0', fetched_server_intf_id='rS-SAutij9BQu6URqOE', fetched_switch_id='2QKZLUzqCO0ZJ73Fb1I', fetched_switch_intf_id='8oBvQ83Dp_E2C0tS0Ec', fetched_tags_link=None, fetched_link_id='server_1<->single-home-1(link-000000001)[1]')
2024-06-27 21:53:19,417 [INFO] LinkGroup(____1)::fetch_apstra() done LinkGroup(ae='____1', lag_mode='', ct_names=['vn20'], tags_ae=['single'], fetched_ae_id='8oBvQ83Dp_E2C0tS0Ec', fetched_lag_mode=None, fetched_ct_names=['vn20'], fetched_tags=None)
2024-06-27 21:53:19,548 [INFO] text GenericSystem(single-home-1)::fetch_apstra() done GenericSystem(server='single-home-1', ext='', tags_server=['single'], gs_id='UjUiEGkxiadUVqE-bdg', fetched_server_tags=[])
2024-06-27 21:53:19,719 [INFO] LinkMember(server_1:xe-0/0/12:eth0)::fetch_apstra() done LinkMember(line='2', speed='10G', ifname='eth0', switch='server_1', switch_ifname='xe-0/0/12', tags_link=['forceup'], comment='', fetched_server_ifname='eth0', fetched_server_intf_id='VVew1ai0NSJ5hKwBj0I', fetched_switch_id='2QKZLUzqCO0ZJ73Fb1I', fetched_switch_intf_id='IJedVMPb15J9tbiwMHM', fetched_tags_link=None, fetched_link_id='server_1<->dual-home-1(link-000000001)[1]')
2024-06-27 21:53:19,719 [INFO] LinkMember(server_2:xe-0/0/12:eth1)::fetch_apstra() done LinkMember(line='3', speed='10G', ifname='eth1', switch='server_2', switch_ifname='xe-0/0/12', tags_link=[], comment='', fetched_server_ifname='eth1', fetched_server_intf_id='CNCswV3MMDbtLJJ5maE', fetched_switch_id='qCc9ps52vPppDp2b6rk', fetched_switch_intf_id='YkqFH8GaaEIQ9f7wGlw', fetched_tags_link=None, fetched_link_id='server_2<->dual-home-1(link-000000002)[1]')
2024-06-27 21:53:19,853 [INFO] LinkGroup(ae101)::fetch_apstra() done LinkGroup(ae='ae1', lag_mode='lacp_active', ct_names=['vn20', 'vn101'], tags_ae=['dual'], fetched_ae_id='k8_2_9LTrNxN1OQrYUs', fetched_lag_mode='lacp_active', fetched_ct_names=['vn101', 'vn20'], fetched_tags=None)
2024-06-27 21:53:20,015 [INFO] text GenericSystem(dual-home-1)::fetch_apstra() done GenericSystem(server='dual-home-1', ext='', tags_server=['dual'], gs_id='fo69Mrmi_JAfZfshYRM', fetched_server_tags=[])
2024-06-27 21:53:20,015 [INFO] add_generic_systems fetched ServerBlueprint._bps={'terra': ServerBlueprint(blueprint='terra')}
2024-06-27 21:53:20,015 [INFO] GenericSystem(single-home-1)::create() present. No need to create this. Skipping
2024-06-27 21:53:20,015 [INFO] GenericSystem(dual-home-1)::create() present. No need to create this. Skipping
2024-06-27 21:53:20,015 [INFO] add_generic_systems generic_systems added ServerBlueprint._bps={'terra': ServerBlueprint(blueprint='terra')}
2024-06-27 21:53:20,015 [INFO] ServerBlueprint:fetch_apstra() self.blueprint='terra'
2024-06-27 21:53:20,391 [INFO] LinkMember(server_1:xe-0/0/11:eth0)::fetch_apstra() done LinkMember(line='1', speed='10G', ifname='eth0', switch='server_1', switch_ifname='xe-0/0/11', tags_link=[], comment='', fetched_server_ifname='eth0', fetched_server_intf_id='rS-SAutij9BQu6URqOE', fetched_switch_id='2QKZLUzqCO0ZJ73Fb1I', fetched_switch_intf_id='8oBvQ83Dp_E2C0tS0Ec', fetched_tags_link=None, fetched_link_id='server_1<->single-home-1(link-000000001)[1]')
2024-06-27 21:53:20,525 [INFO] LinkGroup(____1)::fetch_apstra() done LinkGroup(ae='____1', lag_mode='', ct_names=['vn20'], tags_ae=['single'], fetched_ae_id='8oBvQ83Dp_E2C0tS0Ec', fetched_lag_mode=None, fetched_ct_names=['vn20'], fetched_tags=None)
2024-06-27 21:53:20,681 [INFO] text GenericSystem(single-home-1)::fetch_apstra() done GenericSystem(server='single-home-1', ext='', tags_server=['single'], gs_id='UjUiEGkxiadUVqE-bdg', fetched_server_tags=[])
2024-06-27 21:53:20,831 [INFO] LinkMember(server_1:xe-0/0/12:eth0)::fetch_apstra() done LinkMember(line='2', speed='10G', ifname='eth0', switch='server_1', switch_ifname='xe-0/0/12', tags_link=['forceup'], comment='', fetched_server_ifname='eth0', fetched_server_intf_id='VVew1ai0NSJ5hKwBj0I', fetched_switch_id='2QKZLUzqCO0ZJ73Fb1I', fetched_switch_intf_id='IJedVMPb15J9tbiwMHM', fetched_tags_link=None, fetched_link_id='server_1<->dual-home-1(link-000000001)[1]')
2024-06-27 21:53:20,831 [INFO] LinkMember(server_2:xe-0/0/12:eth1)::fetch_apstra() done LinkMember(line='3', speed='10G', ifname='eth1', switch='server_2', switch_ifname='xe-0/0/12', tags_link=[], comment='', fetched_server_ifname='eth1', fetched_server_intf_id='CNCswV3MMDbtLJJ5maE', fetched_switch_id='qCc9ps52vPppDp2b6rk', fetched_switch_intf_id='YkqFH8GaaEIQ9f7wGlw', fetched_tags_link=None, fetched_link_id='server_2<->dual-home-1(link-000000002)[1]')
2024-06-27 21:53:20,982 [INFO] LinkGroup(ae101)::fetch_apstra() done LinkGroup(ae='ae1', lag_mode='lacp_active', ct_names=['vn20', 'vn101'], tags_ae=['dual'], fetched_ae_id='k8_2_9LTrNxN1OQrYUs', fetched_lag_mode='lacp_active', fetched_ct_names=['vn101', 'vn20'], fetched_tags=None)
2024-06-27 21:53:21,126 [INFO] text GenericSystem(dual-home-1)::fetch_apstra() done GenericSystem(server='dual-home-1', ext='', tags_server=['dual'], gs_id='fo69Mrmi_JAfZfshYRM', fetched_server_tags=[])
2024-06-27 21:53:21,126 [INFO] add_generic_systems after generic system creation - fetched ServerBlueprint._bps={'terra': ServerBlueprint(blueprint='terra')}
2024-06-27 21:53:21,126 [INFO] LinkGroup(____1)::form_lacp() self.ae='____1' is not for lag. Skipping
2024-06-27 21:53:21,126 [INFO] LinkGroup(ae101)::form_lacp() self.ae='ae1' is already lag k8_2_9LTrNxN1OQrYUs. Skipping
2024-06-27 21:53:21,126 [INFO] add_generic_systems lacp formed ServerBlueprint._bps={'terra': ServerBlueprint(blueprint='terra')}
2024-06-27 21:53:21,126 [INFO] ServerBlueprint:fetch_apstra() self.blueprint='terra'
2024-06-27 21:53:21,499 [INFO] LinkMember(server_1:xe-0/0/11:eth0)::fetch_apstra() done LinkMember(line='1', speed='10G', ifname='eth0', switch='server_1', switch_ifname='xe-0/0/11', tags_link=[], comment='', fetched_server_ifname='eth0', fetched_server_intf_id='rS-SAutij9BQu6URqOE', fetched_switch_id='2QKZLUzqCO0ZJ73Fb1I', fetched_switch_intf_id='8oBvQ83Dp_E2C0tS0Ec', fetched_tags_link=None, fetched_link_id='server_1<->single-home-1(link-000000001)[1]')
2024-06-27 21:53:21,631 [INFO] LinkGroup(____1)::fetch_apstra() done LinkGroup(ae='____1', lag_mode='', ct_names=['vn20'], tags_ae=['single'], fetched_ae_id='8oBvQ83Dp_E2C0tS0Ec', fetched_lag_mode=None, fetched_ct_names=['vn20'], fetched_tags=None)
2024-06-27 21:53:21,760 [INFO] text GenericSystem(single-home-1)::fetch_apstra() done GenericSystem(server='single-home-1', ext='', tags_server=['single'], gs_id='UjUiEGkxiadUVqE-bdg', fetched_server_tags=[])
2024-06-27 21:53:21,898 [INFO] LinkMember(server_1:xe-0/0/12:eth0)::fetch_apstra() done LinkMember(line='2', speed='10G', ifname='eth0', switch='server_1', switch_ifname='xe-0/0/12', tags_link=['forceup'], comment='', fetched_server_ifname='eth0', fetched_server_intf_id='VVew1ai0NSJ5hKwBj0I', fetched_switch_id='2QKZLUzqCO0ZJ73Fb1I', fetched_switch_intf_id='IJedVMPb15J9tbiwMHM', fetched_tags_link=None, fetched_link_id='server_1<->dual-home-1(link-000000001)[1]')
2024-06-27 21:53:21,899 [INFO] LinkMember(server_2:xe-0/0/12:eth1)::fetch_apstra() done LinkMember(line='3', speed='10G', ifname='eth1', switch='server_2', switch_ifname='xe-0/0/12', tags_link=[], comment='', fetched_server_ifname='eth1', fetched_server_intf_id='CNCswV3MMDbtLJJ5maE', fetched_switch_id='qCc9ps52vPppDp2b6rk', fetched_switch_intf_id='YkqFH8GaaEIQ9f7wGlw', fetched_tags_link=None, fetched_link_id='server_2<->dual-home-1(link-000000002)[1]')
2024-06-27 21:53:22,032 [INFO] LinkGroup(ae101)::fetch_apstra() done LinkGroup(ae='ae1', lag_mode='lacp_active', ct_names=['vn20', 'vn101'], tags_ae=['dual'], fetched_ae_id='k8_2_9LTrNxN1OQrYUs', fetched_lag_mode='lacp_active', fetched_ct_names=['vn101', 'vn20'], fetched_tags=None)
2024-06-27 21:53:22,161 [INFO] text GenericSystem(dual-home-1)::fetch_apstra() done GenericSystem(server='dual-home-1', ext='', tags_server=['dual'], gs_id='fo69Mrmi_JAfZfshYRM', fetched_server_tags=[])
2024-06-27 21:53:22,161 [INFO] add_generic_systems after form lag - fetched ServerBlueprint._bps={'terra': ServerBlueprint(blueprint='terra')}
2024-06-27 21:53:22,161 [INFO] LinkGroup(____1)::rename_interfaces() self.ae='____1' rename_spec={'links': []}
2024-06-27 21:53:22,161 [INFO] LinkGroup(ae101)::rename_interfaces() self.ae='ae1' rename_spec={'links': []}
2024-06-27 21:53:22,162 [INFO] add_generic_systems interfaces renamed ServerBlueprint._bps={'terra': ServerBlueprint(blueprint='terra')}
2024-06-27 21:53:22,162 [INFO] GenericSystem(single-home-1) done - 0 vlans
2024-06-27 21:53:22,162 [INFO] GenericSystem(dual-home-1) done - 0 vlans
2024-06-27 21:53:22,162 [INFO] add_generic_systems vlans added ServerBlueprint._bps={'terra': ServerBlueprint(blueprint='terra')}
(.venv) ckim@ckim-mbp:test % 
```

### code example

Below is an example code to call add_generic_systems of this package.
```python
def generic_system(host_ip: str, host_port: str, host_user: str, host_password: str, gs_csv: str):
    """
    Add generic systems from a CSV file
    """
    from ck_apstra_api.generic_system import GsCsvKeys, add_generic_systems
    from ck_apstra_api.apstra_session import CkApstraSession
    from result import Ok, Err
    import logging

    logger = logging.getLogger('generic_system()')
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        )
    logger.info(f"{host_ip=} {host_port=} {host_user=} {host_password=} {gs_csv=}")

    session = CkApstraSession(host_ip, host_port, host_user, host_password)

    data = []
    with open(gs_csv, 'r') as csvfile:
        csv_reader = csv.reader(csvfile)
        headers = next(csv_reader)  # Read the header row
        expected_headers = [header.value for header in GsCsvKeys]
        if headers != expected_headers:
            raise ValueError("CSV header mismatch. Expected headers: " + ', '.join(expected_headers))

        for row in csv_reader:
            data.append(dict(zip(headers, row)))

    for res in add_generic_systems(session, data):
        if isinstance(res, Ok):
            logger.info(res.ok_value)
        elif isinstance(res, Err):
            logger.warning(res.err_value)
        else:
            logger.info(f"text {res}")

```


## Misc

This repository is maintained on a best-effort basis. Comments and bug reports are encouraged and welcomed.
