from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, HTTPBasicCredentials

from src.models.schemas import RecommendRequest, RecommendResponse, RAResult
from src.utils.text import normalize_query
from src.service.retrieval import retrieve
from src.service.retrieval_hybrid import retrieve_hybrid
from src.service.augment import augment_results
from src.service.retrieval_multiquery import retrieve_multiquery
from src.service.retrieval_combined import retrieve_combined
from src.service.retrieval_parent import retrieve_parent
from fastapi.responses import JSONResponse


router = APIRouter(prefix="/recommend", tags=["recommend"])
security = HTTPBearer(auto_error=False)

@router.options("")
async def recommend_options():
    return JSONResponse(content={}, status_code=200)

@router.post("", response_model=RecommendResponse)
def recommend(
    payload: RecommendRequest,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    if not payload.query:
        raise HTTPException(400, "query is required")

    q = normalize_query(payload.query)
    k = min(payload.max_results * 5, 25)

    if payload.model == "hybrid":
        raw = retrieve_hybrid(q, k)
    elif payload.model == "multi_query":
        raw = retrieve_multiquery(q, k)
    elif payload.model == "combined":
        raw = retrieve_combined(q, k)
    elif payload.model == "parent":
        raw = retrieve_parent(q, k)
    else:
        raw = retrieve(q, k)

    augmented = augment_results(
        chroma_res=raw,
        max_results=payload.max_results,
        max_runtime=payload.max_runtime,
        auth=auth.credentials if auth else None
    )

    api_results = [
        RAResult(
            title=i["title"],
            year=i["year"],
            genres=i["genres"],
            directors=i["directors"],
            runtime=i["runtime"],
            score=round(i["score"], 4),
            signals={
                "sim_avg": round(i["sim_avg"], 4),
                "tomatometer": i["tomatometer"],
                "count": i["tomatometer_count"]
            },
            snippets=i["snippets"],
            streaming_availability=i["streaming_availability"],
            link=i["link"],
            posterUrl=i["posterUrl"]
        )
        for i in augmented
    ]

    return RecommendResponse(query=q, results=api_results)