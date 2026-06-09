import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from backend.routers import species as species_router
from backend.services.species_service import serialize_species_list


class SpeciesLightweightTests(unittest.TestCase):
    def test_serialize_species_list_keeps_image_by_default(self):
        item = SimpleNamespace(
            id=1,
            name_zh="鲫鱼",
            default_unit="斤",
            default_price=12.5,
            image_url="https://cdn.example.com/fish.png",
            supplier_name="供应商A",
            supplier_note=None,
            release_date="2026-01-01",
            created_at="2026-01-01T00:00:00",
        )

        result = serialize_species_list([item], include_images=True)

        self.assertEqual(result[0]["image_url"], "https://cdn.example.com/fish.png")

    def test_serialize_species_list_strips_image_when_disabled(self):
        item = SimpleNamespace(
            id=1,
            name_zh="鲫鱼",
            default_unit="斤",
            default_price=12.5,
            image_url="data:image/png;base64,abc",
            supplier_name="供应商A",
            supplier_note=None,
            release_date="2026-01-01",
            created_at="2026-01-01T00:00:00",
        )

        result = serialize_species_list([item], include_images=False)

        self.assertIsNone(result[0]["image_url"])
        self.assertEqual(result[0]["name_zh"], "鲫鱼")

    def test_list_species_route_uses_separate_cache_key_for_lightweight_mode(self):
        item = SimpleNamespace(
            id=1,
            name_zh="鲫鱼",
            default_unit="斤",
            default_price=12.5,
            image_url="data:image/png;base64,abc",
            supplier_name="供应商A",
            supplier_note=None,
            release_date="2026-01-01",
            created_at="2026-01-01T00:00:00",
        )
        cache_mock = SimpleNamespace(get=lambda key: None, set=lambda key, value: None)

        with patch.object(species_router, "species_cache", cache_mock):
            with patch.object(species_router, "list_species", return_value=[item]):
                with patch.object(species_router, "serialize_species_list") as serialize_mock:
                    serialize_mock.return_value = [{"id": 1, "image_url": None}]

                    result = species_router.list_species_route(
                        q=None,
                        include_images=False,
                        db=None,
                        current_user=SimpleNamespace(id=1),
                    )

        serialize_mock.assert_called_once_with([item], include_images=False)
        self.assertEqual(result, [{"id": 1, "image_url": None}])


if __name__ == "__main__":
    unittest.main()
