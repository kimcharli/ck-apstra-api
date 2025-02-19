from dataclasses import dataclass
from typing import Any
import json
import yaml
import dotenv
from enum import StrEnum
import os


from ck_apstra_api import CkApstraSession, prep_logging, CkApstraBlueprint


class EnvEnum(StrEnum):
    '''Define the environment variables'''
    HOST_IP = 'HOST_IP'
    HOST_PORT = 'HOST_PORT'
    HOST_USER = 'HOST_USER'
    HOST_PASSWORD = 'HOST_PASSWORD'
    FILE_FOLDER = 'FILE_FOLDER'
    FILE_FORMAT = 'FILE_FORMAT'
    BP_NAME = 'BP_NAME'
    JSON_FILE = 'JSON_FILE'


# keep the common variables in a class
@dataclass
class CliVar:
    session: CkApstraSession = None
    blueprint: CkApstraBlueprint = None
    data_in_file: dict = None
    bp_in_file: dict = None

    file_path: str = None
    file_format: str = None
    file_folder: str = None
    bp_name: str = None
    logger: Any = None


    def __post_init__(self):
        self.data_in_file = {
            'blueprint': {}
        }
        self.logger = prep_logging('DEBUG', 'CliVar::')

    def update(self, **kwargs):
        '''Update the variables with the kwargs'''
        self.logger.info(f"Updating {kwargs}")
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                self.logger.warning(f"Attribute {k} not found")

    def load_file(self, file_path, file_format):
        with open(file_path, 'r') as f:
            if'file_format' == 'json':
                self.data_in_file = json.load(f)
            else:
                self.data_in_file = yaml.load(f, yaml.SafeLoader)

    def get_blueprint(self, bp_name, logger) -> CkApstraBlueprint:
        """ Get the blueprint object. If not found, return None """
        self.blueprint = CkApstraBlueprint(self.session, bp_name)
        if not self.blueprint.id:
            logger.error(f"Blueprint {bp_name} not found")
            return None
        logger.info(f"{bp_name=}, {self.blueprint.id=}")
        if self.blueprint.id:
            logger.info(f"Blueprint {bp_name} found")
            # set the bp_in_file to the blueprint data in the file if it exists
            self.bp_in_file = self.data_in_file['blueprint'].setdefault(bp_name, {})
            return self.blueprint
        else:
            logger.warning(f"Blueprint {bp_name} not found")
            return None


dotenv.load_dotenv()
cliVar = CliVar()

