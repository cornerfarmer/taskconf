import logging

from config.ConfigurationBlock import ConfigurationBlock, NotFoundError


class Preset:
    _printed_settings = set()
    logger = None

    def __init__(self, data=None, base_preset=None, file=None):
        """Creates a new preset.

        Args:
            data(dict): The raw json data of the preset.
            base_preset(Preset): The base preset object for this preset.
            file(str): The filename which contained the preset.
        """
        if data is not None:
            self.set_data(data)
        else:
            self.data = {}
            self.name = ""
            self.uuid = ""
            self.config = None
            self.abstract = False
        self.prefix = ""
        self.base_preset = base_preset
        self.file = file
        self.try_number = 0

    def set_data(self, new_data):
        self.data = new_data
        self.name = new_data["name"] if "name" in new_data else "fallback"
        self.uuid = new_data["uuid"] if "uuid" in new_data else "-1"
        self.config = ConfigurationBlock(new_data["config"])
        self.abstract = "abstract" in new_data and bool(new_data["abstract"])

    def _get_value(self, name, value_type):
        """Returns the configuration with the given name and the given type.

        If the configuration cannot be found in this preset, the request will use the base preset as fallback.

        Args:
            name(str): The name of the configuration.
            value_type(str): The desired type of the configuration value.

        Returns:
            object: The value of the configuration in the requested type.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base presets.
            TypeError. If the configuration value cannot be converted into the requested type.
        """
        try:
            value = getattr(self.config, 'get_' + value_type)(name)
        except NotFoundError:
            if self.base_preset is None:
                raise
            else:
                value = self.base_preset._get_value(name, value_type)

        return value

    def _get_value_with_fallback(self, name, fallback, value_type):
        """Returns the configuration with the given name or the fallback name and the given type.

        If the configuration cannot be found in this preset, the request will use the base preset as fallback.
        If there is no configuration with the given name, the fallback configuration will be used.

        Args:
            name(str): The name of the configuration.
            fallback(str): The name of the fallback configuration, which should be used if the primary one cannot be found.
            value_type(str): The desired type of the configuration value.

        Returns:
            object: The value of the configuration in the requested type.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base presets.
            TypeError. If the configuration value cannot be converted into the requested type.
        """
        name = self.prefix + name

        try:
            value = self._get_value(name, value_type)
        except NotFoundError:
            if fallback is not None:
                value = self._get_value(self.prefix + fallback, value_type)
            else:
                raise

        if name not in Preset._printed_settings and Preset.logger is not None:
            Preset.logger.log(logging.INFO, "Using " + name + " = " + str(value))
            Preset._printed_settings.add(name)

        return value

    def get_int(self, name, fallback=None):
        """Returns the configuration with the given name or the fallback name as an integer.

        If the configuration cannot be found in this preset, the request will use the base preset as fallback.
        If there is no configuration with the given name, the fallback configuration will be used.

        Args:
            name(str): The name of the configuration.
            fallback(str): The name of the fallback configuration, which should be used if the primary one cannot be found.

        Returns:
            int: The integer value of the configuration.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base presets.
            TypeError. If the configuration value cannot be converted into an integer.
        """
        return self._get_value_with_fallback(name, fallback, 'int')

    def get_string(self, name, fallback=None):
        """Returns the configuration with the given name or the fallback name as a string.

        If the configuration cannot be found in this preset, the request will use the base preset as fallback.
        If there is no configuration with the given name, the fallback configuration will be used.

        Args:
            name(str): The name of the configuration.
            fallback(str): The name of the fallback configuration, which should be used if the primary one cannot be found.

        Returns:
            str: The string value of the configuration.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base presets.
            TypeError. If the configuration value cannot be converted into a string.
        """
        return self._get_value_with_fallback(name, fallback, 'string')

    def get_float(self, name, fallback=None):
        """Returns the configuration with the given name or the fallback name as a float.

        If the configuration cannot be found in this preset, the request will use the base preset as fallback.
        If there is no configuration with the given name, the fallback configuration will be used.

        Args:
            name(str): The name of the configuration.
            fallback(str): The name of the fallback configuration, which should be used if the primary one cannot be found.

        Returns:
            float: The float value of the configuration.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base presets.
            TypeError. If the configuration value cannot be converted into a float.
        """
        return self._get_value_with_fallback(name, fallback, 'float')

    def get_bool(self, name, fallback=None):
        """Returns the configuration with the given name or the fallback name as a bool.

        If the configuration cannot be found in this preset, the request will use the base preset as fallback.
        If there is no configuration with the given name, the fallback configuration will be used.

        Args:
            name(str): The name of the configuration.
            fallback(str): The name of the fallback configuration, which should be used if the primary one cannot be found.

        Returns:
            bool: The bool value of the configuration.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base presets.
            TypeError. If the configuration value cannot be converted into a bool.
        """
        return self._get_value_with_fallback(name, fallback, 'bool')

    def get_list(self, name, fallback=None):
        """Returns the configuration with the given name or the fallback name as a list.

        If the configuration cannot be found in this preset, the request will use the base preset as fallback.
        If there is no configuration with the given name, the fallback configuration will be used.

        Args:
            name(str): The name of the configuration.
            fallback(str): The name of the fallback configuration, which should be used if the primary one cannot be found.

        Returns:
            list: The list value of the configuration.

        Raises:
            NotFoundError: If the configuration cannot be found in this or any base presets.
            TypeError. If the configuration value cannot be converted into a list.
        """
        return self._get_value_with_fallback(name, fallback, 'list')

    def get_with_prefix(self, prefix):
        """Clones this preset and adds an additional prefix.

        Args:
            prefix(str): The additional prefix.

        Returns:
            Preset: The new preset with the requested prefix.
        """
        preset = Preset(base_preset=self.base_preset)
        preset.name = self.name
        preset.config = self.config
        preset.prefix = self.prefix + prefix + "/"
        preset.file = self.file
        preset.try_number = self.try_number
        preset.uuid = self.uuid
        return preset

    def get_experiment_name(self):
        """Returns the name of the described experiment.

        Returns:
            str: The experiment name.
        """
        return self.name + " (try " + str(self.try_number) + ")"

    @staticmethod
    def clear_printed_settings(new_logger):
        """Cleans the list of all already printed settings.

        After calling this, the configuration log will start from scratch again.

        Args:
            new_logger: A new logger which should be used for future logging.
        """
        Preset._printed_settings.clear()
        Preset.logger = new_logger
