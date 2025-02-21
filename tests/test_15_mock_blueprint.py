import pytest
import json

from ck_apstra_api.apstra_blueprint import CkApstraBlueprint

@pytest.fixture
def clear_mock_bp(session, mock_bp_name) -> list[dict]:
    bp = CkApstraBlueprint(session, mock_bp_name)
    if bp:
        bp.delete_self()


def test_14_mock_blueprint_pre_cleanup(session, mock_bp_name):
    bp = CkApstraBlueprint(session, mock_bp_name)
    if bp:
        bp.delete_self()
    assert True

def test_15_mock_blueprint(session, mock_bp_name, mock_bp_in_path):
    # uv run ck-cli import-blueprint-json --bp-name _mock --json-file tests/fixtures/mock-blueprint-input.json
    with open(mock_bp_in_path, 'r') as f:
        mock_bp_data = f.read()
    mock_bp_dict = json.loads(mock_bp_data)
    mock_bp_id = session.create_blueprint_json(mock_bp_name, mock_bp_dict)
    # TODO: check the id string or status
    assert mock_bp_id is not None



