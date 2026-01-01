"""
Models / Schemas to ensure structured format in agents
"""

from pydantic import BaseModel, Field
from typing import List, Optional

class WayangOperation(BaseModel):
    cat: str
    id: int
    input: List[int] = Field(default_factory=list)
    output: List[int] = Field(default_factory=list)
    operatorName: str
    keyUdf: Optional[str] = None
    udf: Optional[str] = None
    thisKeyUdf: Optional[str] = None
    thatKeyUdf: Optional[str] = None
    table: Optional[str] = None
    inputFileName: Optional[str] = None
    columnNames: List[str] = Field(default_factory=list)

class WayangPlan(BaseModel):
    operations: List[WayangOperation]
    thoughts: str = Field(default=None, description="Describe your thoughts on how you ended up with this plan. Keep it short")