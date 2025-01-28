from dataclasses import dataclass, asdict
from typing import Any, Dict
import os
import json
import yaml
from enum import StrEnum
from dotenv import load_dotenv

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
    _session: CkApstraSession = None
    host_ip: str = None
    host_port: int = None
    host_user: str = None
    host_password: str = None
    blueprint: CkApstraBlueprint = None  # get from get_blueprint
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
        self.file_folder = None
        self.bp_name = None

    @property
    def session(self):
        if not self._session:
            self._session = CkApstraSession(self.host_ip, self.host_port, self.host_user, self.host_password)
        return self._session

    def update(self, **kwargs):
        '''Update the variables with the kwargs'''
        self.logger.info(f"Updating {kwargs}")
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                self.logger.warning(f"Attribute {k} not found")

    def get_default_file_path(self):
        '''The file name is the blueprint name, or 'apstra'''
        file_folder = self.file_folder or os.getenv(EnvEnum.FILE_FOLDER, '.')
        file_format = self.file_format = self.file_format or os.getenv(EnvEnum.FILE_FORMAT, 'yaml')
        file_name = f"{getattr(self.blueprint, 'label', 'apstra')}.{file_format}"
        return os.path.expanduser(f"{file_folder}/{file_name}")

    def import_file(self):
        '''import the data_in_file from a file'''
        file_path = self.get_default_file_path()
        self.logger.info(f"Importing file {file_path}")
        with open(file_path, 'r') as f:
            if self.file_format == 'json':
                self.data_in_file = json.load(f)
            else:
                self.data_in_file = yaml.load(f, yaml.SafeLoader)
        if self.blueprint.label:
            self.bp_in_file = self.data_in_file['blueprint'].setdefault(self.blueprint.label, {})

    def dump(self):
        '''dump the data_in_file to a file'''
        dump_data = self.blueprint.dump()
        # file_folder = self.file_folder or os.getenv(EnvEnum.FILE_FOLDER, '.')
        # file_format = self.file_format or os.getenv(EnvEnum.FILE_FORMAT, 'yaml')
        # file_path = self.get_default_file_path(file_folder, file_format)
        file_path = self.get_default_file_path()
        self.logger.info(f"Exporting to {file_path}")
        with open(file_path, 'w') as f:
            if self.file_format == 'json':
                f.write(json.dumps(dump_data, indent=2))
            else:
                f.write(yaml.dump(dump_data))

    def export_file(self):
        '''export the data_in_file to a file'''
        # file_folder = self.file_folder or os.getenv(EnvEnum.FILE_FOLDER, '.')
        # file_format = self.file_format or os.getenv(EnvEnum.FILE_FORMAT, 'yaml')
        # file_path = self.get_default_file_path(file_folder, file_format)
        file_path = self.get_default_file_path()
        self.logger.info(f"Exporting to {file_path}")
        with open(file_path, 'w') as f:
            if self.file_format == 'json':
                f.write(json.dumps(asdict(self.data_in_file), indent=2))
            else:
                f.write(yaml.dump(asdict(self.data_in_file)))

    def get_blueprint(self) -> CkApstraBlueprint:
        """ Get the blueprint object. If not found, return None """
        if not self.session:
            return None
        self.blueprint = self.data_in_file.get_blueprint(self.session, self.bp_name)
        # self.logger = prep_logging('DEBUG', f"CliVar(bp={bp_name})")
        # self.blueprint = CkApstraBlueprint(self.session, bp_name)
        # if not self.blueprint.id:
        #     self.logger.error(f"Blueprint {bp_name} not found")
        #     return None
        # breakpoint()
        self.logger.info(f"{self.bp_name=}, {self.blueprint.id=}")
        if self.blueprint.id:
            self.logger.info(f"Blueprint {self.bp_name} found")
            # # set the bp_in_file to the blueprint data in th           
            # self.bp_in_file = self.data_in_file.blueprint[bp_name] = BpInFile()
            self.bp_in_file = self.data_in_file.bp_in_file
            return self.blueprint
        else:
            self.logger.warning(f"Blueprint {self.bp_name} not found")
            return None

# should be here to be able to use the env variables in click options
load_dotenv()
cliVar = CliVar()
