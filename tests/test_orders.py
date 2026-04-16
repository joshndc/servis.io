import os
for k, v in {
    "SUPABASE_URL": "https://fake.supabase.co",
    "SUPABASE_SERVICE_ROLE_KEY": "fake-key",
    "META_APP_SECRET": "fake-secret",
    "META_WEBHOOK_VERIFY_TOKEN": "fake-token",
    "ANTHROPIC_API_KEY": "fake-key",
    "TELEGRAM_BOT_TOKEN": "fake-token",
}.items():
    os.environ[k] = os.environ.get(k) or v

from unittest.mock import MagicMock, patch

def test_create_order_calls_supabase():
    mock_sb = MagicMock()
    mock_sb.table.return_value.insert.return_value.execute.return_value.data = [{"id": "order-123"}]
    with patch("services.orders.get_supabase", return_value=mock_sb):
        from services.orders import create_order
        result = create_order(
            tenant_id="tenant-1",
            page_id="page-1",
            sender_id="sender-1",
            sender_name="Juan",
            contact_number="09171234567",
            items=[{"name": "Milk Tea", "qty": 2, "price": 120}],
            total_price=240,
            pickup_time="3pm",
            notes="less sugar"
        )
        assert result["id"] == "order-123"

def test_update_order_status_calls_supabase():
    mock_sb = MagicMock()
    mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{"id": "order-123", "status": "approved"}]
    with patch("services.orders.get_supabase", return_value=mock_sb):
        from services.orders import update_order_status
        result = update_order_status("order-123", "approved")
        assert result["status"] == "approved"

def test_get_pending_orders_returns_list():
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value.data = [
        {"id": "order-1", "status": "pending"}
    ]
    with patch("services.orders.get_supabase", return_value=mock_sb):
        from services.orders import get_pending_orders
        result = get_pending_orders("tenant-1")
        assert len(result) == 1
        assert result[0]["id"] == "order-1"
