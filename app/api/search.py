from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.search import SearchQueryRequest, SearchResponse, SearchResultItem
from backend.app.services.search_service import search_web
from backend.app.models.search import WebSearch

router = APIRouter(prefix="/search", tags=["Web Search"])

@router.post("", response_model=SearchResponse)
def perform_search(request: SearchQueryRequest, db: Session = Depends(get_db)):
    """
    Direct web search endpoint. Searches the web and records search query if conversation_id is provided.
    """
    clean_query = request.query.strip()
    if not clean_query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")

    raw_results = search_web(clean_query, max_results=request.max_results)
    
    result_items = [
        SearchResultItem(
            title=item.get("title", ""),
            url=item.get("url", ""),
            snippet=item.get("snippet", "")
        )
        for item in raw_results
    ]

    # Save to web_searches if conversation_id is passed
    if request.conversation_id:
        try:
            search_record = WebSearch(
                conversation_id=request.conversation_id,
                query=clean_query,
                results=[item.model_dump() for item in result_items]
            )
            db.add(search_record)
            db.commit()
        except Exception:
            db.rollback()

    return SearchResponse(
        query=clean_query,
        results=result_items,
        total_found=len(result_items)
    )
