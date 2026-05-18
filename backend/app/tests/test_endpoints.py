import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies import get_db_client
from app.core.auth import get_current_user_id, get_current_user_token

# ──────────────────────────────────────────────────────────────
# Mocks
# ──────────────────────────────────────────────────────────────
class MockSupabaseTable:
    def __init__(self, data=None):
        self._data = data or []

    def select(self, *args, **kwargs):
        return self

    def insert(self, *args, **kwargs):
        return self

    def update(self, *args, **kwargs):
        return self

    def delete(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def single(self, *args, **kwargs):
        return self

    def execute(self):
        class MockResult:
            def __init__(self, data):
                self.data = data
        return MockResult(self._data)


class MockSupabaseClient:
    def __init__(self):
        self.table_data = {
            "accounts": [{"id": "acc-1", "name": "Test Account", "is_active": True, "currency": "TRY"}],
            "v_confirmed_transactions": [{"id": "tx-1", "amount": 1500.00, "direction": "expense", "month": "2026-05"}],
            "transaction_drafts": [{"id": "dr-1", "amount": 250.00, "direction": "expense", "month": "2026-05"}]
        }

    def table(self, name):
        return MockSupabaseTable(self.table_data.get(name, []))

    def rpc(self, name, params=None):
        class MockRpcResult:
            def execute(self):
                class MockRpcData:
                    def __init__(self, data):
                        self.data = data
                return MockRpcData("rpc-mock-uuid-success")
        return MockRpcResult()


# Mock dependency overrides
async def override_get_current_user_token():
    return "mock-jwt-token"

async def override_get_current_user_id():
    return "mock-user-uuid"

async def override_get_db_client():
    return MockSupabaseClient()


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user_token] = override_get_current_user_token
    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    app.dependency_overrides[get_db_client] = override_get_db_client
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ──────────────────────────────────────────────────────────────
# Test Cases
# ──────────────────────────────────────────────────────────────
def test_health_check(client):
    response = client.get("/")
    assert response.status_code in (200, 404)  # main endpoint behavior or health check


def test_list_accounts(client):
    response = client.get("/api/v1/accounts")
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert len(res_json["data"]) == 1
    assert res_json["data"][0]["name"] == "Test Account"


def test_list_transactions(client):
    response = client.get("/api/v1/transactions?month=2026-05")
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert len(res_json["data"]) == 1
    assert res_json["data"][0]["amount"] == 1500.00


def test_create_manual_transaction(client):
    payload = {
        "account_id": "acc-1",
        "transaction_date": "2026-05-18",
        "description": "Market Harcaması",
        "amount": 250.50,
        "direction": "expense"
    }
    response = client.post("/api/v1/transactions/manual?month=2026-05", json=payload)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    assert "rpc-mock-uuid-success" in res_json["data"]
