import json
import os
from tabpy.tabpy_server.app.app import TabPyApp
from tabpy.tabpy_server.app.SettingsParameters import SettingsParameters
import tempfile
from tornado.testing import AsyncHTTPTestCase


def _create_expected_info_response(settings, tabpy_state):
    return {
        "description": tabpy_state.get_description(),
        "creation_time": tabpy_state.creation_time,
        "state_path": settings["state_file_path"],
        "server_version": settings[SettingsParameters.ServerVersion],
        "name": tabpy_state.name,
        "versions": settings["versions"],
    }


class TestServiceInfoHandlerDefault(AsyncHTTPTestCase):
    def get_app(self):
        self.app = TabPyApp()
        return self.app._create_tornado_web_app()

    def test_given_vanilla_tabpy_server_expect_correct_info_response(self):
        response = self.fetch("/info")
        self.assertEqual(response.code, 200)
        actual_response = json.loads(response.body)
        expected_response = _create_expected_info_response(
            self.app.settings, self.app.tabpy_state
        )

        self.assertDictEqual(actual_response, expected_response)


class TestServiceInfoHandlerWithAuth(AsyncHTTPTestCase):
    @classmethod
    def setUpClass(cls):
        prefix = "__TestServiceInfoHandlerWithAuth_"
        # create password file
        cls.pwd_file = tempfile.NamedTemporaryFile(
            prefix=prefix, suffix=".txt", delete=False
        )
        cls.pwd_file.write(b"username password")
        cls.pwd_file.close()

        # create state.ini dir and file
        cls.state_dir = tempfile.mkdtemp(prefix=prefix)
        cls.state_file = open(os.path.join(cls.state_dir, "state.ini"), "w+")
        cls.state_file.write(
            "[Service Info]\n"
            "Name = TabPy Serve\n"
            "Description = \n"
            "Creation Time = 0\n"
            "Access-Control-Allow-Origin = \n"
            "Access-Control-Allow-Headers = \n"
            "Access-Control-Allow-Methods = \n"
            "\n"
            "[Query Objects Service Versions]\n"
            "\n"
            "[Query Objects Docstrings]\n"
            "\n"
            "[Meta]\n"
            "Revision Number = 1\n"
        )
        cls.state_file.close()

        # create config file
        cls.config_file = tempfile.NamedTemporaryFile(
            prefix=prefix, suffix=".conf", delete=False
        )
        cls.config_file.write(
            bytes(
                "[TabPy]\n"
                f"TABPY_PWD_FILE = {cls.pwd_file.name}\n"
                f"TABPY_STATE_PATH = {cls.state_dir}",
                "utf-8",
            )
        )
        cls.config_file.close()

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.pwd_file.name)
        os.remove(cls.state_file.name)
        os.remove(cls.config_file.name)
        os.rmdir(cls.state_dir)

    def get_app(self):
        self.app = TabPyApp(self.config_file.name)
        return self.app._create_tornado_web_app()

    def test_given_tabpy_server_with_auth_expect_correct_info_response(self):
        response = self.fetch("/info")
        self.assertEqual(response.code, 200)
        actual_response = json.loads(response.body)
        expected_response = _create_expected_info_response(
            self.app.settings, self.app.tabpy_state
        )

        self.assertDictEqual(actual_response, expected_response)
        self.assertTrue("versions" in actual_response)
        versions = actual_response["versions"]
        self.assertTrue("v1" in versions)
        v1 = versions["v1"]
        self.assertTrue("features" in v1)
        features = v1["features"]
        self.assertDictEqual(
            {"authentication": {"methods": {"basic-auth": {}}, "required": True}},
            features,
        )


class TestServiceInfoHandlerWithoutAuth(AsyncHTTPTestCase):
    @classmethod
    def setUpClass(cls):
        prefix = "__TestServiceInfoHandlerWithoutAuth_"

        # create state.ini dir and file
        cls.state_dir = tempfile.mkdtemp(prefix=prefix)
        with open(os.path.join(cls.state_dir, "state.ini"), "w+") as cls.state_file:
            cls.state_file.write(
                "[Service Info]\n"
                "Name = TabPy Serve\n"
                "Description = \n"
                "Creation Time = 0\n"
                "Access-Control-Allow-Origin = \n"
                "Access-Control-Allow-Headers = \n"
                "Access-Control-Allow-Methods = \n"
                "\n"
                "[Query Objects Service Versions]\n"
                "\n"
                "[Query Objects Docstrings]\n"
                "\n"
                "[Meta]\n"
                "Revision Number = 1\n"
            )
        cls.state_file.close()

        # create config file
        cls.config_file = tempfile.NamedTemporaryFile(
            prefix=prefix, suffix=".conf", delete=False, mode="w+"
        )
        cls.config_file.write("[TabPy]\n" f"TABPY_STATE_PATH = {cls.state_dir}")
        cls.config_file.close()

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.state_file.name)
        os.remove(cls.config_file.name)
        os.rmdir(cls.state_dir)

    def get_app(self):
        self.app = TabPyApp(self.config_file.name)
        return self.app._create_tornado_web_app()

    def test_tabpy_server_with_no_auth_expect_correct_info_response(self):
        response = self.fetch("/info")
        self.assertEqual(response.code, 200)
        actual_response = json.loads(response.body)
        expected_response = _create_expected_info_response(
            self.app.settings, self.app.tabpy_state
        )

        self.assertDictEqual(actual_response, expected_response)
        self.assertTrue("versions" in actual_response)
        versions = actual_response["versions"]
        self.assertTrue("v1" in versions)
        v1 = versions["v1"]
        self.assertTrue("features" in v1)
        features = v1["features"]
        self.assertDictEqual({}, features)
