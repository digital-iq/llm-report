from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from app.utils import call_service

app = FastAPI()

# Internal service URLs (adjust to your OpenShift Services)
MANAGER1_URL = "http://manager1-service:8080"
MANAGER2_URL = "http://manager2-service:8080"

class UserRequest(BaseModel):
    request_text: str

class ReportResponse(BaseModel):
    report_sections: List[Dict[str, Any]]
    assembled_report: str

@app.post("/generate-report", response_model=ReportResponse)
async def generate_report(user_request: UserRequest):
    # Step 1: Call Manager #1
    manager1_payload = {"user_request": user_request.request_text}
    decomposition_result = await call_service(f"{MANAGER1_URL}/process", manager1_payload)

    subtasks = decomposition_result.get("subtasks", [])
    if not subtasks:
        return {"report_sections": [], "assembled_report": "No subtasks generated."}

    report_sections = []
    for subtask in subtasks:
        # Step 2: Call Manager #2 for each subtask
        manager2_payload = {
            "subtask": subtask
        }
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

    return {
        "report_sections": report_sections,
        "assembled_report": assembled_report
    }
