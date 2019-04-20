from taskconf.config.Configuration import Configuration
import os

class TestConfig(object):
    def get_config(self):
        return Configuration(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config"))

    def test_simple_config(self):
        config = self.get_config()
        preset = config.presets_by_uuid["1fd468af-446f-4394-ae43-2d441e8c7575"]
        assert preset.get_int("x") == 2

    def test_inheritance_config(self):
        config = self.get_config()
        preset = config.presets_by_uuid["2fd468af-446f-4394-ae43-2d441e8c7575"]
        assert preset.get_int("a") == 25
        assert preset.get_int("x") == 8
        assert preset.get_int("y") == 51

    def test_multiple_inheritance_config(self):
        config = self.get_config()
        preset = config.presets_by_uuid["8fd468af-446f-4394-ae43-2d441e8c7575"]
        assert preset.get_int("a") == 25
        assert preset.get_int("c") == 99
        assert preset.get_int("d") == 25
        assert preset.get_int("e") == 77
        assert preset.get_int("x") == 8
        assert preset.get_int("y") == 51


    def test_timesteps_config(self):
        config = self.get_config()
        preset = config.presets_by_uuid["3fd468af-446f-4394-ae43-2d441e8c7575"]
        assert preset.get_int("w") == 100
        assert preset.get_int("z") == 24
        preset.iteration_cursor = 10
        assert preset.get_int("w") == 100
        assert preset.get_int("z") == 30
        preset.iteration_cursor = 20
        assert preset.get_int("w") == 100
        assert preset.get_int("z") == 30

    def test_timesteps_inheritance_config(self):
        config = self.get_config()
        preset = config.presets_by_uuid["4fd468af-446f-4394-ae43-2d441e8c7575"]
        assert preset.get_int("w") == 150
        assert preset.get_int("z") == 24
        preset.iteration_cursor = 10
        assert preset.get_int("b") == 12
        assert preset.get_int("c") == 321
        assert preset.get_int("w") == 150
        assert preset.get_int("z") == 30
        preset.iteration_cursor = 20
        assert preset.get_int("b") == 12
        assert preset.get_int("c") == 321
        assert preset.get_int("w") == 150
        assert preset.get_int("z") == 45



