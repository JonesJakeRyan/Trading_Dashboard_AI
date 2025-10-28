"""
Tests for CSV parser service
"""
import pytest
from app.services.csv_parser import CSVParser, CSVParserError


@pytest.mark.unit
class TestWebullParser:
    """Tests for Webull CSV format"""
    
    def test_valid_webull_csv(self):
        """Test parsing valid Webull CSV"""
        csv_content = """Symbol,Action,Quantity,Price,Time,Account
AAPL,BUY,100,150.00,2024-01-15 10:30:00,Account123
AAPL,SELL,100,155.00,2024-01-20 14:00:00,Account123"""
        
        parser = CSVParser("webull_v1")
        trades, errors = parser.parse(csv_content)
        
        assert len(trades) == 2
        assert len(errors) == 0
        
        # Check first trade
        assert trades[0]["symbol"] == "AAPL"
        assert trades[0]["side"] == "BUY"
        assert trades[0]["quantity"] == 100.0
        assert trades[0]["price"] == 150.00
        
        # Check second trade
        assert trades[1]["side"] == "SELL"
    
    def test_webull_short_sell(self):
        """Test Webull short sell mapping"""
        csv_content = """Symbol,Action,Quantity,Price,Time
SPY,Short Sell,200,450.00,2024-02-01 11:00:00"""
        
        parser = CSVParser("webull_v1")
        trades, errors = parser.parse(csv_content)
        
        assert len(trades) == 1
        assert trades[0]["side"] == "SELL"
    
    def test_webull_missing_required_column(self):
        """Test error when required column is missing"""
        csv_content = """Symbol,Action,Price,Time
AAPL,BUY,150.00,2024-01-15 10:30:00"""
        
        parser = CSVParser("webull_v1")
        
        with pytest.raises(CSVParserError) as exc_info:
            parser.parse(csv_content)
        
        assert "Missing required columns" in str(exc_info.value)
    
    def test_webull_invalid_quantity(self):
        """Test error for invalid quantity"""
        csv_content = """Symbol,Action,Quantity,Price,Time
AAPL,BUY,-100,150.00,2024-01-15 10:30:00"""
        
        parser = CSVParser("webull_v1")
        trades, errors = parser.parse(csv_content)
        
        assert len(trades) == 0
        assert len(errors) == 1
        assert "positive" in errors[0]["error"].lower()


@pytest.mark.unit
class TestRobinhoodParser:
    """Tests for Robinhood CSV format"""
    
    def test_valid_robinhood_csv(self):
        """Test parsing valid Robinhood CSV"""
        csv_content = """Symbol,Side,Shares,Price,Date
AAPL,buy,100,150.00,2024-01-15T10:30:00-05:00
AAPL,sell,100,155.00,2024-01-20T14:00:00-05:00"""
        
        parser = CSVParser("robinhood_v1")
        trades, errors = parser.parse(csv_content)
        
        assert len(trades) == 2
        assert len(errors) == 0
        
        assert trades[0]["symbol"] == "AAPL"
        assert trades[0]["side"] == "BUY"
    
    def test_robinhood_fractional_shares(self):
        """Test Robinhood fractional shares"""
        csv_content = """Symbol,Side,Shares,Price,Date
TSLA,buy,50.5,200.00,2024-01-22T09:45:00-05:00"""
        
        parser = CSVParser("robinhood_v1")
        trades, errors = parser.parse(csv_content)
        
        assert len(trades) == 1
        assert trades[0]["quantity"] == 50.5
    
    def test_robinhood_invalid_side(self):
        """Test error for invalid side value"""
        csv_content = """Symbol,Side,Shares,Price,Date
AAPL,transfer,100,150.00,2024-01-15T10:30:00-05:00"""
        
        parser = CSVParser("robinhood_v1")
        trades, errors = parser.parse(csv_content)
        
        assert len(trades) == 0
        assert len(errors) == 1
        assert "side" in errors[0]["error"].lower()


@pytest.mark.unit
class TestUnifiedParser:
    """Tests for Unified CSV format"""
    
    def test_valid_unified_csv(self):
        """Test parsing valid Unified CSV"""
        csv_content = """symbol,side,quantity,price,executed_at,account_id,notes
AAPL,BUY,100,150.00,2024-01-15T10:30:00-05:00,ACCT001,Test trade
AAPL,SELL,100,155.00,2024-01-20T14:00:00-05:00,ACCT001,"""
        
        parser = CSVParser("unified_v1")
        trades, errors = parser.parse(csv_content)
        
        assert len(trades) == 2
        assert len(errors) == 0
        
        assert trades[0]["symbol"] == "AAPL"
        assert trades[0]["account_id"] == "ACCT001"
        assert trades[0]["notes"] == "Test trade"
    
    def test_unified_case_sensitive_headers(self):
        """Test that unified format requires exact header names"""
        csv_content = """Symbol,Side,Quantity,Price,executed_at
AAPL,BUY,100,150.00,2024-01-15T10:30:00-05:00"""
        
        parser = CSVParser("unified_v1")
        
        with pytest.raises(CSVParserError) as exc_info:
            parser.parse(csv_content)
        
        assert "Missing required columns" in str(exc_info.value)
    
    def test_unified_with_optional_fields(self):
        """Test unified format with optional fields omitted"""
        csv_content = """symbol,side,quantity,price,executed_at
AAPL,BUY,100,150.00,2024-01-15T10:30:00-05:00"""
        
        parser = CSVParser("unified_v1")
        trades, errors = parser.parse(csv_content)
        
        assert len(trades) == 1
        assert trades[0]["account_id"] is None
        assert trades[0]["notes"] is None


@pytest.mark.unit
class TestParserValidation:
    """Tests for common validation logic"""
    
    def test_empty_symbol(self):
        """Test error for empty symbol"""
        csv_content = """symbol,side,quantity,price,executed_at
,BUY,100,150.00,2024-01-15T10:30:00-05:00"""
        
        parser = CSVParser("unified_v1")
        trades, errors = parser.parse(csv_content)
        
        assert len(trades) == 0
        assert len(errors) == 1
        assert "symbol" in errors[0]["error"].lower()
    
    def test_price_too_high(self):
        """Test error for price exceeding maximum"""
        csv_content = """symbol,side,quantity,price,executed_at
AAPL,BUY,100,150000.00,2024-01-15T10:30:00-05:00"""
        
        parser = CSVParser("unified_v1")
        trades, errors = parser.parse(csv_content)
        
        assert len(trades) == 0
        assert len(errors) == 1
        assert "price" in errors[0]["error"].lower()
    
    def test_quantity_too_large(self):
        """Test error for quantity exceeding maximum"""
        csv_content = """symbol,side,quantity,price,executed_at
AAPL,BUY,2000000,150.00,2024-01-15T10:30:00-05:00"""
        
        parser = CSVParser("unified_v1")
        trades, errors = parser.parse(csv_content)
        
        assert len(trades) == 0
        assert len(errors) == 1
        assert "quantity" in errors[0]["error"].lower()
    
    def test_empty_csv(self):
        """Test error for empty CSV"""
        csv_content = ""
        
        parser = CSVParser("unified_v1")
        
        with pytest.raises(CSVParserError) as exc_info:
            parser.parse(csv_content)
        
        assert "empty" in str(exc_info.value).lower()
    
    def test_partial_errors(self):
        """Test that valid rows are processed even when some rows fail"""
        csv_content = """symbol,side,quantity,price,executed_at
AAPL,BUY,100,150.00,2024-01-15T10:30:00-05:00
INVALID,BUY,-50,200.00,2024-01-16T10:30:00-05:00
TSLA,SELL,25,300.00,2024-01-17T10:30:00-05:00"""
        
        parser = CSVParser("unified_v1")
        trades, errors = parser.parse(csv_content)
        
        assert len(trades) == 2  # AAPL and TSLA
        assert len(errors) == 1  # INVALID row
        assert trades[0]["symbol"] == "AAPL"
        assert trades[1]["symbol"] == "TSLA"


@pytest.mark.unit
def test_unknown_template():
    """Test error for unknown template"""
    with pytest.raises(CSVParserError) as exc_info:
        CSVParser("unknown_template")
    
    assert "Unknown template" in str(exc_info.value)
