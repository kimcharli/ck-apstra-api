
import logging
import pandas as pd
from math import isnan
from pathlib import Path
from pydantic import BaseModel, validator, StrictStr, field_validator
from typing import List, Optional, Any, TypeVar, Annotated
import numpy as np
import os

import click

from ck_apstra_api.apstra_session import prep_logging
from ck_apstra_api.cli import CkJobEnv

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
    untagged_vlan: Optional[int] = None
    tagged_vlans: Optional[List[int]] = None
    ct_names: Optional[str] = None
    comment: Optional[str] = None

    # convert to string in case an int is given
    @field_validator('gs_ifname1', 'gs_ifname2', 'gs_ifname3', 'gs_ifname4', mode='before')
    @classmethod
    def conver_to_string(cls, v):
        if isinstance(v, str):
            return v
        return str(v)

    @field_validator('tagged_vlans', mode='before')
    @classmethod
    def convert_to_list_of_int(cls, v):
        if v is None:
            return None
        if isinstance(v, int):
            return [v]
        return [ x.strip() for x in v.split(',')]

generic_system_data = {} # { blueprint: { generic_system: {....}}}


def process_row(row):
    blueprint_label = row['blueprint']
    blueprint_data = generic_system_data.setdefault(blueprint_label, {})
    system_label = row['system_label']
    system_data = blueprint_data.setdefault(system_label,[])
    # logging.debug(f"{generic_system_data}")
    pydantic_data = GenericSystemModel(**row)
    system_data.append(pydantic_data.model_dump())
    # logging.debug(f"{pydantic_data=}")


def read_generic_systems(input_file_path_string: str = None, sheet_name: str = 'generic_systems'):
    excel_file_sting = input_file_path_string or os.getenv('excel_input_file')
    input_file_path = Path(excel_file_sting) 
    df = pd.read_excel(input_file_path, sheet_name=sheet_name, header=[1])
    df = df.replace({np.nan: None})

    df.apply(process_row, axis=1)
    return generic_system_data

@click.command(name='read-generic-systems')
def click_read_generic_systems():
    job_env = CkJobEnv()
    generic_systems = read_generic_systems(job_env.excel_input_file, 'generic_systems')
    for bp_label, bp_data in generic_systems.items():
        logging.debug(f"{bp_label=}")
        for gs_label, gs_list in bp_data.items():
            logging.debug(f"{gs_label=}")
            for link in gs_list:
                logging.debug(f"{link=}")


def add_generic_systems(job_env: CkJobEnv, generic_systems: dict):
    """
    Add the generic systems to the Apstra server from the given generic systems data.

    Generic systems data:
    {
        <blueprint_label>: {
            <generic_system_label>: [
                {
                    "blueprint": "blueprint1",
                    "system_label": "generic_system1",
                    "is_external": false,
                    "speed": "10G",
                    "lag_mode": null,
                    "label1": "eth1",
                    "ifname1": "eth1",
                    "gs_ifname1": null,
                    "label2": null,
                    "ifname2": null,
                    "gs_ifname2": null,
                    "label3": null,
                    "ifname3": null,
                    "gs_ifname3": null,
                    "label4": null,
                    "ifname4": null,
                    "gs_ifname4": null,
                    "ct_names": null,
                    "comment": null
                }
            ]
        }
    }
    """

    pass

@click.command(name='add-generic-systems')
def click_add_generic_systems():
    job_env = CkJobEnv()
    generic_systems = read_generic_systems(job_env.excel_input_file, 'generic_systems')
    add_generic_systems(job_env, generic_systems)


if __name__ == "__main__":
    click_add_generic_systems()
    # input_file_path_string = "./tests/fixtures/ApstraProvisiongTemplate.xlsx"
    # sheet_name = "generic_systems"
    # log_level = logging.DEBUG
    # prep_logging(log_level)
    # for bp_label, bp_data in read_generic_systems(input_file_path_string, sheet_name).items():
    #     logging.debug(f"{bp_label=}")
    #     for gs_label, gs_list in bp_data.items():
    #         logging.debug(f"{gs_label=}")
    #         for link in gs_list:
    #             logging.debug(f"{link=}")

