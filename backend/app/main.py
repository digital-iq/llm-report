from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from app.utils import call_service

# ----------------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------------

# For production, specify only your actual frontend route here
ALLOWED_ORIGINS = [
    "*"
]

MANAGER1_URL = os.getenv("MANAGER1_URL", "http://manager1-service.llm-report.svc.cluster.local:8080")
MANAGER2_URL = os.getenv("MANAGER2_URL", "http://manager2-service.llm-report.svc.cluster.local:8080")

# ----------------------------------------------------------------------------
# FastAPI App Setup
# ----------------------------------------------------------------------------

app = FastAPI(title="LLM Orchestrator", version="1.0")

# ----------------------------------------------------------------------------
# Health Check
# ----------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------------------------
# Pydantic Models
# ----------------------------------------------------------------------------

class UserRequest(BaseModel):
    request_text: str

class ReportResponse(BaseModel):
    report_sections: List[Dict[str, Any]]
    assembled_report: str

# ----------------------------------------------------------------------------
# Router with /api prefix
# ----------------------------------------------------------------------------

router = APIRouter(prefix="/api")

@router.post("/generate-report", response_model=ReportResponse)
async def generate_report(user_request: UserRequest):
    """
    Orchestrates generation of a full PDF report by:
    1. Asking Manager #1 to decompose the request
    2. Asking Manager #2 to complete each subtask
    3. Assembling the results
    """
    # Step 1: Decompose via Manager #1
    manager1_payload = {"user_request": user_request.request_text}
    decomposition_result = await call_service(f"{MANAGER1_URL}/process", manager1_payload)

    subtasks = decomposition_result.get("subtasks", [])
    if not subtasks:
        return {
            "report_sections": [],
            "assembled_report": "No subtasks were generated."
        }

    # Step 2: For each subtask, call Manager #2
    report_sections = []
    for subtask in subtasks:
        manager2_payload = {"subtask": subtask}
        subtask_result = await call_service(f"{MANAGER2_URL}/process", manager2_payload)
        report_sections.append({
            "subtask_title": subtask.get("subtask_title"),
            "result": subtask_result
        })

    # Step 3: Assemble Report
    assembled_report = "\n\n".join(
        f"## {section['subtask_title']}\n\n{section['result'].get('final_output', '')}"
        for section in report_sections
    )

    return ReportResponse(
        report_sections=report_sections,
        assembled_report=assembled_report
    )

# ----------------------------------------------------------------------------
# Register router with /api prefix
# ----------------------------------------------------------------------------

app.include_router(router)

