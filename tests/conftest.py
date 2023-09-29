import pytest

from dotenv import load_dotenv
import os

from ck_apstra_api.apstra_session import CkApstraSession


class Data:
    apstra_host: str
    apstra_port: int
    apstra_user: str
    apstra_password: str
    apstra_session: str = None
    main_bp_name: str

    # tor_bp_name: str = 's5'

    def __init__(self):
        load_dotenv()
        Data.apstra_host = os.getenv('apstra_server_host')
        Data.apstra_port = os.getenv('apstra_server_port')
        Data.apstra_user = os.getenv('apstra_server_username')
        Data.apstra_password = os.getenv('apstra_server_password')
        Data.main_bp_name = os.getenv('main_blueprint')

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


# @pytest.fixture(scope="module")
# def tor_bp():
#     return Data().tor_bp_name


