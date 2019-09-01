import glob
import json
import re

from taskconf.config.Configuration import Configuration
import uuid
import fnmatch
import os

class ConfigurationManager:

    def __init__(self, config_path=None):
        """ Creates a new configuration.

        Args:
            config_path(str): The path where the config files are stored.
        """
        if config_path is None:
            config_path = "config"

        self.config_path = config_path
        self.configs = []
        self.configs_by_file = {}
        self.configs_by_uuid = {}
        self._json_by_uuid = {}
        self._ordered_configs = []

        for path in self._find_recursive(config_path, "*.json"):
            with open(path) as data_file:
                input_str = re.sub(r'^\s*//.*\n', '\n', data_file.read(), flags=re.MULTILINE)
                data = json.loads(input_str)

                for config_data in data:

                    if not "uuid" in config_data:
                        config_data["uuid"] = str(uuid.uuid4())

                    if config_data["uuid"] not in self._json_by_uuid:
                        self._json_by_uuid[config_data["uuid"]] = {"data": config_data, "file": path[len(config_path) + 1:]}
                        self._ordered_configs.append(config_data["uuid"])
                    else:
                        raise Exception("A config with uuid '" + config_data["uuid"] + "' is already defined!")

        for config_uuid in self._ordered_configs:
            self._load_config_with_uuid(config_uuid)
            self.configs.append(self.configs_by_uuid[config_uuid])

        print("Loaded " + str(len(self.configs)) + " configs.")

    def _find_recursive(self, dir, file_ending):
        matches = []
        for root, dirnames, filenames in os.walk(dir):
            for filename in fnmatch.filter(filenames, file_ending):
                matches.append(os.path.join(root, filename))
        return matches

    def _load_config_with_uuid(self, config_uuid, children_configs=[]):
        """Loads the config with the given uuid and all its base configs.

        Args:
            config_uuid (str): The uuid of the config.
            children_configs (list): A list of child configs. This will be used to make sure there are no cycles in the inheritance graph..

        Returns:
            Configuration: The loaded config
        """
        if not config_uuid in self._json_by_uuid:
            raise Exception("There is no config with uuid '" + config_uuid + "'!")

        if config_uuid in children_configs:
            raise Exception("There is a cycle in the config inheritance!")

        if config_uuid not in self.configs_by_uuid:
            config_data = self._json_by_uuid[config_uuid]["data"]

            if "base" in config_data:
                base_config_uuids = config_data["base"]
                if not type(base_config_uuids) is list:
                    base_config_uuids = [base_config_uuids]

                base_configs = []
                for base_config_uuid in base_config_uuids:
                    if not type(base_config_uuid) is list:
                        base_config_uuid = [base_config_uuid]
                    base_configs.append([self._load_config_with_uuid(base_config_uuid[0], children_configs + [config_uuid])] + base_config_uuid[1:])
            else:
                base_configs = []

            self.create_config(config_data, base_configs, self._json_by_uuid[config_uuid]["file"])

        return self.configs_by_uuid[config_uuid]

    def create_config(self, config_data, base_configs, file):
        config = Configuration(config_data, base_configs, file)

        if config.file is not None:
            if config.file not in self.configs_by_file:
                self.configs_by_file[config.file] = []
            self.configs_by_file[config.file].append(config)

            self.configs_by_uuid[config.uuid] = config
        return config

    def save_to_file(self, filename, configs):
        data = []
        for config in configs:
            data.append(config.data)

        if len(data) > 0 and len(filename) > 0:
            with open(self.config_path + "/" + filename, 'w+') as data_file:
                json.dump(data, data_file, indent=2, separators=(',', ': '), sort_keys=True)

    def save(self):
        for filename in self.configs_by_file.keys():
            if filename is not None:
                self.save_to_file(filename, self.configs_by_file[filename])

    def add_config(self, config_data, file, metadata={}):
        if "base" in config_data:
            base_config_uuids = config_data["base"]
            if not type(base_config_uuids) is list:
                base_config_uuids = [base_config_uuids]

            base_config_uuids = [[base_config_uuid] if not type(base_config_uuid) is list else base_config_uuid for base_config_uuid in base_config_uuids]
            base_configs = [[self.configs_by_uuid[base[0]]] + base[1:] for base in base_config_uuids]
        else:
            base_configs = []

        config = self.create_config(config_data, base_configs, file)
        for key in metadata:
            config.set_metadata(key, metadata[key])
        if file is not None:
            self.configs.append(config)
            self.save()

        return config

    def remove_config(self, config):
        self.configs.remove(config)
        if config.file is not None:
            self.configs_by_file[config.file].remove(config)
        del self.configs_by_uuid[str(config.uuid)]

        self.save()