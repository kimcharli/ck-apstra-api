import logging
import pytest
import csv

from ck_apstra_api import add_generic_systems, GsCsvKeys

logger = logging.getLogger(__name__)

@pytest.fixture
def load_gs_csv_file(gs_csv) -> list[dict]:
    """Load CSV file and return a list of dictionaries."""
    data = []
    with open(f"tests/fixtures/{gs_csv}", 'r') as csvfile:
        csv_reader = csv.reader(csvfile)
        headers = next(csv_reader)  # Read the header row
        expected_headers = [header.value for header in GsCsvKeys]
        if headers != expected_headers:
            raise ValueError(
                "CSV header mismatch. Expected headers: "
                    + ', '.join(expected_headers))

        for row in csv_reader:
            data.append(dict(zip(headers, row)))
    # logger.info(f"Reading CSV file: {gs_csv=} {headers=} {data=}")
    return data

def test_21_generic_system(session, load_gs_csv_file):
    gs_rows = load_gs_csv_file
    for res in add_generic_systems(session, gs_rows):
        # logger.info(type(res))
        logger.info(res)
    assert True



