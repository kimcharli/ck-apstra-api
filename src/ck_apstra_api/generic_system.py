
import logging
import pandas as pd
from math import isnan
from pathlib import Path
from pydantic import BaseModel, validator
from typing import List, Optional, Any, TypeVar, Annotated
import numpy as np
import os

import click

from ck_apstra_api.apstra_session import prep_logging


class GenericSystemModel(BaseModel):
    blueprint: str
    system_label: str
    is_external: Optional[bool] = False
    speed: str               # 10G 
    lag_mode: Optional[str]  # mandatory in case of multiple interfaces
    label1: str
    ifname1: str
    gs_ifname1: Optional[str]
    label2: Optional[str]
    ifname2: Optional[str]
    gs_ifname2: Optional[str]
    label3: Optional[str]
    ifname3: Optional[str]
    gs_ifname3: Optional[str]
    label4: Optional[str]
    ifname4: Optional[str]
    gs_ifname4: Optional[str]
    ct_names: Optional[str] = None
    comment: Optional[str] = None


generic_system_data = {} # { blueprint: { generic_system: {....}}}


def process_row(row):
    blueprint_label = row['blueprint']
    blueprint_data = generic_system_data.setdefault(blueprint_label, {})
    system_label = row['system_label']
    system_data = blueprint_data.setdefault(system_label,[])
    # logging.debug(f"{generic_system_data}")
    pydantic_data = GenericSystemModel(**row)
    system_data.append(pydantic_data.dict())
    # logging.debug(f"{pydantic_data=}")


@click.command()
def read_generic_system(input_file_path_string: str = None, sheet_name: str = 'generic_systems'):    
    logging.debug("Hello World!")
    excel_file_sting = input_file_path_string or os.getenv('excel_input_file')
    input_file_path = Path(excel_file_sting) 
    df = pd.read_excel(input_file_path, sheet_name=sheet_name, header=[1])
    df = df.replace({np.nan: None})

    df.apply(process_row, axis=1)
    return generic_system_data


if __name__ == "__main__":
    input_file_path_string = "./tests/fixtures/ApstraProvisiongTemplate.xlsx"
    sheet_name = "generic_systems"
    log_level = logging.DEBUG
    prep_logging(log_level)
    for bp_label, bp_data in read_generic_system(input_file_path_string, sheet_name).items():
        logging.debug(f"{bp_label=}")
        for gs_label, gs_list in bp_data.items():
            logging.debug(f"{gs_label=}")
            for link in gs_list:
                logging.debug(f"{link=}")

