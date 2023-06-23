"""Test case utils for Jaseci."""

import inspect
import os
from abc import ABC, abstractmethod
from unittest import TestCase as _TestCase


class TestCase(_TestCase):
    """Base test case for Jaseci."""

    def setUp(self) -> None:
        """Set up test case."""
        return super().setUp()

    def tearDown(self) -> None:
        """Tear down test case."""
        return super().tearDown()

    def load_fixture(self, fixture: str) -> str:
        """Load fixture from fixtures directory."""
        fixture_src = inspect.getmodule(inspect.currentframe().f_back).__file__
        fixture_path = os.path.join(os.path.dirname(fixture_src), "fixtures", fixture)
        with open(fixture_path, "r") as f:
            return f.read()

    def file_to_str(self, file_path: str) -> str:
        """Load fixture from fixtures directory."""
        with open(file_path, "r") as f:
            return f.read()

    def fixture_abs_path(self, fixture: str) -> str:
        """Load fixture from fixtures directory."""
        fixture_src = inspect.getmodule(inspect.currentframe().f_back).__file__
        file_path = os.path.join(os.path.dirname(fixture_src), "fixtures", fixture)
        return os.path.abspath(file_path)


class TestCaseMicroSuite(ABC, TestCase):
    """Base test case for Jaseci."""

    @classmethod
    def self_attach_micro_tests(cls) -> None:
        """Attach micro tests."""
        directory = os.path.dirname(__file__) + "/../jac/tests/fixtures/micro"
        for filename in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, filename)) and filename.endswith(
                ".jac"
            ):
                method_name = f"test_micro_{filename.replace('.jac', '')}"
                file_path = os.path.join(directory, filename)
                setattr(
                    cls, method_name, lambda self, f=file_path: self.micro_suite_test(f)
                )

        def test_micro_jac_files_fully_tested(self) -> None:  # noqa: ANN001
            """Test that all micro jac files are fully tested."""
            self.directory = os.path.dirname(__file__) + "/../jac/tests/fixtures/micro"
            for filename in os.listdir(self.directory):
                if os.path.isfile(os.path.join(self.directory, filename)):
                    method_name = f"test_micro_{filename.replace('.jac', '')}"
                    self.assertIn(method_name, dir(self))

        cls.test_micro_jac_files_fully_tested = test_micro_jac_files_fully_tested

    @abstractmethod
    def micro_suite_test(self, filename: str) -> None:
        """Test micro jac file."""
        pass
