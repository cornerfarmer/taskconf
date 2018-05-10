import glob
import json
import re

from config.Preset import Preset


class Configuration:

    def __init__(self, config_path=None, default_preset_name="Default"):
        """ Creates a new configuration.

        Args:
            config_path(str): The path where the config files are stored.
            default_preset_name(str): The name of the default base preset.
        """
        if config_path is None:
            config_path = "config"

        self.config_path = config_path
        self.presets = []
        self.presets_by_name = {}
        self.presets_by_uuid = {}
        self._json_by_name = {}
        self._ordered_names = []
        self.default_preset_name = default_preset_name

        for path in glob.iglob(config_path + "/**/*.json", recursive=True):
            with open(path) as data_file:
                input_str = re.sub(r'^\s*//.*\n', '\n', data_file.read(), flags=re.MULTILINE)
                data = json.loads(input_str)

                for preset_data in data:

                    if not "name" in preset_data:
                        raise Exception("The given preset has no name!")

                    if preset_data["name"] not in self._json_by_name:
                        self._json_by_name[preset_data["name"]] = {"data": preset_data, "file": path[len(config_path) + 1:]}
                        self._ordered_names.append(preset_data["name"])
                    else:
                        raise Exception("A preset with name '" + preset_data["name"] + "' is already defined!")

        for name in self._ordered_names:
            self._load_preset_with_name(name)
            self.presets.append(self.presets_by_name[name])

        self.save()

        print("Loaded " + str(len(self.presets)) + " presets.")

    def _load_preset_with_name(self, preset_name, children_presets=[]):
        """Loads the preset with the given name and all its base presets.

        Args:
            preset_name (str): The name of the preset.
            children_presets (list): A list of child presets. This will be used to make sure there are no cycles in the inheritance graph..

        Returns:
            Preset: The loaded preset
        """
        if not preset_name in self._json_by_name:
            raise Exception("There is no preset with name '" + preset_name + "'!")

        if preset_name in children_presets:
            raise Exception("There is a cycle in the presets inheritance!")

        if preset_name not in self.presets_by_name:
            preset_data = self._json_by_name[preset_name]["data"]

            if "base" in preset_data:
                preset_base = self._load_preset_with_name(preset_data["base"], children_presets + [preset_name])
            elif preset_name != self.default_preset_name:
                preset_base = self._load_preset_with_name(self.default_preset_name, children_presets + [preset_name])
            else:
                preset_base = None

            self.create_preset(preset_data, preset_base, self._json_by_name[preset_name]["file"])

        return self.presets_by_name[preset_name]

    def create_preset(self, preset_data, preset_base, file):
        preset = Preset(preset_data, preset_base, file)
        self.presets_by_name[preset.name] = preset
        self.presets_by_uuid[preset.uuid] = preset
        return preset

    def find_presets_by_names(self, names):
        """Returns all presets with the given names.

        The method will only return non-abstract presets.

        Args:
            names(list): A list of preset names.

        Returns:
            list: The list of presets.
        """
        presets = []

        for name in names:
            if name in self.presets_by_name:
                if not self.presets_by_name[name].abstract:
                    presets.append(self.presets_by_name[name])

        return presets

    def find_presets_by_files(self, files):
        """Returns all presets from the given files.

        The method will only return non-abstract presets.

        Args:
            files(list): A list of config filenames which presets should be returned.

        Returns:
            list: The list of presets.
        """
        presets = []

        for preset in self.presets:
            if preset.file in files:
                if not preset.abstract:
                    presets.append(preset)

        return presets

    def find(self, names, files):
        """Returns all presets with the given names or from the given files.

        The method will only return non-abstract presets.
        If both given parameters are empty, all presets are returned.

        Args:
            names: A list of preset names.
            files: A list of config filenames which presets should be returned.

        Returns:
            list: The list of presets.
        """
        if len(names) + len(files) == 0:
            presets = [preset for preset in self.presets if not preset.abstract]
        else:
            presets = self.find_presets_by_names(names) + self.find_presets_by_files(files)

        return presets

    def save_to_file(self, filename, presets):
        data = []
        for preset in presets:
            data.append(preset.data)

        if len(data) > 0 and len(filename) > 0:
            with open(self.config_path + "/" + filename, 'w') as data_file:
                json.dump(data, data_file, indent=2, separators=(',', ': '))

    def save(self):
        filename = ""
        presets = []
        for preset in self.presets:
            if filename != preset.file:
                self.save_to_file(filename, presets)
                presets = [preset]
                filename = preset.file
            else:
                presets.append(preset)

        self.save_to_file(filename, presets)

    def add_preset(self, preset_data):
        if "base" in preset_data:
            preset_base = self.presets_by_name[preset_data]
        else:
            preset_base = self.presets_by_name[self.default_preset_name]

        preset = self.create_preset(preset_data, preset_base, self.presets[-1].file)
        self.presets.append(preset)
        self.save()

        return preset