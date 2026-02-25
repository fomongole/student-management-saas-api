from pydantic import BaseModel

class FinancialSummary(BaseModel):
    total_billed: float
    total_collected: float
    outstanding_balance: float

class PopulationSummary(BaseModel):
    total_students: int
    total_teachers: int
    total_parents: int

class AdminDashboardResponse(BaseModel):
    population: PopulationSummary
    financials: FinancialSummary