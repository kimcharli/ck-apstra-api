import logging
import pytest
import csv
from result import Ok, Err

from ck_apstra_api import add_generic_systems, GsCsvKeys

logger = logging.getLogger(__name__)

@pytest.fixture
def load_gs_csv_file(gs_csv) -> list[dict]:
    """Load CSV file and return a list of dictionaries."""
    links_to_add = []
    with open(f"tests/fixtures/{gs_csv}", 'r') as csvfile:
        csv_reader = csv.DictReader(csvfile)        
        # headers = next(csv_reader)  # Read the header row
        headers = csv_reader.fieldnames      # Read the header row
        expected_headers = [header.value for header in GsCsvKeys]
        if sorted(headers) != sorted(expected_headers):
            raise ValueError(
                f"CSV header mismatch. Expected headers ({len(expected_headers)}): "
                    + ', '.join(expected_headers) + f', Input headers ({len(headers)}) : ' + ', '.join(headers))

        for row in csv_reader:
            links_to_add.append(row)
    # logger.info(f"Reading CSV file: {gs_csv=} {headers=} {data=}")
    return links_to_add

def test_21_generic_system(session, load_gs_csv_file):
    # uv run ck-cli import-generic-system --gs-csv-in tests/fixtures/gs_sample.csv
    # logger.info(f"######## {load_gs_csv_file=}")
    for res in add_generic_systems(session, load_gs_csv_file):
        if isinstance(res, Ok):
            print(res.ok_value)
        elif isinstance(res, Err):
            print(res.err_value)
        else:
            print(res)
    assert True

