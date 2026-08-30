from __future__ import annotations

import importlib.util
import unittest


class LesterProgrammingSchoolModuleTests(unittest.TestCase):
    def test_module_exists(self) -> None:
        self.assertIsNotNone(importlib.util.find_spec("scripts.lester_programming_school"))


if __name__ == "__main__":
    unittest.main()
