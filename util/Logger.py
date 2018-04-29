import logging
import os

class Logger:

    def __init__(self, results_path=None, experiment_name=None, file_name=None, logger=None, module_name="general", replace=False):
        """ Creates a logger.

        Args:
            results_path(str): The path where to write logs.
            experiment_name(str): The name of the current experiment.
            file_name(str): The name of the logfile.
            logger(logging.Logger): An existing logger which should be used instead of creating one.
            module_name(str): The name of the module which uses this logger.
            replace(bool): True, if an existing log file should be replaced.
        """
        self.module_name = module_name

        if logger is None:
            self.logger = logging.getLogger(experiment_name)
            self.logger.setLevel(logging.DEBUG)

            directory = results_path + experiment_name + "/"
            if not os.path.exists(directory):
                os.makedirs(directory)

            path = directory + file_name + ".log"
            if replace and os.path.isfile(path):
                os.remove(path)

            fh = logging.FileHandler(path)
            fh.setLevel(logging.DEBUG)

            formatter = logging.Formatter('[%(asctime)s][%(levelname)s]%(message)s')
            fh.setFormatter(formatter)

            self.logger.addHandler(fh)

            if not replace:
                self.log(logging.INFO, "-" * 100)
        else:
            self.logger = logger

    def log(self, level, message):
        """ Logs the given message.

        Args:
            level(int): The log level of the message.
            message(str): The message.
        """
        self.logger.log(level, '[' + self.module_name + '] ' + message)

    def log_confusion_matrix(self, level, confusion_matrix, classes):
        """ Logs the given confusion matrix with proper alignment.

        Args:
            level(int): The log level of the message.
            confusion_matrix(ndarray): The matrix to log.
            classes(list): The class names.
        """
        cells = []

        for i in range(len(classes)):
            if i == 0:
                row = ["Act \\ Pred"]
                for class_name in classes:
                    row.append(class_name)
                cells.append(row)

            row = [classes[i]]
            for j in range(len(classes)):
                row.append(str(int(confusion_matrix[i][j])))
            cells.append(row)

        for row in cells:
            text = ""
            for cell in row:
                text += "{:11s}".format(cell) + "|"
            self.log(level, text)

    def get_with_module(self, module_name):
        """ Clones this logger and sets a new module name.

        Returns:
            Logger: The cloned logger.
        """
        return Logger(logger=self.logger, module_name=module_name)
