import datetime
import logging
import uuid

from taskconf.config.ConfigurationBlock import ConfigurationBlock, NotFoundError
import collections
import copy
import time

class Preset:

    def __init__(self, data=None, base_preset=None, file=None):
        """Creates a new preset.

        Args:
            data(dict): The raw json data of the preset.
            base_preset(Preset): The base preset object for this preset.
            file(str): The filename which contained the preset.
        """
        self.prefix = ""
        self.base_preset = base_preset
        self.file = file
        self.try_number = 0
        self.printed_settings = dict()
        self.logger = None
        self.iteration_cursor = 0

        if data is not None:
            self.set_data(data)
        else:
            self.data = {}
            self.name = ""
            self.uuid = ""
            self.creation_time = 0
            self.config = None
            self.abstract = False
            self.dynamic = False

    def treat_dynamic(self, simulated_base=None):
        if simulated_base is None:
            return self.dynamic or (self.base_preset is not None and self.base_preset.treat_dynamic())
        else:
            return self.dynamic or simulated_base.treat_dynamic()

    def set_data(self, new_data):
        if "uuid" not in new_data:
            new_data["uuid"] = str(uuid.uuid4())
        if "creation_time" not in new_data:
            new_data["creation_time"] = time.mktime(datetime.datetime.now().timetuple())

        self.data = new_data
        self.config = ConfigurationBlock(new_data["config"])
        self.name = new_data["name"] if "name" in new_data else self._generate_name()
        self.uuid = new_data["uuid"]
        self.creation_time = datetime.datetime.fromtimestamp(new_data["creation_time"])
        self.abstract = "abstract" in new_data and bool(new_data["abstract"])
        self.dynamic = "dynamic" in new_data and bool(new_data["dynamic"])

    def all_timesteps(self):
        if self.treat_dynamic():
            timesteps = set([int(num) for num in self.config.configBlocks.keys()])
        else:
            timesteps = {0}

        if self.base_preset is not None:
            timesteps |= self.base_preset.all_timesteps()

        return timesteps

    def _generate_name(self):
        name = ""
        if self.base_preset is not None and self.base_preset.base_preset is not None:
            name += self.base_preset.name + ": "
        flattened_data = self.config.flatten()
        for key in flattened_data:
            name += key + ": " + str(flattened_data[key]) + " - "

        if name.endswith(" - "):
            name = name[:-3]
        elif name is "":
            name = "empty"

        self.data["name"] = name
        return name

    def valid_timesteps(self, current_timestep):
        timesteps = self.all_timesteps()
        timesteps = list(filter(lambda x: x <= current_timestep, timesteps))
        timesteps.sort(reverse=True)
        return timesteps

    def _get_value_at_timestep(self, name, value_type, timestep):
        if timestep > 0 and not self.treat_dynamic():
            raise NotFoundError("Dynamic mode not enabled for preset")

        if self.treat_dynamic():
            timestep_name = str(timestep) + "/" + name
        else:
            timestep_name = name

        try:
            value = getattr(self.config, 'get_' + value_type)(timestep_name)
        except NotFoundError:
            if self.base_preset is None:
                raise
            else:
                value = self.base_preset._get_value_at_timestep(name, value_type, timestep)

        return value

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
        for timestep in self.valid_timesteps(self.iteration_cursor):
            try:
                value = self._get_value_at_timestep(name, value_type, timestep)
                return value
            except NotFoundError:
                pass

        raise NotFoundError("No such configuration '" + name + "'!")

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

        if (name not in self.printed_settings or self.printed_settings[name] != value) and self.logger is not None:
            if name not in self.printed_settings:
                self.logger.log("Using " + name + " = " + str(value))
            else:
                self.logger.log("Switching " + name + ": " + str(self.printed_settings[name]) + " -> " + str(value))
            self.printed_settings[name] = value

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
    
    def get_keys(self, name):
        return self.config.get_keys(name)

    def get_with_prefix(self, prefix):
        """Clones this preset and adds an additional prefix.

        Args:
            prefix(str): The additional prefix.

        Returns:
            Preset: The new preset with the requested prefix.
        """
        preset = self.clone(deep=False)
        preset.prefix = self.prefix + prefix + "/"
        return preset

    def clone(self, deep=True):
        preset = Preset(base_preset=self.base_preset)
        preset.name = self.name
        if deep:
            preset.config = ConfigurationBlock(self.data['config'])
            preset.data = copy.deepcopy(self.data)
        else:
            preset.config = self.config
            preset.data = self.data
        preset.prefix = self.prefix
        preset.file = self.file
        preset.try_number = self.try_number
        preset.uuid = self.uuid
        preset.creation_time = self.creation_time
        preset.iteration_cursor = self.iteration_cursor
        preset.dynamic = self.dynamic
        return preset

    def get_experiment_name(self):
        """Returns the name of the described experiment.

        Returns:
            str: The experiment name.
        """
        return self.name + " (try " + str(self.try_number) + ")"

    def set_logger(self, new_logger, printed_settings=None):
        """Cleans the list of all already printed settings.

        After calling this, the configuration log will start from scratch again.

        Args:
            new_logger: A new logger which should be used for future logging.
            printed_settings:
        """
        self.printed_settings = {} if printed_settings is None else printed_settings
        self.logger = new_logger

    def compose_config(self, simulated_base=None, force_dynamic=False):
        """Merges the config of this preset and all its base presets.

        Args:
            simulated_base: A preset which should be used as base.
            force_dynamic: True, if the composed config should in any case be dynamic.

        Returns:
            dict: The composed config
        """
        config = copy.deepcopy(self.data['config'])

        if not self.dynamic and (self.treat_dynamic(simulated_base) or force_dynamic):
            config = {'0': config}

        if self.base_preset is not None or simulated_base is not None:
            config = self._deep_update(self.base_preset.compose_config(force_dynamic=force_dynamic or self.dynamic) if simulated_base is None else simulated_base.compose_config(force_dynamic=force_dynamic or self.dynamic), config)
        return config

    def compose_config_for_timestep(self, current_timestep):
        """Merges the config of this preset and all its base presets at a given timestep.

        Args:
            current_timestep: The timestep at which the configs should be merged.

        Returns:
            dict: The merged config.
        """
        config = {}
        for timestep in self.valid_timesteps(current_timestep):
            config = self._deep_update(self._compose_single_timestep(str(timestep)), config)
        return config

    def _compose_single_timestep(self, timestep):
        if self.treat_dynamic():
            if timestep in self.data['config']:
                config = copy.deepcopy(self.data['config'][timestep])
            else:
                config = {}
        else:
            if timestep == '0':
                config = copy.deepcopy(self.data['config'])
            else:
                config = {}

        if self.base_preset is not None:
            config = self._deep_update(self.base_preset._compose_single_timestep(timestep), config)
        return config

    def _deep_update(self, d, u):
        for k, v in u.items():
            if isinstance(v, collections.Mapping):
                d[k] = self._deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def set_config_at_timestep(self, new_config, timestep):
        data = copy.deepcopy(self.data)
        if self.dynamic:
            if str(timestep) in self.data['config']:
                new_config = self._deep_update(copy.deepcopy(self.data['config'][str(timestep)]), new_config)
        else:
            data['config'] = {'0': data['config']}
            data['dynamic'] = True

        data['config'][str(timestep)] = new_config
        self.set_data(data)