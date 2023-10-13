#!/usr/bin/env python3
import requests
import urllib3
import logging
import time
from datetime import datetime


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s %(levelname)8s %(name)s:%(funcName)s() - %(message)s (%(filename)s:%(lineno)d)"
    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def prep_logging(log_level: str = 'INFO'):
    '''Configure logging options'''
    timestamp = datetime.now().strftime("%Y%m%d-%H:%H:%S")
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.getLevelName(log_level))
    ch.setFormatter(CustomFormatter())
    root.addHandler(ch)


# https client session to Apstra Controller
class CkApstraSession:

    def __init__(self, 
                 host: str, 
                 port: int, 
                 username: str, 
                 password: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.token = None
        self.ssl_verify = False
        self.logger = logging.getLogger('CkApstraSession')

        self.session = requests.Session()
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.session.verify = False
        self.session.headers.update({'Content-Type': "application/json"})
        self.url_prefix = f"https://{self.host}:{self.port}/api"

        self.login()

        self.device_profile_cache = {}  # { device_profile_id: data }

    def login(self) -> None:
        """
        Log in to the Apstra controller.
        """
        url = f"{self.url_prefix}/user/login"
        payload = {
            "username": self.username,
            "password": self.password
        }
        response = self.session.post(url, json=payload)
        # print(f"{response.content=}")
        self.token = response.json()["token"]
        self.session.headers.update({'AuthToken': self.token})

    def get_device_profile(self, device_profile_name: str = None) -> dict:
        """
        Get the device profile with the specified name.

        Args:
            name: The name of the device profile.

        Returns:
            The device profile, or None if the device profile does not exist.
        """
        if device_profile_name is None:
            self.logger.warning("name is None")
            return None
        if device_profile_name not in self.device_profile_cache:
            # url = f"{self.url_prefix}/device-profiles"
            device_profiles = self.get_items('device-profiles')['items']
            self.device_profile_cache[device_profile_name] = [x for x in device_profiles if x['id'] == device_profile_name][0]
        return self.device_profile_cache[device_profile_name]

    def get_logical_device(self, id: int) -> dict:
        """
        Get the logical device with the specified ID.

        Args:
            id: The ID of the logical device.

        Returns:
            The logical device, or None if the logical device does not exist.
        """
        # url = f"{self.url_prefix}/design/logical-devices/{id}"
        return self.get_items(f"design/logical-devices/{id}")

    def get_items(self, url: str) -> dict:
        """
        Get the items from the url.

        Args:
            The url under /api

        Returns:
            The items
        """
        url = f"{self.url_prefix}/{url}"
        # self.logger.debug(f"{url=}")
        return self.session.get(url).json()

    def patch_item(self, url: str, spec: dict) -> dict:
        """
        Patch an items.

        Args:
            The url under /api/
            The patch spec

        Returns:
            The return
        """
        url = f"{self.url_prefix}/{url}"
        self.logger.debug(f"patch_item({url}, {spec})")
        return self.session.patch(url, json=spec).json()

    def patch_throttled(self, url: str, spec: dict, params: None) -> dict:
        """
        """
        throttle_seconds = 10
        patched = self.session.patch(url, json=spec, params=params)
        try:
            while True:
                # http 429 too many requests
                if patched.status_code != 429:
                    break
                self.logger.info(f"sleeping {throttle_seconds} seconds due to: {patched.text}")
                time.sleep(throttle_seconds)
                patched = self.session.patch(url, json=spec, params=params)
                if patched.content:
                    return patched.json()
                else:
                    return None
            if patched.content:
                return patched.json()
            else:
                return None
        except Exception as e:
            self.logger.error(f"{spec=}, {patched.content=} {e=}")
            return None

    def print_token(self) -> None:
        """
        Print the current authentication token.
        """
        self.logger.info(f"{self.token=}")

    def list_blueprint_ids(self) -> list:
        """
        Get the list of blueprint ids

        Returns:
            The list for blueprint id.
        """
        url = f"{self.url_prefix}/blueprints"
        return self.session.options(url).json()['items']

    def post(self, url: str, data: dict, params: dict = None) -> dict:
        """
        Post data to the url.

        Args:
            The url under /api/
            The post data

        Returns:
            The return
        """
        url = f"{self.url_prefix}/{url}"
        # self.logger.debug(f"post({url}, {data})")
        return self.session.post(url, json=data, params=params)

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()
    log_level = os.getenv('logging_level', 'DEBUG')
    prep_logging(log_level)

    apstra_server_host = os.getenv('apstra_server_host')
    apstra_server_port = os.getenv('apstra_server_port')
    apstra_server_username = os.getenv('apstra_server_username')
    apstra_server_password = os.getenv('apstra_server_password')

    apstra = CkApstraSession(apstra_server_host, apstra_server_port, apstra_server_username, apstra_server_password)
    apstra.print_token()
