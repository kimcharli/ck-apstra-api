from dataclasses import dataclass
from typing import Any
import os
import json
import yaml
import dotenv
from enum import StrEnum

from ck_apstra_api import CkApstraSession, prep_logging
from ck_apstra_api import CkApstraBlueprint


class EnvEnum(StrEnum):
    '''Define the environment variables'''
    HOST_IP = 'HOST_IP'
    HOST_PORT = 'HOST_PORT'
    HOST_USER = 'HOST_USER'
    HOST_PASSWORD = 'HOST_PASSWORD'
    OUT_FOLDER = 'OUT_FOLDER'
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
    logger: Any = None

    def __post_init__(self):
        self.data_in_file = {
            'blueprint': {}
        }
        # first prep_logging is to set the logging file
        self.logger = prep_logging('DEBUG', 'CliVar', out_folder=os.getenv(EnvEnum.OUT_FOLDER, '.'))

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
        file_path = self.get_default_file_path(file_folder, file_format)
        self.logger.info(f"Exporting to {file_path}")
        with open(file_path, 'w') as f:
            if'file_format' == 'json':
                f.write(json.dumps(cliVar.data_in_file, indent=2))
            else:
                f.write(yaml.dump(cliVar.data_in_file))


    def get_blueprint(self, bp_name) -> CkApstraBlueprint:
        """ Get the blueprint object. If not found, return None """
        self.logger = prep_logging('DEBUG', f"CliVar(bp={bp_name})")
        self.blueprint = CkApstraBlueprint(self.session, bp_name)
        if not self.blueprint.id:
            self.logger.error(f"Blueprint {bp_name} not found")
            return None
        self.logger.info(f"{bp_name=}, {self.blueprint.id=}")
        if self.blueprint.id:
            self.logger.info(f"Blueprint {bp_name} found")
            # set the bp_in_file to the blueprint data in the file if it exists
            self.bp_in_file = self.data_in_file['blueprint'].setdefault(bp_name, {})
            return self.blueprint
        else:
            self.logger.warning(f"Blueprint {bp_name} not found")
            return None

dotenv.load_dotenv()
cliVar = CliVar()

