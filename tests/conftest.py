import pytest

from ck_apstra_api.apstra_session import CkApstraSession

class Data:
    apstra_host: str = '10.85.192.50'  # 4.1.2
    apstra_port: int = 443
    apstra_user: str = 'admin'
    apstra_password: str = 'zaq1@WSXcde3$RFV'
    apstra_session: str = None

    main_bp_name: str = 'terra'
    tor_bp_name: str = 's5'

    def __init__(self):
        Data.apstra_session = CkApstraSession(
            Data.apstra_host, 
            Data.apstra_port, 
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
def tor_bp():
    return Data().tor_bp_name



