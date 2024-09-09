from utils.shell_device.base.device_shell_exception import DeviceShellException
from utils.shell_device.base.IDeviceShell import IDeviceShell
import paramiko
import io
import base64
from pydantic import Field
from typing import Optional, Literal, Tuple, NoReturn
from pydantic.networks import IPvAnyAddress

class SshDeviceShell (IDeviceShell):
    ssh_ip: IPvAnyAddress = Field (
        description="shell interface ip",
    )
    ssh_port: Optional[int] = Field (
        default=22,
        description="shell interface port",
    )
    ssh_authentication_method: Literal["None", "Password", "Key"] = Field (
        description="Authentication method for interface",
    )
    ssh_username: Optional[str] = Field (
        default=None,
        description="Username for shell interface",
    )
    ssh_password: Optional[str] = Field (
        default=None,
        description="Password for shell interface",
    )
    ssh_private_key: Optional[str] = Field (
        default=None,
        description="private key for shell interface in base64",
    )


    def model_post_init (self, *args, **kwargs):
        super ().model_post_init (self, *args, **kwargs)
        self.logger.info ("initializing ssh")

        try:
            self._init_ssh ()
        except (
                TimeoutError,
                paramiko.AuthenticationException,
                paramiko.SSHException,
        ) as e:
            self.logger.error (f"ssh initialization failed with: {e}", exc_info=True)
            raise e

    def exec_command (self, command: str, testcase_filter: Optional[str] = None) -> Tuple[str, ...]:
        """
        This method executes a given command via ssh and returns the output.
        If a testcase_filter is provided, it only returns lines that contain the filter string.

        :param command: String that represents the command to be executed.
        :param testcase_filter: Optional string used to filter the command's output.
        :return: A tuple containing the command's output lines that match the testcase_filter.
                 If no filter is provided, it returns all output lines.
        """

        _, stdout, _ = self.ssh.exec_command (command)

        detections = []
        for line in stdout.readlines ():
            self.logger.debug (f'read: "{line}"')
            if testcase_filter:
                if testcase_filter in line:
                    self.logger.debug (f'detect: "{testcase_filter}"')
                    detections.append (line)
                    break
            else:
                detections.append (line)

        return tuple (detections)

    def _init_ssh (self) -> NoReturn:
        try:
            self.ssh = paramiko.SSHClient ()
            self.ssh.set_missing_host_key_policy (paramiko.AutoAddPolicy ())
            if self.ssh_authentication_method == "None":
                self.ssh.connect (
                    str (self.ssh_ip),
                    self.ssh_port,
                    timeout=1,
                )
            elif self.ssh_authentication_method == "Password":
                self.ssh.connect (
                    str (self.ssh_ip),
                    self.ssh_port,
                    username=self.ssh_username,
                    password=self.ssh_password,
                    timeout=1,
                )
            elif self.ssh_authentication_method == "Key":
                self.ssh.connect (
                    str (self.ssh_ip),
                    self.ssh_port,
                    username=self.ssh_username,
                    pkey=paramiko.Ed25519Key.from_private_key (
                        io.StringIO (
                            str (
                                base64.b64decode (
                                    bytes (
                                        self.ssh_private_key,
                                        "utf-8",
                                    )
                                ),
                                "utf-8",
                            )
                        )
                    ),
                    timeout=1,
                )
            else:
                self.logger.error (
                    f"Unrecognized logging_interface_authentication_method {self.ssh_authentication_method}")
                raise DeviceShellException (
                    f"Unrecognized logging_interface_authentication_method {self.ssh_authentication_method}")
        except Exception as e:
            self.logger.error (f"ssh connection failed with: {str (e)}", exc_info=True)
            raise DeviceShellException (str (e))

    def teardown (self):
        """
        This method is intended to close the ssh connection.
        If an error occurs during the operation, it is logged and re-raised.
        """

        try:
            self.ssh.close ()
        except Exception as e:
            self.logger.error (f"ssh closing failed with: {e}", exc_info=True)
            raise e
