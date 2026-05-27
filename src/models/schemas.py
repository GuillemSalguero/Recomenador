from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Literal

class RecommendRequest(BaseModel):
    query: str = Field(..., min_length=3)
    max_results: int = 5
    max_runtime: Optional[int] = None
    model: Literal["self_query", "hybrid",  "multi_query", "combined", "parent"] = "self_query"

class StreamingAvailability(BaseModel):
    nombre: str
    tipo: Optional[str]
    link: Optional[str]


class RAResult(BaseModel):
    title: Optional[str]
    year: Optional[str]
    genres: Optional[str]
    directors: List[str]
    runtime: Optional[int]
    score: float
    signals: dict
    snippets: List[str]
    streaming_availability: List[StreamingAvailability] = []
    link: str
    posterUrl: Optional[str] = None

class RecommendResponse(BaseModel):
    query: str
    results: List[RAResult]