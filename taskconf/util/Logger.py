import logging
try:
  from pathlib2 import Path
except ImportError:
  from pathlib import Path
from multiprocessing import Lock
import datetime
import sys

class Logger:

    def __init__(self, log_path=None, file_name=None, parent_logger=None, module_name="general", replace=False, terminal=None):
        """ Creates a logger.

        Args:
            log_path(Path): The path where to write logs.
            file_name(str): The name of the logfile.
            logger(logging.Logger): An existing logger which should be used instead of creating one.
            module_name(str): The name of the module which uses this logger.
            replace(bool): True, if an existing log file should be replaced.
        """
        self.terminal = terminal
        self._module_name = module_name

        if parent_logger is None:
            self._parent = None
            path = log_path / Path(file_name + ".log")
            if replace and path.exists():
                path.unlink()

            self._mutex = Lock()
            self._file = open(str(path), "a")
            if not replace:
                self.log("-" * 50)
        else:
            self._parent = parent_logger

    def __del__(self):
        if self._parent is None:
            self._file.close()

    def log(self, message, level=logging.INFO):
        """ Logs the given message.

        Args:
            level(int): The log level of the message.
            message(str): The message.
        """
        if self._parent is None:
            line = ""
            line += "[" + str(datetime.datetime.now()) + "]"
            line += "[" + logging.getLevelName(level) + "]"
            line += "[" + self._module_name + "]"
            line += " " + message.strip()
            line += "\n"

            self._mutex.acquire()
            if self.terminal is not None:
                self.terminal.write(line)
            self._file.write(line)
            self._file.flush()
            self._mutex.release()
        else:
            self._parent.log(message, level)

    def get_with_module(self, module_name):
        """ Clones this logger and sets a new module name.

        Returns:
            Logger: The cloned logger.
        """
        return Logger(parent_logger=self, module_name=module_name)
