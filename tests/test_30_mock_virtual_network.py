import pytest
import json

from ck_apstra_api import CkApstraBlueprint

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




