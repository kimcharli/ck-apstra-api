import pytest
import json
import yaml
from ck_apstra_api import CkApstraBlueprint
from result import Err, Ok


@pytest.fixture
def mock_bp(session, mock_bp_name) -> CkApstraBlueprint:
    mock_bp = CkApstraBlueprint(session, mock_bp_name)
    return mock_bp


@pytest.fixture
def mock_vn_csv_data(mock_bp, mock_vn_in_csv_file):
    with open(mock_vn_in_csv_file, 'r') as f:
        mock_vn_data = f.read()
    return mock_vn_data


def test_30_mock_import_virtual_network_csv(session, mock_bp, mock_vn_csv_data):
    # uv run ck-cli --file-folder tests/fixtures import-virtual-network-csv --bp-name _mock --file-name mock-vn-input.csv 
    patched = mock_bp.patch_virtual_networks_csv_bulk(mock_vn_csv_data)
    print(f"patched: {patched}, {patched.text}")
    assert patched.status_code == 202


def test_31_add_single_vlan_cts(session, mock_sngle_vlan_cts_yaml_file):
    # uv run ck-cli add-single-vlan-cts
    with open(mock_sngle_vlan_cts_yaml_file, 'r') as f:
        mock_data = yaml.safe_load(f)
    mock_bp = CkApstraBlueprint(session, mock_data['blueprint'])
    tagged_ct_name_format = mock_data['tagged_ct_name_format']
    untagged_ct_name_format = mock_data['untagged_ct_name_format']
    vni_base = mock_data['vni_base']
    tagged_vlan_ids = mock_data['tagged_vlan_ids']
    untagged_vlan_ids = mock_data['untagged_vlan_ids']

    print(f"tagged_vlan_ids to add {tagged_vlan_ids}")
    for vlan_id in mock_data['tagged_vlan_ids']:
        istagged = True
        ct_label = f"{tagged_ct_name_format.format(vlan_id=vlan_id)}"
        print(f"tagged {vlan_id=}, name = {ct_label}")
        for res in mock_bp.add_single_vlan_ct(vlan_id + vni_base, vlan_id, is_tagged=istagged, ct_label=ct_label):
            if isinstance(res, Err):
                print(f"{res.err_value}")
            else:
                print(f"{res.ok_value}")
    print("")
    print(f"untagged_vlan_ids to add {untagged_vlan_ids}")
    for vlan_id in mock_data['untagged_vlan_ids']:
        is_tagged = False
        ct_label = f"{untagged_ct_name_format.format(vlan_id=vlan_id)}"
        print(f"tagged {vlan_id=}, name = {ct_label}")
        for res in mock_bp.add_single_vlan_ct(vlan_id + vni_base, vlan_id, is_tagged=is_tagged, ct_label=ct_label):
            if isinstance(res, Err):
                print(f"{res.err_value}")
                break
            else:
                print(f"{res.ok_value}")



