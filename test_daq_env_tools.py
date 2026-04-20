import os
import json
import unittest
from daq_env_tools import restore_environment_variables_json, get_environment_variables

class TestRestoreEnvironmentVariablesJson(unittest.TestCase):
    def setUp(self):
        """
        Set up a temporary JSON file with environment variables for testing.
        """
        self.test_file = "test_env.json"
        self.test_env_vars = {
            "TEST_VAR1": "value1",
            "TEST_VAR2": "value2",
            "TEST_VAR3": "value3"
        }
        with open(self.test_file, 'w') as f:
            json.dump(self.test_env_vars, f)

    def tearDown(self):
        """
        Clean up the temporary JSON file and remove test environment variables.
        """
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        for key in self.test_env_vars.keys():
            if key in os.environ:
                del os.environ[key]

    def test_restore_environment_variables_json(self):
        """
        Test that environment variables are correctly restored from a JSON file.
        """
        restore_environment_variables_json(self.test_file)

        for key, value in self.test_env_vars.items():
            self.assertEqual(os.environ.get(key), value)

class TestGetEnvironmentVariables(unittest.TestCase):
    def setUp(self):
        """
        Set up test environment variables.
        """
        self.test_env_vars = {
            "TEST_VAR1": "value1",
            "TEST_VAR2": "value2",
            "TEST_VAR3": "value3"
        }
        for key, value in self.test_env_vars.items():
            os.environ[key] = value

    def tearDown(self):
        """
        Clean up test environment variables.
        """
        for key in self.test_env_vars.keys():
            if key in os.environ:
                del os.environ[key]

    def test_get_environment_variables(self):
        """
        Test that get_environment_variables correctly retrieves environment variables.
        """
        env_vars = get_environment_variables()
        for key, value in self.test_env_vars.items():
            self.assertIn(key, env_vars)
            self.assertEqual(env_vars[key], value)

if __name__ == "__main__":
    unittest.main()