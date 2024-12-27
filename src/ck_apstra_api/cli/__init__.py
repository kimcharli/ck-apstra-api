from dataclasses import dataclass
import json
import yaml
import dotenv

from ck_apstra_api import CkApstraSession, prep_logging
from ck_apstra_api import CkApstraBlueprint


# keep the common variables in a class
@dataclass
class CliVar:
    session: CkApstraSession = None
    blueprint: CkApstraBlueprint = None
    data_in_file: dict = None
    bp_in_file: dict = None

    def __post_init__(self):
        self.data_in_file = {
            'blueprint': {}
        }

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

