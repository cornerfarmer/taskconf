import glob
import json
import re

from taskconf.config.Preset import Preset
import uuid
import fnmatch
import os

class Configuration:

    def __init__(self, config_path=None):
        """ Creates a new configuration.

        Args:
            config_path(str): The path where the config files are stored.
        """
        if config_path is None:
            config_path = "config"

        self.config_path = config_path
        self.presets = []
        self.presets_by_file = {}
        self.presets_by_uuid = {}
        self._json_by_uuid = {}
        self._ordered_preset = []

        for path in self._find_recursive(config_path, "*.json"):
            with open(path) as data_file:
                input_str = re.sub(r'^\s*//.*\n', '\n', data_file.read(), flags=re.MULTILINE)
                data = json.loads(input_str)

                for preset_data in data:

                    if not "uuid" in preset_data:
                        preset_data["uuid"] = str(uuid.uuid4())

                    if preset_data["uuid"] not in self._json_by_uuid:
                        self._json_by_uuid[preset_data["uuid"]] = {"data": preset_data, "file": path[len(config_path) + 1:]}
                        self._ordered_preset.append(preset_data["uuid"])
                    else:
                        raise Exception("A preset with uuid '" + preset_data["uuid"] + "' is already defined!")

        for preset_uuid in self._ordered_preset:
            self._load_preset_with_uuid(preset_uuid)
            self.presets.append(self.presets_by_uuid[preset_uuid])

        print("Loaded " + str(len(self.presets)) + " presets.")

    def _find_recursive(self, dir, file_ending):
        matches = []
        for root, dirnames, filenames in os.walk(dir):
            for filename in fnmatch.filter(filenames, file_ending):
                matches.append(os.path.join(root, filename))
        return matches

    def _load_preset_with_uuid(self, preset_uuid, children_presets=[]):
        """Loads the preset with the given uuid and all its base presets.

        Args:
            preset_uuid (str): The uuid of the preset.
            children_presets (list): A list of child presets. This will be used to make sure there are no cycles in the inheritance graph..

        Returns:
            Preset: The loaded preset
        """
        if not preset_uuid in self._json_by_uuid:
            raise Exception("There is no preset with uuid '" + preset_uuid + "'!")

        if preset_uuid in children_presets:
            raise Exception("There is a cycle in the presets inheritance!")

        if preset_uuid not in self.presets_by_uuid:
            preset_data = self._json_by_uuid[preset_uuid]["data"]

            if "base" in preset_data:
                base_preset_uuids = preset_data["base"]
                if not type(base_preset_uuids) is list:
                    base_preset_uuids = [base_preset_uuids]

                base_presets = []
                for base_preset_uuid in base_preset_uuids:
                    base_presets.append(self._load_preset_with_uuid(base_preset_uuid, children_presets + [preset_uuid]))
            else:
                base_presets = []

            self.create_preset(preset_data, base_presets, self._json_by_uuid[preset_uuid]["file"])

        return self.presets_by_uuid[preset_uuid]

    def create_preset(self, preset_data, base_presets, file):
        preset = Preset(preset_data, base_presets, file)

        if preset.file is not None:
            if preset.file not in self.presets_by_file:
                self.presets_by_file[preset.file] = []
            self.presets_by_file[preset.file].append(preset)

            self.presets_by_uuid[preset.uuid] = preset
        return preset

    def save_to_file(self, filename, presets):
        data = []
        for preset in presets:
            data.append(preset.data)

        if len(data) > 0 and len(filename) > 0:
            with open(self.config_path + "/" + filename, 'w+') as data_file:
                json.dump(data, data_file, indent=2, separators=(',', ': '), sort_keys=True)

    def save(self):
        for filename in self.presets_by_file.keys():
            if filename is not None:
                self.save_to_file(filename, self.presets_by_file[filename])

    def add_preset(self, preset_data, file, metadata={}):
        if "base" in preset_data:
            base_preset_uuids = preset_data["base"]
            if not type(base_preset_uuids) is list:
                base_preset_uuids = [base_preset_uuids]

            base_presets = [self.presets_by_uuid[base] for base in base_preset_uuids]
        else:
            base_presets = []

        preset = self.create_preset(preset_data, base_presets, file)
        for key in metadata:
            preset.set_metadata(key, metadata[key])
        if file is not None:
            self.presets.append(preset)
            self.save()

        return preset