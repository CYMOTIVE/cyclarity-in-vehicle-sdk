from utils.shell_device.base.device_shell_exception import DeviceShellException
from utils.shell_device.base.IDeviceShell import IDeviceShell
import serial
import re
import time
from pydantic import Field
from typing import Optional, Literal, Tuple

READ_BLOCK_SIZE = 10000
COMMAND_DONE_STRING = 'clarity_command_done'

class SerialDeviceShell(IDeviceShell):
    serial_device_name: str = Field (
        description="serial device name e.g. /dev/ttyUSB0",
    )
    serial_authentication_method: Literal["None", "Password"] = Field (
        description="Authentication method for interface",
    )
    serial_username: Optional[str] = Field (
        default=None,
        description="Username for shell interface",
    )
    serial_password: Optional[str] = Field (
        default=None,
        description="Password for shell interface",
    )
    serial_boudrate: Optional[int] = Field (
        description="serial interface baud rate such as 9600 or 115200 etc",
        default=115200,
    )
    serial_bytesize: Optional[Literal[5, 6, 7, 8]] = Field (
        description="serial interface Number of data bits. Possible values: 5, 6, 7, 8",
        default=8
    )
    serial_parity: Optional[Literal['N', 'E', 'O', 'M', 'S']] = Field (
        description="serial interface enable parity checking. Possible values: 'N', 'E', 'O', 'M', 'S'",
        default='N'
    )
    serial_stopbits: Optional[Literal[1, 1.5, 2]] = Field (
        description="serial interface number of stop bits. Possible values: 1, 1.5, 2",
        default=1
    )
    serial_timeout: Optional[float] = Field (
        description="serial interface read timeout value.",
        default=1
    )
    serial_xonxoff: Optional[bool] = Field (
        description="serial interface enable software flow control.",
        default=False
    )
    serial_rtscts: Optional[bool] = Field (
        description="serial interface enable hardware (RTS/CTS) flow control",
        default=False
    )
    serial_dsrdtr: Optional[bool] = Field (
        description="serial interface enable hardware (DSR/DTR) flow control.",
        default=False
    )
    serial_write_timeout: Optional[float] = Field (
        description="serial interface write timeout value.",
        default=None
    )
    serial_write_inter_byte_timeout: Optional[float] = Field (
        # todo how to set None option
        description="serial interface inter-character timeout, None to disable (default).",
        default=None
    )

    _ser = None
    _logged_in = False
    _last_read = ''

    def model_post_init(self, *args, **kwargs):
        super().model_post_init(self, *args, **kwargs) 
        self.logger.debug ("initializing serial")
        if not self.serial_device_name:
                raise DeviceShellException('serial_device_name is not defined')

        try:
            self._ser = serial.Serial (
                port=self.serial_device_name,
                baudrate=self.serial_boudrate,
                bytesize=self.serial_bytesize,
                parity=self.serial_parity,
                stopbits=self.serial_stopbits,
                timeout=self.serial_timeout,
                xonxoff=self.serial_xonxoff,
                rtscts=self.serial_rtscts,
                dsrdtr=self.serial_dsrdtr,
                write_timeout=self.serial_write_timeout,
                inter_byte_timeout=self.serial_write_inter_byte_timeout,
            )
            self._logged_in = False
            self._last_read = ''
            if not self._init_serial():
                raise DeviceShellException('serial connection failed')
        except Exception as e:
            self.logger.error (f"serial connection failed with: {str(e)}", exc_info=True)
            raise e

    @staticmethod
    def _is_password_prompt (str: str) -> bool:
        return ('Password:') in str

    @staticmethod
    def _is_login_prompt (str: str) -> bool:
        return 'login:' in str and 'Last' not in str

    @staticmethod
    def _is_command_prompt (str: str) -> bool:
        cli_prompt_pattern = re.compile (
            r'(\$|>|#|\[.+\@.+\s.+\]\$|>.+|.+@.+:.+\>)$'
        )

        return bool (cli_prompt_pattern.search (str))

    @staticmethod
    def _is_failure_prompt (str: str) -> bool:
        linux_pattern = re.compile (r"(Login incorrect|Permission denied, please try again)")
        return bool (linux_pattern.search (str))

    def _write_string(self, str: str) -> None:
        self.logger.debug (f"serial write {str}")
        self._ser.write (str.encode ())
        self._ser.flush ()
        time.sleep (0.5)

    def exec_command (self, command: str, testcase_filter: Optional[str] = None) -> Tuple[str, ...]:
        """
        This method executes a given command via serial interface and returns the output.
        If a testcase_filter is provided, it only returns lines that contain the filter string.

        :param command: String that represents the command to be executed.
        :param testcase_filter: Optional string used to filter the command's output.
        :return: A tuple containing the command's output lines that match the testcase_filter.
                 If no filter is provided, it returns all output lines.
        """


        if not self._logged_in:
            self.logger.error ("serial connection not logged in")
            return ['']

        try:
            self._write_string (f'{command} ; echo {COMMAND_DONE_STRING}\n')
            self._ser.flush ()
        except Exception as e:
            self.logger.error ("serial connection failed with: {e}")
            raise e

        if testcase_filter is None:
            testcase_filter = ''

        detections = []
        while True:
            try:
                self._read_string ()
                if testcase_filter in self._last_read:
                    detections.append (self._last_read)
                    break
                if COMMAND_DONE_STRING in self._last_read:
                    break
            except Exception as e:
                self.logger.error ("serial connection failed with: {e}", exc_info=True)
                raise e

        return tuple (detections)

    def _read_string(self) -> int:
        #todo consider using readline instead of read
        try:
            ser_bytes = self._ser.read (READ_BLOCK_SIZE)
            print(ser_bytes)
            self._last_read = ser_bytes.decode ("utf-8")[:-1]
            if ser_bytes:
                self.logger.debug (f'serial read: {ser_bytes.decode ("utf-8")[:-1]}')
            return len (ser_bytes.decode ("utf-8")[:-1])
        except Exception as e:
            self.logger.error ("Error reading from serial")
            raise e


    def _read_string_blocked_until_result(self, read_tries_timeout: int = 20) -> None:
        ser_bytes = 0
        read_cntr = read_tries_timeout
        while ser_bytes == 0 and read_cntr > 0:
            ser_bytes = self._read_string ()
            read_cntr -= 1

    def _login_with_password(self, user: str, password: str, sleep_before_answer: int = 1, login_retries: int = 3) -> bool:
        success = False
        i = login_retries
        while not success and i > 0:
            self.logger.debug (f"login try #{login_retries-i+1}")
            self._write_string (f'{user}\n')
            self._read_string ()

            if self._is_password_prompt (self._last_read):
                self.logger.debug ("sending password")
                self._write_string (f'{password}\n')
                time.sleep (sleep_before_answer)
                self._read_string ()
            if self._is_command_prompt (self._last_read):
                success = True
                break
            if self._is_failure_prompt (self._last_read):
                success = False
                break
            i -= 1
        self.logger.debug (f'login with password: {success}')
        return success

    def _validate_prompt(self, shell_name: str = 'bash') -> bool:
        self._write_string ('ps -p $$ -o comm=\n')
        self._read_string ()
        return shell_name in self._last_read

    def _logout (self) -> None:
        self._logged_in = False
        self._write_string ('logout\n')
        self._read_string ()

    def _login (self, user: str, password: str) -> bool\
            :
        # for debugging proposes:
        #self.logout()
        #self._ser.flushInput()


        self._write_string ('\n')
        time.sleep(1)
        line_size = self._read_string ()
        if self._is_command_prompt (self._last_read):
            if self._validate_prompt ():
                self.logger.debug ('Already logged in')
                self._logged_in = True
                return True

        empty_cntr: int = 0
        unknown_cntr: int = 0

        while not self._logged_in:
            try:
                line_size = self._read_string ()
                if line_size > 0:
                    if self._is_command_prompt(self._last_read):  # and not user and not password: # and password ans username is empty
                        self.logger.debug ('Logged in')
                        self._logged_in = True
                        return True
                    elif self._is_login_prompt (self._last_read):
                        if self._login_with_password (user, password):
                            if self._is_command_prompt (self._last_read):
                                self._logged_in = True
                                return True
                                #in case we want double check
                                # if self.validate_prompt ():
                                #    self.logger.debug ('Logged In')
                                #    self.logged_in = True
                                #    return True
                                #else
                                #   return False
                            else:
                                return False
                        else:
                            return False
                    else:
                        unknown_cntr += 1
                        if unknown_cntr > 5:
                            return False
                else:
                    empty_cntr += 1
                    if empty_cntr > 5:
                        self._write_string ('\n')
                        empty_cntr = 0

            except Exception as error:
                self.logger.error (error, exc_info=True)
                return False

        return False

    def teardown(self):
        """
        This method is intended to logout the serial session.
        If an error occurs during the operation, it is logged and re-raised.
        """

        self._logout()

    def _init_serial(self) -> bool:
        return self._login (self.serial_username, self.serial_password)


