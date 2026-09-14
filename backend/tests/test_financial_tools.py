import pytest
from pydantic import ValidationError
from app.services.agent.tools import (
    CalculateRevenueTool, CalculateExpensesTool, CalculateGrossProfitTool,
    CalculateNetProfitTool, CalculateNetProfitMarginTool, CalculateWorkingCapitalTool,
    CalculateCurrentRatioTool, CalculateDebtToEquityTool, TOOL_REGISTRY
)

def test_registry_contains_tools():
    assert "calculate_revenue" in TOOL_REGISTRY
    assert "calculate_expenses" in TOOL_REGISTRY
    assert "calculate_gross_profit" in TOOL_REGISTRY
    assert "calculate_net_profit" in TOOL_REGISTRY
    assert "calculate_net_profit_margin" in TOOL_REGISTRY
    assert "calculate_working_capital" in TOOL_REGISTRY
    assert "calculate_current_ratio" in TOOL_REGISTRY
    assert "calculate_debt_to_equity" in TOOL_REGISTRY

# --- Revenue ---
def test_calculate_revenue_normal():
    tool = CalculateRevenueTool()
    res = tool.execute({"operating_revenue": 1000, "other_revenue": 200})
    assert res == 1200.0

def test_calculate_revenue_missing_params():
    tool = CalculateRevenueTool()
    with pytest.raises(ValidationError):
        tool.execute({"operating_revenue": 1500})
    with pytest.raises(ValidationError):
        tool.execute({})

# --- Expenses ---
def test_calculate_expenses_normal():
    tool = CalculateExpensesTool()
    res = tool.execute({"operating_expenses": 500, "other_expenses": 100})
    assert res == 600.0

def test_calculate_expenses_missing_params():
    tool = CalculateExpensesTool()
    with pytest.raises(ValidationError):
        tool.execute({"operating_expenses": 500})
    with pytest.raises(ValidationError):
        tool.execute({})

# --- Gross Profit ---
def test_calculate_gross_profit():
    tool = CalculateGrossProfitTool()
    res = tool.execute({"revenue": 1000, "cogs": 400})
    assert res == 600.0

def test_calculate_gross_profit_negative():
    tool = CalculateGrossProfitTool()
    res = tool.execute({"revenue": 500, "cogs": 800})
    assert res == -300.0

def test_calculate_gross_profit_missing_param():
    tool = CalculateGrossProfitTool()
    with pytest.raises(ValidationError):
        tool.execute({"revenue": 1000})

# --- Net Profit ---
def test_calculate_net_profit():
    tool = CalculateNetProfitTool()
    res = tool.execute({"gross_profit": 2000, "operating_expenses": 1500})
    assert res == 500.0
# --- Net Profit Margin ---
def test_calculate_net_profit_margin():
    tool = CalculateNetProfitMarginTool()
    res = tool.execute({"net_profit": 300000, "revenue": 1800000})
    assert abs(res - 16.666666666666664) < 1e-9

def test_calculate_net_profit_margin_zero_revenue():
    tool = CalculateNetProfitMarginTool()
    with pytest.raises(ValueError, match="Division by zero"):
        tool.execute({"net_profit": 500, "revenue": 0})

def test_calculate_net_profit_margin_invalid_type():
    tool = CalculateNetProfitMarginTool()
    with pytest.raises(ValidationError):
        tool.execute({"net_profit": "some text", "revenue": 1000})

# --- Working Capital ---
def test_calculate_working_capital():
    tool = CalculateWorkingCapitalTool()
    res = tool.execute({"current_assets": 10000, "current_liabilities": 4000})
    assert res == 6000.0

def test_calculate_working_capital_negative():
    tool = CalculateWorkingCapitalTool()
    res = tool.execute({"current_assets": 2000, "current_liabilities": 5000})
    assert res == -3000.0

# --- Current Ratio ---
def test_calculate_current_ratio():
    tool = CalculateCurrentRatioTool()
    res = tool.execute({"current_assets": 10000, "current_liabilities": 4000})
    assert res == 2.5

def test_calculate_current_ratio_zero_liabilities():
    tool = CalculateCurrentRatioTool()
    with pytest.raises(ValueError, match="Division by zero"):
        tool.execute({"current_assets": 5000, "current_liabilities": 0})

# --- Debt to Equity ---
def test_calculate_debt_to_equity():
    tool = CalculateDebtToEquityTool()
    res = tool.execute({"total_debt": 50000, "shareholders_equity": 100000})
    assert res == 0.5

def test_calculate_debt_to_equity_zero_equity():
    tool = CalculateDebtToEquityTool()
    with pytest.raises(ValueError, match="Division by zero"):
        tool.execute({"total_debt": 50000, "shareholders_equity": 0})

