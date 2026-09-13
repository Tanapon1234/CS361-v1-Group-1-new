import unittest

from fakes import *  # noqa: F401,F403 - sets sys.path
from validation import InvalidFacultyIdError, validate_faculty_id


class TestValidFacultyIds(unittest.TestCase):
    def test_accepts_simple_and_hyphenated_ids(self):
        for value in ("eng", "science", "eng-01", "faculty-of-engineering", "a", "0", "cs361"):
            with self.subTest(value=value):
                self.assertEqual(validate_faculty_id(value), value)


class TestInvalidFacultyIds(unittest.TestCase):
    def _reject(self, value, expected_reason=None):
        with self.assertRaises(InvalidFacultyIdError) as ctx:
            validate_faculty_id(value)
        if expected_reason:
            self.assertEqual(ctx.exception.reason, expected_reason)

    def test_empty_id(self):
        self._reject("", "empty_id")
        self._reject("   ", "empty_id")

    def test_missing_id(self):
        self._reject(None, "missing_id")
        self._reject(123, "missing_id")

    def test_path_traversal(self):
        for value in ("../", "..", "../../etc/passwd", "eng/../source", "..%2f"):
            with self.subTest(value=value):
                self._reject(value)

    def test_slash_and_backslash(self):
        for value in ("eng/sub", "/eng", "eng\\sub", "\\", "serving/faculties/eng"):
            with self.subTest(value=value):
                self._reject(value, "path_traversal")

    def test_control_characters(self):
        for value in ("eng\n", "eng\t", "eng\x00", "\x7f"):
            with self.subTest(value=repr(value)):
                self._reject(value, "control_character")

    def test_percent_encoded_input_is_rejected(self):
        for value in ("%2e%2e%2f", "%2f", "%5c", "eng%20science"):
            with self.subTest(value=value):
                self._reject(value)

    def test_format_rules(self):
        for value in ("ENG", "Eng", "eng_science", "eng.json", "-eng", "eng-", "eng--sci", "eng sci"):
            with self.subTest(value=value):
                self._reject(value, "invalid_format")

    def test_too_long(self):
        self._reject("a" * 65, "too_long")


if __name__ == "__main__":
    unittest.main()
