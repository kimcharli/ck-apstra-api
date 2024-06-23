import logging

from ck_apstra_api.apstra_blueprint import CkApstraBlueprint
from ck_apstra_api.generic_system import add_generic_systems

logger = logging.getLogger(__name__)


def test_21_generic_system(session, load_gs_csv_file):
    gs_rows = load_gs_csv_file
    for res in add_generic_systems(session, gs_rows):
        # logger.info(type(res))
        logger.info(res)
    assert True



