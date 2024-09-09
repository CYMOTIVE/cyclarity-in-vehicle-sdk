import logging
import ipaddress
import base64

from adb_shell.adb_device import AdbDeviceTcp, AdbDeviceUsb
from adb_shell.auth.sign_pythonrsa import PythonRSASigner

from utils.shell_device.base.device_shell_exception import DeviceShellException
from utils.shell_device.base.IDeviceShell import IDeviceShell

from pydantic import Field, field_validator
from pydantic.networks import IPvAnyAddress
from typing import Optional, Literal, Tuple



class AdbDeviceShell (IDeviceShell):
    adb_authentication_method: Literal["None", "Key"] = Field (
        description="Authentication method for interface",
    )
    adb_ip: str = Field (
        description="shell interface ip OR 'usb'",
    )
    adb_port: Optional[int] = Field (
        default=5555,
        description="shell interface port",
    )
    adb_private_key: Optional[str] = Field (
        default=None,
        description="private key (RSA-2048) for shell interface in base64",
    )
    adb_public_key: Optional[str] = Field (
        default=None,
        description="public key (RSA-2048) for shell interface in base64",
    )

    _adb_device_shell = None

    @field_validator ('adb_ip')
    @classmethod
    def validate_ip(cls, v):
        if v == 'usb':
            return v
        try:
            IPvAnyAddress(v)
            return v
        except ValueError:
            raise ValueError("adb_ip must be either 'usb' or a valid IP address")

    def model_post_init(self, *args, **kwargs):
        super().model_post_init(self, *args, **kwargs) 
        self.logger.info ("initializing adb")

        try:
            res = self._init_adb ()
            if not res:
                raise DeviceShellException ('adb connection failed')
        except Exception as e:
            self.logger.error (f"adb initialization failed with: {e}", exc_info=True)
            raise e

    def _init_adb(self) -> bool:
        if self.adb_authentication_method == "Key":
            pub, priv = self._read_keys ()
            signer = PythonRSASigner (pub, priv)
        elif self.adb_authentication_method == "None":
            signer = None
        else:
            self.logger.error (
                f'Authentication method {self.adb_authentication_method} for the ADB logging interface is not supported!')
            raise DeviceShellException ('Authentication method is not supported!')

        # Connect
        if self._valid_ip (self.adb_ip):
            self.logger.debug (
                f"Connecting adb IP device_shell: {self.adb_ip}:{self.adb_port}")
            self._adb_device_shell = AdbDeviceTcp (
                self.adb_ip,
                self.adb_port,
                default_transport_timeout_s=5)
        elif self.adb_ip == 'usb':
            self.logger.debug ("Adding adb USB device_shell")
            self._adb_device_shell = AdbDeviceUsb ()
        else:
            self.logger.error (f"invalid destination_ip: {self.adb_ip}")
            raise DeviceShellException (f'invalid destination_ip: {self.adb_ip}')

        #long timeout in order to give the operator time to approve the connection on the device_shell
        res = self._adb_device_shell.connect (rsa_keys=[signer], auth_timeout_s=60)
        if res:
            self.logger.info (
                f"Connected adb device shell at  {self.adb_ip}:{self.adb_port}")
        return res

    def exec_command (self, command: str, testcase_filter: Optional[str] = None) -> Tuple[str, ...]:
        """
        This method executes a given command via adb interface and returns the output.
        If a testcase_filter is provided, it only returns lines that contain the filter string.

        :param command: String that represents the command to be executed.
        :param testcase_filter: Optional string used to filter the command's output.
        :return: A tuple containing the command's output lines that match the testcase_filter.
                 If no filter is provided, it returns all output lines.
        """

        # Send a shell command
        stdout_str = self._adb_device_shell.shell (command)

        if testcase_filter:
            if testcase_filter in stdout_str:
                self.logger.debug (f'detect: "{testcase_filter}"')
                return tuple ([stdout_str.strip ()])
            else:
                return tuple ()
        else:
            return tuple ([stdout_str.strip ()])

    def teardown (self):
        """
        This method is intended to close the adb session.
        If an error occurs during the operation, it is logged and re-raised.
        """
        try:
            self._adb_device_shell.close ()
        except Exception as e:
            self.logger.error (f"adb closing failed with: {e}", exc_info=True)
            raise e

    def _read_keys (self) -> Tuple[str, str]:
        adbkey_pub = None
        adbkey_private = None
        try:
            adbkey_private = str (
                base64.b64decode (
                    bytes (
                        self.adb_private_key,
                        "utf-8",
                    )
                ),
                "utf-8",
            )

            adbkey_pub = str (
                base64.b64decode (
                    bytes (
                        self.adb_public_key,
                        "utf-8",
                    )
                ),
                "utf-8",
            )

        except Exception as e:
            self.logger.error (f"adb initialization failed with: {e}", exc_info=True)
            raise DeviceShellException ('key decode failed!')

        return adbkey_pub, adbkey_private

    @staticmethod
    def _valid_ip(ip: str) -> bool:
        try:
            ipaddress.ip_address (ip)
            return True
        except ValueError:
            return False
