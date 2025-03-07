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
    LOG_FOLDER = 'LOG_FOLDER'
    FILE_NAME = 'FILE_NAME'
    FILE_FORMAT = 'FILE_FORMAT'
    BP_NAME = 'BP_NAME'
    JSON_FILE = 'JSON_FILE'

# Keep the common variables in a class
@dataclass
class CliVar:
    session: CkApstraSession = None
    blueprint: CkApstraBlueprint = None
    data_in_file: dict = None
    bp_in_file: dict = None

    file_path: str = None
    file_format: str = None
    file_folder: str = '.'  # Default to current folder
    log_folder: str = '.'  # Default to current folder
    file_name: str = None
    bp_name: str = None
    logger: Any = None

    def __post_init__(self):
        '''Initialize data_in_file with default structure'''
        self.data_in_file = {
            'blueprint': {}
        }

    def get_filepath(self) -> str:
        '''Construct the full file path'''
        return os.path.join(self.file_folder, self.file_name)

    def update(self, **kwargs):
        '''Update the variables with the kwargs'''
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                self.logger.warning(f"Attribute {k} not found")

    def gen_logger(self, log_level: str, log_name: str):
        '''Generate the logger'''
        self.logger = prep_logging(log_level, 'CliVar::', self.log_folder)
        return prep_logging(log_level, log_name)

    def load_file(self, file_path: str, file_format: str):
        '''Load the file into self.data_in_file'''
        self.file_path = file_path
        self.file_format = file_format
        with open(file_path, 'r') as f:
            if file_format == 'json':
                self.data_in_file = json.load(f)
            elif file_format == 'yaml':
                self.data_in_file = yaml.safe_load(f)
            else:
                self.logger.error(f"File format {file_format} not supported")

    def get_blueprint(self, bp_name: str, logger: Any) -> CkApstraBlueprint:
        '''Get the blueprint object. If not found, return None'''
        if not bp_name:
            bp_name = self.bp_name
        self.blueprint = CkApstraBlueprint(self.session, bp_name)
        if not self.blueprint.id:
            logger.error(f"Blueprint {bp_name} not found")
            return None
        logger.info(f"{bp_name=}, {self.blueprint.id=}")
        self.bp_in_file = self.data_in_file['blueprint'].setdefault(bp_name, {})
        return self.blueprint

    def write_file(self, data: str):
        '''Write the data to the file'''
        file_path = self.get_filepath()
        with open(file_path, 'w') as f:
            f.write(data)
        self.logger.info(f"File written to {file_path}")

    def read_file(self):
        '''Read the data from the file and decode based on the file format'''
        file_path = self.get_filepath()
        file_extension = file_path.split('.')[-1]
        self.logger.info(f"Reading file {file_path}, {file_extension=}")
        with open(file_path, 'r') as f:
            match file_extension:
                case 'json':
                    return json.load(f)
                case 'yaml' | 'yml':
                    return yaml.safe_load(f)
                case _:
                    return f.read()

# Load environment variables from .env file
dotenv.load_dotenv()
cliVar: CliVar = CliVar()

