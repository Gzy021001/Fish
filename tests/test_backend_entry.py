import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class BackendEntryTests(unittest.TestCase):
    def test_default_sqlite_path_points_to_backend_database_file(self):
        expected_db_path = (REPO_ROOT / "backend" / "fish_price.db").resolve()

        with patch.dict(
            os.environ,
            {"POSTGRES_URL": "", "DATABASE_URL": "", "VERCEL": ""},
            clear=False,
        ):
            for module_name in ("backend.main", "backend.app", "app", "database", "backend.database"):
                sys.modules.pop(module_name, None)

            importlib.import_module("backend.main")
            database_module = sys.modules.get("database") or sys.modules["backend.database"]

        self.assertEqual(Path(database_module.engine.url.database).resolve(), expected_db_path)

    def test_backend_main_can_be_imported_from_project_root(self):
        module = importlib.import_module("backend.main")
        self.assertIsNotNone(module.app)


if __name__ == "__main__":
    unittest.main()
