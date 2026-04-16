import os
# Stub env vars before any import
for k, v in {
    "SUPABASE_URL": "https://fake.supabase.co",
    "SUPABASE_SERVICE_ROLE_KEY": "fake-key",
    "META_APP_SECRET": "fake-secret",
    "META_WEBHOOK_VERIFY_TOKEN": "fake-token",
    "ANTHROPIC_API_KEY": "fake-key",
    "TELEGRAM_BOT_TOKEN": "fake-token",
}.items():
    os.environ[k] = os.environ.get(k) or v

from unittest.mock import patch, MagicMock
from services.orders import create_order, update_order_status, get_pending_orders


def _result(data):
    m = MagicMock()
    m.data = data
    return m


def test_create_order_returns_inserted_row():
    with patch("services.orders.get_supabase") as mock_sb:
        (mock_sb.return_value.table.return_value
         .insert.return_value.execute.return_value) = _result([{"id": "order-123"}])
        result = create_order(
            tenant_id="tenant-1",
            page_id="page-1",
            sender_id="sender-1",
            sender_name="Juan",
            contact_number="09171234567",
            items=[{"name": "Milk Tea", "qty": 2, "price": 120}],
            total_price=240,
            pickup_time="3pm",
            notes="less sugar",
        )
        assert result["id"] == "order-123"


def test_update_order_status_returns_updated_row():
    with patch("services.orders.get_supabase") as mock_sb:
        (mock_sb.return_value.table.return_value
         .update.return_value.eq.return_value.execute.return_value) = _result([{"id": "order-123", "status": "approved"}])
        result = update_order_status("order-123", "approved")
        assert result["status"] == "approved"


def test_get_pending_orders_returns_list():
    with patch("services.orders.get_supabase") as mock_sb:
        (mock_sb.return_value.table.return_value
         .select.return_value.eq.return_value.eq.return_value
         .order.return_value.execute.return_value) = _result([{"id": "order-1", "status": "pending"}])
        result = get_pending_orders("tenant-1")
        assert len(result) == 1
        assert result[0]["id"] == "order-1"
