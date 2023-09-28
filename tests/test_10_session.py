#from ck_apstra_api.apstra_session import CkApstraSession

# def test_10_session(get_session):
#     get_session.print_token()


def test_10_session(session):
    session.print_token()
    assert True
