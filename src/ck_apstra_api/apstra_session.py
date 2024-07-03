#!/usr/bin/env python3
from functools import cache
from typing import Optional
import requests
import urllib3
import logging
import time
from datetime import datetime
from result import Result, Ok, Err


class CustomFormatter(logging.Formatter):
    black = "\x1b[30;21m"
    grey = "\x1b[38;21m"
    dark_gray = "\x1b[90;21m"
    white = "\x1b[37;21m"
    bright_white = "\x1b[97;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: white + format + reset,
        logging.INFO: dark_gray + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        levelname = record.levelname.ljust(8)  # Set the level name to a fixed width (e.g., 8 characters)
        record.levelname = levelname
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def prep_logging(log_level: str = 'INFO', log_name: str = 'root'):
    '''Configure logging options'''
    timestamp = datetime.now().strftime("%Y%m%d-%H:%H:%S")
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.getLevelName(log_level))
    ch.setFormatter(CustomFormatter())
    logger.addHandler(ch)
    return logger

def deep_copy(obj):
    """Retun nested deep copy of an object"""
    if type(obj) is dict:
        return {k: deep_copy(v) for k, v in obj.items()}
    if type(obj) is list:
        return [deep_copy(v) for v in obj]
    return obj


# https client session to Apstra Controller
class CkApstraSession:

    def __init__(self, 
                 host: str, 
                 port: int, 
                 username: str, 
                 password: str) -> None:
        """
        Create a new Apstra session. When it fails, self.last_error captures the error message.
        """
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
        self.last_error = None

        self.get_version()
        self.login()

        self.device_profile_cache = {}  # { device_profile_id: data }

    def get_version(self) -> str:
        """
        Get the version of the Apstra controller.

        Returns:
            The version of the Apstra controller.
        """
        url = f"{self.url_prefix}/versions/server"
        response = self.session.get(url)
        version = response.json()["version"]
        self.version = version
        return self.version

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
        # the status code is 201 if the login is successful
        if response.status_code == 201:
            self.token = response.json()["token"]
            self.session.headers.update({'AuthToken': self.token})
            self.last_error = None
            return
        if response.status_code == 401:
            self.last_error = response.json()['errors']
            self.logger.error(f"login failed: {response.content}")
            return
        else:
            self.last_error = response.content
            self.logger.error(f"login failed: {self.last_error}")
            return

    def logout(self) -> None:
        self.token = None
        url = f"{self.url_prefix}/aaa/logout"
        response = self.post(url, None)
        # the status code is 404 (not found) if the logout is successful
        return response
    
    def is_online(self) -> bool:
        """
        Check if the Apstra controller is online.

        Returns:
            True if the Apstra controller is online, False otherwise.
        """
        return self.token is not None


    @cache
    def get_device_profile(self, device_profile_name: str = None) -> Result[dict, str]:
        """
        Get the device profile with the specified name.

        Args:
            name: The name of the device profile.

        Returns:
            The device profile, or None if the device profile does not exist.
        """
        if device_profile_name is None:
            return Err(f"Error: {device_profile_name=}")
            # return None, f"Error: {device_profile_name=}"
        device_profiles = self.get_items('device-profiles')['items']
        the_device_profile = [x for x in device_profiles if x['id'] == device_profile_name][0]
        return Ok(the_device_profile)
        # return the_device_profile, None


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

