from dataclasses import dataclass, asdict
from typing import Any, Dict
import os
import json
import yaml
import dotenv
from enum import StrEnum

from ck_apstra_api import CkApstraSession, CkApstraBlueprint, prep_logging, DataInFile

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

@dataclass
class CliVar:
    session: CkApstraSession = None
    blueprint: CkApstraBlueprint = None
    # data_in_file: dict = None
    data_in_file: DataInFile = None
    # bp_in_file: dict = None
    file_path: str = None
    file_format: str = None
    logger: Any = None

    def __post_init__(self):
        # self.data_in_file = {
        #     'blueprint': {}
        # }
        # first prep_logging is to set the logging file
        self.logger = prep_logging('DEBUG', 'CliVar', os.getenv(EnvEnum.FILE_FOLDER, '.'))
        self.data_in_file = DataInFile()

    def get_default_file_path(self, file_folder, file_format):
        '''The file name is the blueprint name, or 'apstra'''
        file_name = f"{getattr(self.blueprint, 'label', 'apstra')}.{file_format}"
        return os.path.expanduser(f"{file_folder}/{file_name}")

    def import_file(self, file_folder, file_format):
        '''import the data_in_file from a file'''
        file_path = self.get_default_file_path(file_folder, file_format)
        self.logger.info(f"Importing file {file_path}")
        with open(file_path, 'r') as f:
            if'file_format' == 'json':
                self.data_in_file = json.load(f)
            else:
                self.data_in_file = yaml.load(f, yaml.SafeLoader)
        if self.blueprint.label:
            self.bp_in_file = self.data_in_file['blueprint'].setdefault(self.blueprint.label, {})

    def export_file(self, file_folder, file_format):
        '''export the data_in_file to a file'''
        file_folder = file_folder or os.getenv(EnvEnum.FILE_FOLDER, '.')
        file_format = file_format or os.getenv(EnvEnum.FILE_FORMAT, 'yaml')
        file_path = self.get_default_file_path(file_folder, file_format)
        self.logger.info(f"Exporting to {file_path}")
        with open(file_path, 'w') as f:
            if'file_format' == 'json':
                f.write(json.dumps(cliVar.data_in_file.as_dict(), indent=2))
            else:
                f.write(yaml.dump(cliVar.data_in_file.as_dict()))

    def get_blueprint(self, bp_name) -> CkApstraBlueprint:
        """ Get the blueprint object. If not found, return None """
        self.blueprint = self.data_in_file.get_blueprint(self.session, bp_name)
        # self.logger = prep_logging('DEBUG', f"CliVar(bp={bp_name})")
        # self.blueprint = CkApstraBlueprint(self.session, bp_name)
        # if not self.blueprint.id:
        #     self.logger.error(f"Blueprint {bp_name} not found")
        #     return None
        # breakpoint()
        self.logger.info(f"{bp_name=}, {self.data_in_file.bp_data.id=}")
        if self.data_in_file.bp_data.id:
            self.logger.info(f"Blueprint {bp_name} found")
            # # set the bp_in_file to the blueprint data in th           
            # self.bp_in_file = self.data_in_file.blueprint[bp_name] = BpInFile()
            self.bp_in_file = self.data_in_file.bp_in_file
            return self.blueprint
        else:
            self.logger.warning(f"Blueprint {bp_name} not found")
            return None

dotenv.load_dotenv()
cliVar = CliVar()

