class ConfigurationBlock:

    def __init__(self, data):
        """Creates a configuration block.

        Args:
            data(dict): A nested key/value structure of raw configurations.
        """
        self.data = {}
        self.configBlocks = {}

        for key, value in data.items():
            if isinstance(value, dict):
                self.configBlocks[key] = ConfigurationBlock(value)
            else:
                self.data[key] = value

    def get_value(self, name):
        """Returns the value of the configuration with the given name.

        Args:
            name(str): The name of the configuration.

        Returns:
            str: The string value of the configuration.

        Raises:
            NotFoundError: If the configuration or the configuration block could not be found.
        """
        if "/" in name:
            delimiter_pos = name.find("/")
            block_name = name[:delimiter_pos]
            if block_name in self.configBlocks:
                return self.configBlocks[block_name].get_value(name[delimiter_pos + 1:])
            else:
                raise NotFoundError("No such configuration block '" + block_name + "'!")
        else:
            if name in self.data:
                return self.data[name]
            else:
                raise NotFoundError("No such configuration '" + name + "'!")

    def get_int(self, name):
        """Returns the value of the configuration with the given name as integer.

        Args:
            name(str): The name of the configuration.

        Returns:
            int: The integer value of the configuration.

        Raises:
            TypeError: If the value could not be converted to an integer.
        """
        value = self.get_value(name)
        try:
            return int(value)
        except ValueError:
            raise TypeError("Cannot convert '" + str(value) + "' to int!")

    def get_bool(self, name):
        """Returns the value of the configuration with the given name as bool.

        Args:
            name(str): The name of the configuration.

        Returns:
            bool: The bool value of the configuration.

        Raises:
            TypeError: If the value could not be converted to a bool.
        """
        value = self.get_value(name)
        try:
            return bool(value)
        except ValueError:
            raise TypeError("Cannot convert '" + str(value) + "' to bool!")

    def get_float(self, name):
        """Returns the value of the configuration with the given name float.

        Args:
            name(str): The name of the configuration.

        Returns:
            float: The float value of the configuration.

        Raises:
            TypeError: If the value could not be converted to a float.
        """
        value = self.get_value(name)
        try:
            return float(value)
        except ValueError:
            raise TypeError("Cannot convert '" + str(value) + "' to float!")

    def get_string(self, name):
        """Returns the value of the configuration with the given name as string.

        Args:
            name(str): The name of the configuration.

        Returns:
            string: The string value of the configuration.

        Raises:
            TypeError: If the value could not be converted to a string.
        """
        value = self.get_value(name)
        try:
            return str(value)
        except ValueError:
            raise TypeError("Cannot convert '" + str(value) + "' to string!")

    def get_list(self, name):
        """Returns the value of the configuration with the given name as list.

        Args:
            name(str): The name of the configuration.

        Returns:
            list: The list value of the configuration.

        Raises:
            TypeError: If the value could not be converted to a string.
        """
        value = self.get_value(name)
        if not isinstance(value, list):
            raise TypeError("Cannot convert '" + str(value) + "' to list!")
        return value

    def get_keys(self, name):
        if name != "":
            if "/" in name:
                delimiter_pos = name.find("/")
                block_name = name[:delimiter_pos]
                name = name[delimiter_pos + 1:]
            else:
                block_name = name
                name = ""
                
            if block_name in self.configBlocks:
                return self.configBlocks[block_name].get_keys(name)
            else:
                raise NotFoundError("No such configuration block '" + block_name + "'!")
        else:
            return list(self.configBlocks.keys()) + list(self.data.keys())

    def flatten(self, prefix=''):
        data = {}
        for key in self.data.keys():
            data[prefix + key] = self.data[key]
        for key in self.configBlocks.keys():
            data.update(self.configBlocks[key].flatten(prefix + key + "/"))
        return data


class NotFoundError(Exception):
    pass
