from dataclasses import dataclass
import dotenv

from ck_apstra_api import CkApstraSession, prep_logging
from ck_apstra_api import CkApstraBlueprint


# keep the common variables in a class
@dataclass
class CliVar:
    session: CkApstraSession = None
    blueprint: CkApstraBlueprint = None
    export_data: dict = None

    def __post_init__(self):
        self.export_data = {
            'blueprint': {}
        }

    def get_blueprint(self, bp_name, logger) -> CkApstraBlueprint:
        """ Get the blueprint object. If not found, return None """
        self.blueprint = CkApstraBlueprint(self.session, bp_name)
        if not self.blueprint.id:
            logger.error(f"Blueprint {bp_name} not found")
            return None
        logger.info(f"{bp_name=}, {self.blueprint.id=}")
        if self.blueprint.id:
            logger.info(f"Blueprint {bp_name} found")
            self.export_data['blueprint']['label'] = bp_name
            return self.blueprint
        else:
            logger.warning(f"Blueprint {bp_name} not found")
            return None


dotenv.load_dotenv()
cliVar = CliVar()

