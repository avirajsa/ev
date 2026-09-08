from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.agent.orchestrator import agent_orchestrator
from app.core.security import get_current_user_or_device

router = APIRouter(prefix="/agent", tags=["Agent"])

class QueryRequest(BaseModel):
    message: str = Field(..., description="User message or transcribed voice input")
    chat_history: Optional[List[Dict[str, Any]]] = Field(default=None, description="Previous messages")
    preferred_model: Optional[str] = Field(default=None, description="Optional LLM model override")

class QueryResponse(BaseModel):
    response: str
    model_used: Optional[str]
    chat_history: List[Dict[str, Any]]

@router.post("/query", response_model=QueryResponse)
async def process_agent_query(
    request: QueryRequest,
    current_client: dict = Depends(get_current_user_or_device)
):
    """
    Submits a command or question to EV Agent.
    Triggers reasoning, remote tool execution across connected devices, and returns the response.
    """
    try:
        result = await agent_orchestrator.process_user_request(
            user_message=request.message,
            chat_history=request.chat_history,
            model_override=request.preferred_model
        )
        return QueryResponse(
            response=result["response"],
            model_used=result.get("model_used"),
            chat_history=result["chat_history"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent processing error: {str(e)}"
        )
