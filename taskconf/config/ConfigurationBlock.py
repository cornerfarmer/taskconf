import copy
import collections
import json

class ConfigurationBlock:

    def __init__(self, config, base_configs=[]):
        """Creates a configuration block.

        Args:
            data(dict): A nested key/value structure of raw configurations.
        """
        self.config = config
        self.base_configs = base_configs
        self.printed_settings = {}
        self.logger = None
        if config is not None:
            self._merge_config()

    def set_logger(self, new_logger, printed_settings=None):
        """Cleans the list of all already printed settings.

        After calling this, the configuration log will start from scratch again.

        Args:
            new_logger: A new logger which should be used for future logging.
            printed_settings:
        """
        self.printed_settings = {} if printed_settings is None else printed_settings
        self.logger = new_logger

    def _merge_config(self):
        self.merged_config = {}

        for base_config in self.base_configs:
            self._deep_update(self.merged_config, base_config[0], base_config[1:])

        self._deep_update(self.merged_config, self.config, [])

    def _deep_update(self, d, u, args):
        for k, v in u.items():
            if isinstance(v, collections.Mapping):
                d[k] = self._deep_update(d.get(k, {}), v, args)
            else:
                d[k] = v
                if type(d[k]) == str:
                    for i in range(len(args)):
                        template = "$T" + str(i) + "$"
                        try:
                            json_value = json.loads(str(args[i]))
                        except ValueError:
                            json_value = None

                        if d[k] == template and json_value is not None:
                            d[k] = json_value
                        else:
                            d[k] = d[k].replace(template, args[i])
        return d

    def get_merged_config(self):
        return self.merged_config

    def _path_from_config(self, config, prefix=[]):
        if len(config.keys()) == 1 and type(list(config.values())[0]) == dict:
            return self._path_from_config(list(config.values())[0], prefix + [list(config.keys())[0]])
        else:
            return prefix

    def all_timesteps(self):
        return set([int(num) for num in self.merged_config.keys()])

    def valid_timesteps(self, current_timestep):
        timesteps = self.all_timesteps()
        timesteps = list(filter(lambda x: x <= current_timestep, timesteps))
        timesteps.sort(reverse=True)
        return timesteps

    def _get_value_from_block(self, name, block):
        if "/" in name:
            delimiter_pos = name.find("/")
            block_name = name[:delimiter_pos]
            if block_name in block and type(block[block_name]) is dict:
                return self._get_value_from_block(name[delimiter_pos + 1:], block[block_name])
            else:
                raise NotFoundError("No such configuration block '" + block_name + "'!")
        else:
            if name in block:
                return block[name]
            else:
                raise NotFoundError("No such configuration '" + name + "'!")

    def _get_value_at_timestep(self, name, timestep):
        return self._get_value_from_block(str(timestep) + "/" + name, self.merged_config)

    def _get_value(self, name, current_timestep):
        """Returns the configuration with the given name and the given type.

        If the configuration cannot be found in this config, the request will use the base config as fallback.

        Args:
            name(str): The name of the configuration.
            value_type(str): The desired type of the configuration value.

        Returns:
            object: The value of the configuration in the requested type.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base configs.
            TypeError. If the configuration value cannot be converted into the requested type.
        """
        for timestep in self.valid_timesteps(current_timestep):
            try:
                value = self._get_value_at_timestep(name, timestep)
                return value
            except NotFoundError:
                pass

        raise NotFoundError("No such configuration '" + name + "'!")

    def _get_value_with_fallback(self, name, fallback, current_timestep):
        """Returns the configuration with the given name or the fallback name and the given type.

        If the configuration cannot be found in this config, the request will use the base config as fallback.
        If there is no configuration with the given name, the fallback configuration will be used.

        Args:
            name(str): The name of the configuration.
            fallback(str): The name of the fallback configuration, which should be used if the primary one cannot be found.
            value_type(str): The desired type of the configuration value.

        Returns:
            object: The value of the configuration in the requested type.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base configs.
            TypeError. If the configuration value cannot be converted into the requested type.
        """

        try:
            value = self._get_value(name, current_timestep)
        except NotFoundError:
            if fallback is not None:
                value = self._get_value(fallback, current_timestep)
            else:
                raise

        if (name not in self.printed_settings or self.printed_settings[name] != value) and self.logger is not None:
            if name not in self.printed_settings:
                self.logger.log("Using " + name + " = " + str(value))
            else:
                self.logger.log("Switching " + name + ": " + str(self.printed_settings[name]) + " -> " + str(value))
            self.printed_settings[name] = value

        return value

    def get_int(self, name, fallback=None, current_timestep=0):
        """Returns the value of the configuration with the given name as integer.

        Args:
            name(str): The name of the configuration.

        Returns:
            int: The integer value of the configuration.

        Raises:
            TypeError: If the value could not be converted to an integer.
        """
        value = self._get_value_with_fallback(name, fallback, current_timestep)
        try:
            return int(value)
        except ValueError:
            raise TypeError("Cannot convert '" + str(value) + "' to int!")

    def get_bool(self, name, fallback=None, current_timestep=0):
        """Returns the value of the configuration with the given name as bool.

        Args:
            name(str): The name of the configuration.

        Returns:
            bool: The bool value of the configuration.

        Raises:
            TypeError: If the value could not be converted to a bool.
        """
        value = self._get_value_with_fallback(name, fallback, current_timestep)
        try:
            return bool(value)
        except ValueError:
            raise TypeError("Cannot convert '" + str(value) + "' to bool!")

    def get_float(self, name, fallback=None, current_timestep=0):
        """Returns the value of the configuration with the given name float.

        Args:
            name(str): The name of the configuration.

        Returns:
            float: The float value of the configuration.

        Raises:
            TypeError: If the value could not be converted to a float.
        """
        value = self._get_value_with_fallback(name, fallback, current_timestep)
        try:
            return float(value)
        except ValueError:
            raise TypeError("Cannot convert '" + str(value) + "' to float!")

    def get_string(self, name, fallback=None, current_timestep=0):
        """Returns the value of the configuration with the given name as string.

        Args:
            name(str): The name of the configuration.

        Returns:
            string: The string value of the configuration.

        Raises:
            TypeError: If the value could not be converted to a string.
        """
        value = self._get_value_with_fallback(name, fallback, current_timestep)
        try:
            return str(value)
        except ValueError:
            raise TypeError("Cannot convert '" + str(value) + "' to string!")

    def get_list(self, name, fallback=None, current_timestep=0):
        """Returns the value of the configuration with the given name as list.

        Args:
            name(str): The name of the configuration.

        Returns:
            list: The list value of the configuration.

        Raises:
            TypeError: If the value could not be converted to a string.
        """
        value = self._get_value_with_fallback(name, fallback, current_timestep)
        if not isinstance(value, list):
            raise TypeError("Cannot convert '" + str(value) + "' to list!")
        return value

    def get_value(self, name, fallback=None, current_timestep=0):
        """Returns the value of the configuration with the given name as list.

        Args:
            name(str): The name of the configuration.

        Returns:
            list: The list value of the configuration.

        Raises:
            TypeError: If the value could not be converted to a string.
        """
        value = self._get_value_with_fallback(name, fallback, current_timestep)
        return value

    def get_keys(self, name):
        return self._get_keys(name, self.merged_config)

    def _get_keys(self, name, block):
        if name != "":
            if "/" in name:
                delimiter_pos = name.find("/")
                block_name = name[:delimiter_pos]
                name = name[delimiter_pos + 1:]
            else:
                block_name = name
                name = ""

            if block_name in block:
                return self._get_keys(name, block[block_name])
            else:
                raise NotFoundError("No such configuration block '" + block_name + "'!")
        else:
            return list(block.keys())

    def flatten(self, prefix=''):
        data = {}
        for key in self.data.keys():
            data[prefix + key] = self.data[key]
        for key in self.configBlocks.keys():
            data.update(self.configBlocks[key].flatten(prefix + key + "/"))
        return data

    def clone(self):
        config = ConfigurationBlock(None)
        config.config = copy.deepcopy(self.config)
        config.base_configs = [copy.deepcopy(base) for base in self.base_configs]
        config.merged_config = copy.deepcopy(self.merged_config)
        return config

class NotFoundError(Exception):
    pass
