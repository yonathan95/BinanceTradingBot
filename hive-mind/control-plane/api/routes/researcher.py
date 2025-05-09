"""
API routes for the researcher agent
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time
from datetime import datetime

# Import the researcher agent
from hive_mind.agents.researcher_agent import ResearcherAgent

router = APIRouter(
    prefix="/researcher",
    tags=["researcher"],
)

# Initialize researcher agent
researcher = ResearcherAgent()

class ResearchRequest(BaseModel):
    """
    Request model for research queries
    """
    query: str = Field(..., description="The search query to research")
    use_existing: bool = Field(True, description="Whether to use existing knowledge")
    min_reliability: float = Field(0.6, description="Minimum reliability score for sources (0.0-1.0)")
    agent_id: Optional[str] = Field(None, description="ID of the agent making the request")

class ResearchResult(BaseModel):
    """
    Response model for research results
    """
    query: str = Field(..., description="The original query")
    timestamp: str = Field(..., description="Timestamp of the research")
    sources: List[str] = Field([], description="List of sources")
    content: List[str] = Field([], description="Content from each source")
    reliability_scores: List[float] = Field([], description="Reliability scores for each source")
    summary: str = Field("", description="Summary of findings")
    processing_time: float = Field(..., description="Time taken to process the request in seconds")

@router.post("/research", response_model=ResearchResult)
async def research_topic(request: ResearchRequest):
    """
    Research a topic and return the results
    """
    start_time = time.time()
    
    try:
        # Process the research request
        message = {
            "request_type": "research",
            "query": request.query,
            "use_existing": request.use_existing,
            "min_reliability": request.min_reliability,
            "agent_id": request.agent_id
        }
        
        # Format the request for the researcher agent
        result = researcher.process_request(message)
        
        # Parse the content from the result
        content = result.get("content", "{}")
        if isinstance(content, str):
            try:
                import json
                content_data = json.loads(content)
            except:
                content_data = {"summary": "Error parsing research results"}
        else:
            content_data = content
        
        # Create the response
        processing_time = time.time() - start_time
        
        # If we have a properly structured result
        if isinstance(content_data, dict) and "sources" in content_data:
            return ResearchResult(
                query=content_data.get("query", request.query),
                timestamp=content_data.get("timestamp", datetime.now().isoformat()),
                sources=content_data.get("sources", []),
                content=content_data.get("content", []),
                reliability_scores=content_data.get("reliability_scores", []),
                summary=content_data.get("summary", ""),
                processing_time=processing_time
            )
        else:
            # If we have an error or unexpected format
            return ResearchResult(
                query=request.query,
                timestamp=datetime.now().isoformat(),
                sources=[],
                content=[],
                reliability_scores=[],
                summary="Error processing research request",
                processing_time=processing_time
            )
            
    except Exception as e:
        processing_time = time.time() - start_time
        
        # Log the error
        import logging
        logging.error(f"Error processing research request: {str(e)}")
        
        # Return an error response
        raise HTTPException(
            status_code=500,
            detail=f"Error processing research request: {str(e)}",
        )

@router.get("/status")
async def get_status():
    """
    Get the status of the researcher agent
    """
    # For now just return basic info, could expand with more detailed stats
    return {
        "status": "active",
        "knowledge_size": len(researcher.knowledge_store["texts"]),
        "embedding_model": researcher.embedding_model is not None,
        "timestamp": datetime.now().isoformat()
    } 