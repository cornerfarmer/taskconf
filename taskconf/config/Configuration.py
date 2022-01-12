import copy
import datetime
import time
import uuid

from taskconf.config.ConfigurationBlock import ConfigurationBlock
import collections


class Configuration:

    def __init__(self, data=None, base_configs=[], file=None):
        """Creates a new config.

        Args:
            data(dict): The raw json data of the config.
            base_configs(Configuration): The base config object for this config.
            file(str): The filename which contained the config.
        """
        self.prefix = ""
        self.base_configs = base_configs#[[base_config] if not type(base_config) is list else base_config for base_config in base_configs]
        self.file = file
        self.try_number = 0
        self.iteration_cursor = 0

        if data is not None:
            self.set_data(data)
        else:
            self.data = {}
            self.uuid = ""
            self.creation_time = 0
            self.config = None
            self.abstract = False
            self.dynamic = False

    def set_base_configs(self, base_configs):
        self.base_configs = {}
        for iteration in base_configs:
            self.base_configs[iteration] = [[base_config] if not type(base_config) is list else base_config for base_config in base_configs[iteration]]
        self.config = self._build_config(self.data["config"])
        self.dynamic = len(self.config.get_merged_config()) > 1

    def treat_dynamic(self):
        if self.dynamic:
            return True

        for iteration in self.base_configs:
            for base_config in self.base_configs[iteration]:
                if base_config[0].treat_dynamic():
                    return True

        return False

    def set_data(self, new_data):
        if "uuid" not in new_data:
            new_data["uuid"] = str(uuid.uuid4())
        if "creation_time" not in new_data:
            new_data["creation_time"] = time.mktime(datetime.datetime.now().timetuple())

        self.data = new_data
        self.uuid = new_data["uuid"]
        self.creation_time = datetime.datetime.fromtimestamp(new_data["creation_time"])
        self.abstract = "abstract" in new_data and bool(new_data["abstract"])
        self.dynamic = "dynamic" in new_data and bool(new_data["dynamic"])
        self.config = self._build_config(new_data["config"])
        self.dynamic = len(self.config.get_merged_config()) > 1

    def update_config(self, config):
        self.data["config"] = self._deep_update(self.data["config"], config)
        self.set_data(self.data)

    def _deep_update(self, d, u):
        for k, v in u.items():
            if isinstance(v, collections.Mapping):
                d[k] = self._deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def set_metadata(self, name, value):
        self.data[name] = value

    def get_metadata(self, name):
        return self.data[name]

    def has_metadata(self, name):
        return name in self.data

    def path(self):
        return self.config.path()

    def _build_config(self, config):
        if not self.dynamic:
            config = {"0": config}

        base_configs = []
        for iteration in self.base_configs:
            for base_config in self.base_configs[iteration]:
                base_configs.append([{iteration: base_config[0].get_merged_config(True)["0"]}] + base_config[1:])
        return ConfigurationBlock(config, base_configs)

    def get_merged_config(self, force_dynamic=False):
        config = self.config.get_merged_config()
        if not force_dynamic and not self.treat_dynamic():
            config = config["0"]
        return config

    def get_int(self, name, fallback=None):
        """Returns the configuration with the given name or the fallback name as an integer.

        If the configuration cannot be found in this config, the request will use the base config as fallback.
        If there is no configuration with the given name, the fallback configuration will be used.

        Args:
            name(str): The name of the configuration.
            fallback(str): The name of the fallback configuration, which should be used if the primary one cannot be found.

        Returns:
            int: The integer value of the configuration.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base configs.
            TypeError. If the configuration value cannot be converted into an integer.
        """
        return self.config.get_int(self.prefix + name, fallback, self.iteration_cursor)

    def get_string(self, name, fallback=None):
        """Returns the configuration with the given name or the fallback name as a string.

        If the configuration cannot be found in this config, the request will use the base config as fallback.
        If there is no configuration with the given name, the fallback configuration will be used.

        Args:
            name(str): The name of the configuration.
            fallback(str): The name of the fallback configuration, which should be used if the primary one cannot be found.

        Returns:
            str: The string value of the configuration.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base configs.
            TypeError. If the configuration value cannot be converted into a string.
        """
        return self.config.get_string(self.prefix + name, fallback, self.iteration_cursor)

    def get_float(self, name, fallback=None):
        """Returns the configuration with the given name or the fallback name as a float.

        If the configuration cannot be found in this config, the request will use the base config as fallback.
        If there is no configuration with the given name, the fallback configuration will be used.

        Args:
            name(str): The name of the configuration.
            fallback(str): The name of the fallback configuration, which should be used if the primary one cannot be found.

        Returns:
            float: The float value of the configuration.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base configs.
            TypeError. If the configuration value cannot be converted into a float.
        """
        return self.config.get_float(self.prefix + name, fallback, self.iteration_cursor)

    def get_bool(self, name, fallback=None):
        """Returns the configuration with the given name or the fallback name as a bool.

        If the configuration cannot be found in this config, the request will use the base config as fallback.
        If there is no configuration with the given name, the fallback configuration will be used.

        Args:
            name(str): The name of the configuration.
            fallback(str): The name of the fallback configuration, which should be used if the primary one cannot be found.

        Returns:
            bool: The bool value of the configuration.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base configs.
            TypeError. If the configuration value cannot be converted into a bool.
        """
        return self.config.get_bool(self.prefix + name, fallback, self.iteration_cursor)

    def get_list(self, name, fallback=None):
        """Returns the configuration with the given name or the fallback name as a list.

        If the configuration cannot be found in this config, the request will use the base config as fallback.
        If there is no configuration with the given name, the fallback configuration will be used.

        Args:
            name(str): The name of the configuration.
            fallback(str): The name of the fallback configuration, which should be used if the primary one cannot be found.

        Returns:
            list: The list value of the configuration.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base configs.
            TypeError. If the configuration value cannot be converted into a list.
        """
        return self.config.get_list(self.prefix + name, fallback, self.iteration_cursor)

    def get_value(self, name, fallback=None):
        return self.config.get_value(self.prefix + name, fallback, self.iteration_cursor)
    
    def get_keys(self, name):
        if not self.dynamic:
            name = "0/" + name
        return self.config.get_keys(name)

    def get_with_prefix(self, prefix):
        """Clones this config and adds an additional prefix.

        Args:
            prefix(str): The additional prefix.

        Returns:
            Configuration: The new config with the requested prefix.
        """
        config = self.clone(deep=False)
        config.prefix = self.prefix + prefix + "/"
        return config

    def clone(self, deep=True):
        config = Configuration(base_configs=self.base_configs)
        if deep:
            config.config = self.config.clone()
            config.data = copy.deepcopy(self.data)
        else:
            config.config = self.config
            config.data = self.data
        config.prefix = self.prefix
        config.file = self.file
        config.try_number = self.try_number
        config.uuid = self.uuid
        config.creation_time = self.creation_time
        config.iteration_cursor = self.iteration_cursor
        config.dynamic = self.dynamic
        return config

    def set_logger(self, new_logger, printed_settings=None):
        """Cleans the list of all already printed settings.

        After calling this, the configuration log will start from scratch again.

        Args:
            new_logger: A new logger which should be used for future logging.
            printed_settings:
        """
        self.config.set_logger(new_logger, printed_settings)

    def get_merged_data(self):
        data = copy.deepcopy(self.data)
        data["config"] = self.get_merged_config()
        return data