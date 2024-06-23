import pytest
import csv
import logging
import os

logger = logging.getLogger(__name__)


from ck_apstra_api.apstra_session import CkApstraSession


class Data:
    apstra_host: str
    apstra_port: int
    apstra_user: str
    apstra_password: str
    apstra_session: str = None
    main_bp_name: str
    gs_cvs: str

    # tor_bp_name: str = 's5'

    def __init__(self):
        Data.apstra_host = '10.85.192.45'
        Data.apstra_port = '443'
        Data.apstra_user = 'admin'
        Data.apstra_password = 'admin'
        Data.main_bp_name = 'terra'
        Data.gs_cvs = 'gs_sample.csv'

        Data.apstra_session = CkApstraSession(
            Data.apstra_host,
            int(Data.apstra_port),
            Data.apstra_user,
            Data.apstra_password)
    

@pytest.fixture(scope="module")
def session():
    my_session = Data()
    return my_session.apstra_session


@pytest.fixture(scope="module")
def main_bp():
    return Data().main_bp_name

@pytest.fixture(scope="module")
def gs_csv():
    return Data().gs_cvs


# @pytest.fixture(scope="module")
# def tor_bp():
#     return Data().tor_bp_name

@pytest.fixture
def load_gs_csv_file(gs_csv):
    data = []
    with open(f"tests/fixtures/{gs_csv}", 'r') as csvfile:
        csv_reader = csv.reader(csvfile)
        headers = next(csv_reader)  # Read the header row

        # Check if the headers match the expected ones
        expected_headers = [
            'blueprint', 'server', 'ext', 'tags_server', 'ae', 'lag_mode',
            'ct_names', 'tags_ae', 'speed', 'ifname', 'switch', 'switch_ifname',
            'tags_link', 'comment'
        ]
        if headers != expected_headers:
            raise ValueError("CSV header mismatch. Expected headers: " + ', '.join(expected_headers))

        for row in csv_reader:
            data.append(dict(zip(headers, row)))
    # logger.info(f"Reading CSV file: {gs_csv=} {headers=} {data=}")
    return data

