from typing import Dict, Any, Type
from pydantic import BaseModel, Field

class BaseTool:
    name: str
    description: str
    schema: Type[BaseModel]

    def execute(self, params: Dict[str, Any]) -> Any:
        raise NotImplementedError

# --- Existing Tools ---
class CalculateTaxSchema(BaseModel):
    income: float

class DummyTaxCalculatorTool(BaseTool):
    name = "calculate_tax"
    description = "Calculates simple tax given an income. Tax is 15%."
    schema = CalculateTaxSchema

    def execute(self, params: Dict[str, Any]) -> float:
        validated = self.schema(**params)
        return validated.income * 0.15

# --- Profitability Tools ---
class CalculateRevenueSchema(BaseModel):
    operating_revenue: float = Field(description="Operating revenue")
    other_revenue: float = Field(description="Other revenue")

class CalculateRevenueTool(BaseTool):
    name = "calculate_revenue"
    description = "Calculates total revenue from operating and other revenue."
    schema = CalculateRevenueSchema

    def execute(self, params: Dict[str, Any]) -> float:
        validated = self.schema(**params)
        return validated.operating_revenue + validated.other_revenue

class CalculateExpensesSchema(BaseModel):
    operating_expenses: float = Field(description="Operating expenses")
    other_expenses: float = Field(description="Other expenses")

class CalculateExpensesTool(BaseTool):
    name = "calculate_expenses"
    description = "Calculates total expenses from operating and other expenses."
    schema = CalculateExpensesSchema

    def execute(self, params: Dict[str, Any]) -> float:
        validated = self.schema(**params)
        return validated.operating_expenses + validated.other_expenses

class CalculateGrossProfitSchema(BaseModel):
    revenue: float = Field(description="Total revenue")
    cogs: float = Field(description="Cost of Goods Sold (COGS)")

class CalculateGrossProfitTool(BaseTool):
    name = "calculate_gross_profit"
    description = "Calculates gross profit: Revenue - Cost of Goods Sold."
    schema = CalculateGrossProfitSchema

    def execute(self, params: Dict[str, Any]) -> float:
        validated = self.schema(**params)
        return validated.revenue - validated.cogs

class CalculateNetProfitSchema(BaseModel):
    gross_profit: float = Field(description="Gross profit (Revenue - COGS)")
    operating_expenses: float = Field(description="Operating expenses")

class CalculateNetProfitTool(BaseTool):
    name = "calculate_net_profit"
    description = "Calculates net profit: Gross Profit - Operating Expenses."
    schema = CalculateNetProfitSchema

    def execute(self, params: Dict[str, Any]) -> float:
        validated = self.schema(**params)
        return validated.gross_profit - validated.operating_expenses

class CalculateNetProfitMarginSchema(BaseModel):
    net_profit: float = Field(description="Net profit")
    revenue: float = Field(description="Total revenue")

class CalculateNetProfitMarginTool(BaseTool):
    name = "calculate_net_profit_margin"
    description = "Calculates net profit margin percentage: (Net Profit / Revenue) * 100."
    schema = CalculateNetProfitMarginSchema

    def execute(self, params: Dict[str, Any]) -> float:
        validated = self.schema(**params)
        if validated.revenue <= 0:
            raise ValueError("Division by zero: revenue must be strictly positive to calculate margin.")
        return (validated.net_profit / validated.revenue) * 100.0

# --- Liquidity Tools ---
class CalculateWorkingCapitalSchema(BaseModel):
    current_assets: float = Field(description="Current assets")
    current_liabilities: float = Field(description="Current liabilities")

class CalculateWorkingCapitalTool(BaseTool):
    name = "calculate_working_capital"
    description = "Calculates working capital: Current Assets - Current Liabilities."
    schema = CalculateWorkingCapitalSchema

    def execute(self, params: Dict[str, Any]) -> float:
        validated = self.schema(**params)
        return validated.current_assets - validated.current_liabilities

class CalculateCurrentRatioSchema(BaseModel):
    current_assets: float = Field(description="Current assets")
    current_liabilities: float = Field(description="Current liabilities")

class CalculateCurrentRatioTool(BaseTool):
    name = "calculate_current_ratio"
    description = "Calculates current ratio: Current Assets / Current Liabilities."
    schema = CalculateCurrentRatioSchema

    def execute(self, params: Dict[str, Any]) -> float:
        validated = self.schema(**params)
        if validated.current_liabilities == 0:
            raise ValueError("Division by zero: current liabilities cannot be 0.")
        return validated.current_assets / validated.current_liabilities

# --- Leverage Tools ---
class CalculateDebtToEquitySchema(BaseModel):
    total_debt: float = Field(description="Total debt")
    shareholders_equity: float = Field(description="Shareholders' equity")

class CalculateDebtToEquityTool(BaseTool):
    name = "calculate_debt_to_equity"
    description = "Calculates debt-to-equity ratio: Total Debt / Shareholders' Equity."
    schema = CalculateDebtToEquitySchema

    def execute(self, params: Dict[str, Any]) -> float:
        validated = self.schema(**params)
        if validated.shareholders_equity == 0:
            raise ValueError("Division by zero: shareholders' equity cannot be 0.")
        return validated.total_debt / validated.shareholders_equity

TOOL_REGISTRY: Dict[str, BaseTool] = {
    "calculate_tax": DummyTaxCalculatorTool(),
    "calculate_revenue": CalculateRevenueTool(),
    "calculate_expenses": CalculateExpensesTool(),
    "calculate_gross_profit": CalculateGrossProfitTool(),
    "calculate_net_profit": CalculateNetProfitTool(),
    "calculate_net_profit_margin": CalculateNetProfitMarginTool(),
    "calculate_working_capital": CalculateWorkingCapitalTool(),
    "calculate_current_ratio": CalculateCurrentRatioTool(),
    "calculate_debt_to_equity": CalculateDebtToEquityTool()
}
