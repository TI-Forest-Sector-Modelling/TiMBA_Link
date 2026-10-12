
import importlib
import pkgutil
import unittest
from pathlib import Path

import linking_pipeline


class TestTiMBALinkImports(unittest.TestCase):
    """Tests whether all TiMBA_Link modules can be imported."""

    def test_import_all_timba_link_modules(self):
        package_path = Path(linking_pipeline.__file__).parent

        for _, module_name, _ in pkgutil.walk_packages(
            [str(package_path)],
            linking_pipeline.__name__ + ".",
        ):
            with self.subTest(module=module_name):
                importlib.import_module(module_name)


if __name__ == "__main__":
    unittest.main()
