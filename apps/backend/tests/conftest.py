"""
Pytest configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client for API testing"""
    return TestClient(app)


@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing"""
    return [
        {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 100,
            "price": 150.00,
            "executed_at": "2024-01-15T10:30:00-05:00",
        },
        {
            "symbol": "AAPL",
            "side": "SELL",
            "quantity": 100,
            "price": 155.00,
            "executed_at": "2024-01-20T14:00:00-05:00",
        },
    ]
