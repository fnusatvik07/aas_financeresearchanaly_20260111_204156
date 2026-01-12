# ui_user_f29f1967/main.py
"""
Finance Research Analyst - Auto-generated FastAPI service
Role: Financial Data Research and Analysis Specialist
"""
import asyncio
import json
import os
import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from claude_agent_sdk import query, ClaudeAgentOptions
from claude_agent_sdk.types import Message, AssistantMessage, ResultMessage, TextBlock, ToolUseBlock, ToolResultBlock
from dotenv import load_dotenv
from typing import AsyncGenerator

load_dotenv()

app = FastAPI(
    title="Finance Research Analyst",
    description="Financial Data Research and Analysis Specialist",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    prompt: str
    max_turns: int = 20

class QueryResponse(BaseModel):
    status: str
    response: str
    usage: dict = None
    agent_info: dict = None

class StreamEvent(BaseModel):
    type: str  # "progress", "tool_use", "response", "complete", "error"
    data: dict
    timestamp: str

# Agent configuration
AGENT_CONFIG = {
    "name": "Finance Research Analyst",
    "role": "Financial Data Research and Analysis Specialist",
    "tools": ['WebSearch', 'WebFetch', 'Read', 'Write', 'Bash'],
    "system_prompt": """You are a Finance Research Analyst agent with an analytical personality. Your primary objective is to gather finance-related information from the internet and deliver comprehensive results in Excel format.

Your workflow:
1. Use WebSearch to find relevant financial information based on user queries (stock prices, market data, company financials, economic indicators, etc.)
2. Use WebFetch to retrieve and analyze detailed content from financial websites and sources
3. Process and structure the collected data logically, ensuring accuracy and relevance
4. Use Bash commands (such as Python scripts or CSV tools) to create properly formatted Excel files (.xlsx or .csv)
5. Use Write to save the final Excel file with clear naming conventions

Your analytical approach:
- Be thorough and precise in data collection
- Verify information from multiple sources when possible
- Organize data in clear, professional Excel formats with appropriate headers
- Include data sources and timestamps for transparency
- Present numerical data with proper formatting (currency symbols, percentages, decimals)

Always maintain a professional, detail-oriented demeanor. If financial data is ambiguous or unavailable, clearly communicate limitations. Focus on delivering actionable, well-structured financial intelligence in an easily digestible Excel format.""",
    "permission_mode": "plan"
}

@app.get("/")
async def root():
    return {
        "message": "Welcome to Finance Research Analyst",
        "role": "Financial Data Research and Analysis Specialist",
        "agent_id": "ui_user_f29f1967",
        "endpoints": [
            "/query - POST: Send a task to the agent",
            "/stream - POST: Stream agent progress in real-time",
            "/info - GET: Get agent information",
            "/health - GET: Check service health"
        ]
    }

@app.get("/info")
async def get_agent_info():
    return {
        "agent_id": "ui_user_f29f1967",
        "name": AGENT_CONFIG["name"],
        "role": AGENT_CONFIG["role"],
        "tools": AGENT_CONFIG["tools"],
        "status": "active",
        "features": ["streaming", "real-time_progress"]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "Finance Research Analyst"}

@app.get("/files")
async def list_files():
    """
    List all generated files in the agent directory
    """
    try:
        files_dir = Path("./generated_files")
        if not files_dir.exists():
            files_dir.mkdir(exist_ok=True)
            
        files = []
        for file_path in files_dir.glob("*"):
            if file_path.is_file():
                files.append({
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": datetime.datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        return {"files": files, "count": len(files)}
    except Exception as e:
        return {"files": [], "count": 0, "error": str(e)}

@app.get("/files/{filename}")
async def download_file(filename: str):
    """
    Download a specific generated file
    """
    try:
        file_path = Path("./generated_files") / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def stream_agent_progress(request: QueryRequest) -> AsyncGenerator[str, None]:
    """
    Stream agent progress in real-time
    """
    def create_event(event_type: str, data: dict) -> str:
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.datetime.now().isoformat()
        }
        return f"data: {json.dumps(event)}\n\n"
    
    try:
        # Send initial event
        yield create_event("progress", {
            "message": "🤖 Starting Finance Research Analyst...",
            "agent": AGENT_CONFIG["name"],
            "status": "initializing"
        })
        
        # Create Claude Agent SDK options
        options = ClaudeAgentOptions(
            allowed_tools=AGENT_CONFIG["tools"],
            system_prompt=AGENT_CONFIG["system_prompt"],
            permission_mode=AGENT_CONFIG["permission_mode"],
            max_turns=request.max_turns,
        )
        
        yield create_event("progress", {
            "message": "📋 Processing your request...",
            "status": "processing"
        })
        
        # Execute the query and stream progress
        response_parts = []
        usage_info = None
        
        async for message in query(prompt=request.prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_parts.append(block.text)
                        # Stream partial response
                        yield create_event("response", {
                            "content": block.text,
                            "partial": True,
                            "message": "💭 Agent thinking..."
                        })
                    elif isinstance(block, ToolUseBlock):
                        # Stream tool usage
                        yield create_event("tool_use", {
                            "tool": block.name,
                            "input": block.input,
                            "message": f"🔧 Using {block.name} tool...",
                            "status": "executing"
                        })
            elif isinstance(message, ResultMessage):
                usage_info = {
                    "duration_ms": message.duration_ms,
                    "total_cost_usd": message.total_cost_usd,
                    "num_turns": message.num_turns,
                    "session_id": message.session_id
                }
                break
        
        full_response = "\n".join(response_parts) if response_parts else "No response received"
        
        # Send completion event
        yield create_event("complete", {
            "response": full_response,
            "usage": usage_info or {},
            "status": "completed",
            "message": "✅ Task completed successfully!",
            "agent_info": {
                "name": AGENT_CONFIG["name"],
                "role": AGENT_CONFIG["role"]
            }
        })
        
    except Exception as e:
        yield create_event("error", {
            "error": str(e),
            "message": f"❌ Error: {str(e)}",
            "status": "failed"
        })

@app.post("/stream")
async def stream_query(request: QueryRequest):
    """
    Stream agent progress in real-time using Server-Sent Events (SSE)
    """
    return StreamingResponse(
        stream_agent_progress(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """
    Send a query/task to the Finance Research Analyst (non-streaming)
    """
    try:
        # Create Claude Agent SDK options
        options = ClaudeAgentOptions(
            allowed_tools=AGENT_CONFIG["tools"],
            system_prompt=AGENT_CONFIG["system_prompt"],
            permission_mode=AGENT_CONFIG["permission_mode"],
            max_turns=request.max_turns,
        )
        
        # Execute the query
        response_parts = []
        usage_info = None
        
        async for message in query(prompt=request.prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_parts.append(block.text)
            elif isinstance(message, ResultMessage):
                usage_info = {
                    "duration_ms": message.duration_ms,
                    "total_cost_usd": message.total_cost_usd,
                    "num_turns": message.num_turns,
                    "session_id": message.session_id
                }
                break
        
        full_response = "\n".join(response_parts) if response_parts else "No response received"
        
        return QueryResponse(
            status="success",
            response=full_response,
            usage=usage_info or {},
            agent_info={
                "name": AGENT_CONFIG["name"],
                "role": AGENT_CONFIG["role"]
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
