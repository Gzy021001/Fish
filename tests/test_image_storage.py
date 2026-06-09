import base64
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import UploadFile
from starlette.datastructures import Headers

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from backend.services import species_service
from backend.services.image_storage import store_image_asset


class ImageStorageTests(unittest.TestCase):
    def test_store_image_asset_returns_local_upload_url_outside_vercel(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(
                os.environ,
                {
                    "UPLOADS_DIR": temp_dir,
                },
                clear=False,
            ):
                os.environ.pop("VERCEL", None)
                os.environ.pop("IMAGE_STORAGE_MODE", None)
                os.environ.pop("SUPABASE_URL", None)
                os.environ.pop("SUPABASE_SERVICE_ROLE_KEY", None)
                os.environ.pop("SUPABASE_STORAGE_BUCKET", None)

                result = store_image_asset(b"fake-image", "image/png", folder="species")

                self.assertTrue(result.startswith("/uploads/species/"))
                saved_name = result.replace("/uploads/species/", "", 1)
                saved_path = Path(temp_dir) / "species" / saved_name
                self.assertTrue(saved_path.exists())

    def test_store_image_asset_falls_back_to_base64_on_vercel_without_storage(self):
        with patch.dict(
            os.environ,
            {
                "VERCEL": "1",
            },
            clear=False,
        ):
            os.environ.pop("IMAGE_STORAGE_MODE", None)
            os.environ.pop("SUPABASE_URL", None)
            os.environ.pop("SUPABASE_SERVICE_ROLE_KEY", None)
            os.environ.pop("SUPABASE_STORAGE_BUCKET", None)

            result = store_image_asset(b"abc", "image/png", folder="species")

            self.assertEqual(
                result,
                "data:image/png;base64," + base64.b64encode(b"abc").decode("utf-8"),
            )

    def test_upload_image_persists_generated_image_src(self):
        species = SimpleNamespace(image_url=None)
        upload = UploadFile(
            filename="fish.png",
            file=io.BytesIO(b"fake-bytes"),
            headers=Headers({"content-type": "image/png"}),
        )
        db = SimpleNamespace(commit=lambda: None, refresh=lambda obj: None)

        with patch.object(species_service, "get_species", return_value=species):
            with patch.object(
                species_service,
                "store_image_asset",
                return_value="/uploads/species/test.png",
            ):
                result = species_service.upload_image(1, upload, db)

        self.assertEqual(result.image_url, "/uploads/species/test.png")


if __name__ == "__main__":
    unittest.main()
