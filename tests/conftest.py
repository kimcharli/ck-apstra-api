import pytest
import logging
from ck_apstra_api import CkApstraSession

logger = logging.getLogger(__name__)

class Data:
    apstra_host: str
    apstra_port: int
    apstra_user: str
    apstra_password: str
    apstra_session: str = None
    main_bp_name: str
    gs_cvs: str
    mock_bp_name: str = '_mock'
    bp_input_json_file: str = 'mock-blueprint-input.json'
    bp_output_json_file: str = 'mock-blueprint-output.json'

    def __init__(self):
        Data.apstra_host = '10.85.192.53'
        Data.apstra_port = '443'
        Data.apstra_user = 'admin'
        Data.apstra_password = 'admin'
        Data.main_bp_name = 'terra'
        Data.gs_cvs = 'gs_sample.csv'
        Data.mock_bp_name = '_mock'
        Data.mock_bp_in_file = 'mock-blueprint-input.json'
        Data.mock_bp_out_file = 'mock-blueprint-output.json'
        Data.mock_vn_in_csv_file = 'mock-vn-input.csv'
        Data.mock_sngle_vlan_cts_yaml_file = 'mock-vlan-cts.yaml'

        Data.apstra_session = CkApstraSession(
            Data.apstra_host,
            int(Data.apstra_port),
            Data.apstra_user,
            Data.apstra_password)

@pytest.fixture(scope="module")
def session():
    """Fixture to create and return an Apstra session."""
    my_session = Data()
    return my_session.apstra_session

@pytest.fixture(scope="module")
def main_bp():
    """Fixture to return the main blueprint name."""
    return Data().main_bp_name

@pytest.fixture(scope="module")
def gs_csv():
    """Fixture to return the GS CSV file name."""
    return Data().gs_cvs

@pytest.fixture(scope="module")
def mock_bp_name():
    """Fixture to return the mock blueprint name."""
    return Data().mock_bp_name

@pytest.fixture(scope="module")
def mock_bp_in_file():
    """Fixture to return the mock blueprint input file name."""
    return Data().mock_bp_in_file

@pytest.fixture(scope="module")
def mock_bp_out_file():
    """Fixture to return the mock blueprint output file name."""
    return Data().mock_bp_out_file

@pytest.fixture(scope="module")
def mock_bp_in_path():
    """Fixture to return the path to the mock blueprint input file."""
    return f'tests/fixtures/{Data().mock_bp_in_file}'

@pytest.fixture(scope="module")
def mock_vn_in_csv_file():
    """Fixture to return the path to the mock VN input CSV file."""
    return f'tests/fixtures/{Data().mock_vn_in_csv_file}'

@pytest.fixture(scope="module")
def mock_sngle_vlan_cts_yaml_file():
    """Fixture to return the path to the mock single VLAN CTS YAML file."""
    return f'tests/fixtures/{Data().mock_sngle_vlan_cts_yaml_file}'

# Uncomment and use this fixture if needed
# @pytest.fixture(scope="module")
# def tor_bp():
#     """Fixture to return the TOR blueprint name."""
#     return Data().tor_bp_name


