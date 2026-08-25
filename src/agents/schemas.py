from pydantic import BaseModel, Field


class PlanOutput(BaseModel):
    plan: list[str] = Field(min_length=1, max_length=8)


class HypothesisOutput(BaseModel):
    hypotheses: list[str] = Field(min_length=1, max_length=4)
    selected_hypothesis: str
    evidence: list[str] = Field(default_factory=list)


class PatchOutput(BaseModel):
    unified_diff: str
    summary: str
    tests: list[str] = Field(default_factory=lambda: ["python -m pytest"])


class CriticOutput(BaseModel):
    approved: bool
    summary: str
    concerns: list[str] = Field(default_factory=list)
