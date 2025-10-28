"""
Tests for ingest API endpoints
"""
import pytest
from io import BytesIO


@pytest.mark.integration
def test_ingest_unified_csv_success(client):
    """Test successful CSV upload with unified format"""
    csv_content = """symbol,side,quantity,price,executed_at
AAPL,BUY,100,150.00,2024-01-15T10:30:00-05:00
AAPL,SELL,100,155.00,2024-01-20T14:00:00-05:00"""
    
    files = {"file": ("test.csv", BytesIO(csv_content.encode()), "text/csv")}
    data = {"template": "unified_v1"}
    
    response = client.post("/api/v1/ingest/", files=files, data=data)
    
    assert response.status_code == 200
    result = response.json()
    
    assert result["status"] == "completed"
    assert result["trades_processed"] == 2
    assert result["trades_failed"] == 0
    assert "job_id" in result


@pytest.mark.integration
def test_ingest_webull_csv_success(client):
    """Test successful CSV upload with Webull format"""
    csv_content = """Symbol,Action,Quantity,Price,Time
AAPL,BUY,100,150.00,2024-01-15 10:30:00
TSLA,SELL,50,200.00,2024-01-20 14:00:00"""
    
    files = {"file": ("webull.csv", BytesIO(csv_content.encode()), "text/csv")}
    data = {"template": "webull_v1"}
    
    response = client.post("/api/v1/ingest/", files=files, data=data)
    
    assert response.status_code == 200
    result = response.json()
    
    assert result["status"] == "completed"
    assert result["trades_processed"] == 2


@pytest.mark.integration
def test_ingest_robinhood_csv_success(client):
    """Test successful CSV upload with Robinhood format"""
    csv_content = """Symbol,Side,Shares,Price,Date
AAPL,buy,100,150.00,2024-01-15T10:30:00-05:00
TSLA,sell,50.5,200.00,2024-01-20T14:00:00-05:00"""
    
    files = {"file": ("robinhood.csv", BytesIO(csv_content.encode()), "text/csv")}
    data = {"template": "robinhood_v1"}
    
    response = client.post("/api/v1/ingest/", files=files, data=data)
    
    assert response.status_code == 200
    result = response.json()
    
    assert result["status"] == "completed"
    assert result["trades_processed"] == 2


@pytest.mark.integration
def test_ingest_invalid_template(client):
    """Test error for invalid template"""
    csv_content = """symbol,side,quantity,price,executed_at
AAPL,BUY,100,150.00,2024-01-15T10:30:00-05:00"""
    
    files = {"file": ("test.csv", BytesIO(csv_content.encode()), "text/csv")}
    data = {"template": "invalid_template"}
    
    response = client.post("/api/v1/ingest/", files=files, data=data)
    
    assert response.status_code == 400
    assert "Invalid template" in response.json()["detail"]


@pytest.mark.integration
def test_ingest_non_csv_file(client):
    """Test error for non-CSV file"""
    content = b"Not a CSV file"
    
    files = {"file": ("test.txt", BytesIO(content), "text/plain")}
    data = {"template": "unified_v1"}
    
    response = client.post("/api/v1/ingest/", files=files, data=data)
    
    assert response.status_code == 400
    assert "CSV" in response.json()["detail"]


@pytest.mark.integration
def test_ingest_missing_required_columns(client):
    """Test error for missing required columns"""
    csv_content = """symbol,side,price,executed_at
AAPL,BUY,150.00,2024-01-15T10:30:00-05:00"""
    
    files = {"file": ("test.csv", BytesIO(csv_content.encode()), "text/csv")}
    data = {"template": "unified_v1"}
    
    response = client.post("/api/v1/ingest/", files=files, data=data)
    
    assert response.status_code == 400
    assert "Missing required columns" in response.json()["detail"]


@pytest.mark.integration
def test_ingest_partial_failures(client):
    """Test that valid rows are processed even with some failures"""
    csv_content = """symbol,side,quantity,price,executed_at
AAPL,BUY,100,150.00,2024-01-15T10:30:00-05:00
INVALID,BUY,-50,200.00,2024-01-16T10:30:00-05:00
TSLA,SELL,25,300.00,2024-01-17T10:30:00-05:00"""
    
    files = {"file": ("test.csv", BytesIO(csv_content.encode()), "text/csv")}
    data = {"template": "unified_v1"}
    
    response = client.post("/api/v1/ingest/", files=files, data=data)
    
    assert response.status_code == 200
    result = response.json()
    
    assert result["status"] == "completed"
    assert result["trades_processed"] == 2
    assert result["trades_failed"] == 1
    assert result["errors"] is not None
    assert len(result["errors"]) == 1


@pytest.mark.integration
def test_ingest_all_failures(client):
    """Test response when all trades fail validation"""
    csv_content = """symbol,side,quantity,price,executed_at
AAPL,BUY,-100,150.00,2024-01-15T10:30:00-05:00
TSLA,INVALID,50,200.00,2024-01-16T10:30:00-05:00"""
    
    files = {"file": ("test.csv", BytesIO(csv_content.encode()), "text/csv")}
    data = {"template": "unified_v1"}
    
    response = client.post("/api/v1/ingest/", files=files, data=data)
    
    assert response.status_code == 200
    result = response.json()
    
    assert result["status"] == "failed"
    assert result["trades_processed"] == 0
    assert result["trades_failed"] == 2


@pytest.mark.integration
def test_ingest_with_account_id(client):
    """Test CSV upload with account_id parameter"""
    csv_content = """symbol,side,quantity,price,executed_at
AAPL,BUY,100,150.00,2024-01-15T10:30:00-05:00"""
    
    files = {"file": ("test.csv", BytesIO(csv_content.encode()), "text/csv")}
    data = {"template": "unified_v1", "account_id": "TEST_ACCOUNT"}
    
    response = client.post("/api/v1/ingest/", files=files, data=data)
    
    assert response.status_code == 200
    result = response.json()
    
    assert result["status"] == "completed"


@pytest.mark.integration
def test_list_templates(client):
    """Test listing available templates"""
    response = client.get("/api/v1/ingest/templates")
    
    assert response.status_code == 200
    result = response.json()
    
    assert "templates" in result
    assert len(result["templates"]) == 3
    
    template_ids = [t["id"] for t in result["templates"]]
    assert "webull_v1" in template_ids
    assert "robinhood_v1" in template_ids
    assert "unified_v1" in template_ids
