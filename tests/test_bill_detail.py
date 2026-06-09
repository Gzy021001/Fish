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

from backend.routers import bills as bills_router
from backend.services import bill_service


class BillDetailTests(unittest.TestCase):
    def test_get_bill_returns_requested_bill(self):
        bill = SimpleNamespace(id=12)
        query = SimpleNamespace(
            options=lambda *args, **kwargs: query,
            filter=lambda *args, **kwargs: query,
            first=lambda: bill,
        )
        db = SimpleNamespace(query=lambda *args, **kwargs: query)

        with patch.object(bill_service, "get_bill_or_404", return_value=bill) as get_bill_mock:
            result = bill_service.get_bill(12, db=db)

        get_bill_mock.assert_not_called()
        self.assertEqual(result.id, 12)

    def test_get_bill_route_uses_service_result(self):
        bill = SimpleNamespace(id=8)

        with patch.object(bills_router, "get_bill", return_value=bill) as get_bill_mock:
            result = bills_router.get_bill_route(
                bill_id=8,
                db=SimpleNamespace(),
                current_user=SimpleNamespace(id=1),
            )

        get_bill_mock.assert_called_once()
        self.assertEqual(result.id, 8)


if __name__ == "__main__":
    unittest.main()
