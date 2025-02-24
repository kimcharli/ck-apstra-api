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


# keep the common variables in a class
@dataclass
class CliVar:
    session: CkApstraSession = None
    blueprint: CkApstraBlueprint = None
    data_in_file: dict = None
    bp_in_file: dict = None

    file_path: str = None
    file_format: str = None
    file_folder: str = '.'  # default to current folder
    log_folder: str = '.'  # default to current folder
    file_name: str = None
    bp_name: str = None
    logger: Any = None


    def __post_init__(self):  # TODO: remove this
        self.data_in_file = {
            'blueprint': {}
        }

    def get_filepath(self):
        return os.path.join(self.file_folder, self.file_name)

    def update(self, **kwargs):
        '''Update the variables with the kwargs'''
        # TODO: caller process by caller=sys._getframe().f_code.co_name
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                self.logger.warning(f"Attribute {k} not found")

    def gen_logger(self, log_level: str, log_name):
        '''Generate the logger'''
        self.logger = prep_logging(log_level, 'CliVar::', self.log_folder)
        return prep_logging(log_level, log_name)

    def load_file(self, file_path, file_format):
        '''Load the file into self.data_in_file'''
        self.file_path = file_path
        self.file_format = file_format
        with open(file_path, 'r') as f:
            if file_format == 'json':
                self.data_in_file = json.load(f)
            elif file_format == 'yaml':
                self.data_in_file = yaml.load(f, yaml.SafeLoader)
            else:
                self.logger.error(f"File format {file_format} not supported")


    def get_blueprint(self, bp_name, logger) -> CkApstraBlueprint:
        """ Get the blueprint object. If not found, return None """
        if not bp_name:
            bp_name = self.bp_name
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

    def write_file(self, data):
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
            match file_extension:   # file extension
                case 'json':
                    return json.load(f)
                case 'yaml':
                    return yaml.safe_load(f)
                case 'yml':
                    return yaml.safe_load(f)
                case _:
                    # no decoding by default
                    return f.read()


dotenv.load_dotenv()
cliVar: CliVar = CliVar()

