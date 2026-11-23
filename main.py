
import csv
import os
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Security
from fastapi.security import APIKeyHeader

app = FastAPI(
    title="Employee Directory API",
    description="Custom REST API powered by a CSV file hosted with GitHub and Render.",
    version="1.0.0"
)

CSV_PATH = Path(__file__).parent / "employee_directory.csv"
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(key: str = Security(api_key_header)):
    expected = os.environ.get("API_KEY")
    if not expected:
        raise HTTPException(status_code=503, detail="API key not configured")
    if not key or not secrets.compare_digest(key, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")


def load_employees():
    if not CSV_PATH.is_file():
        raise HTTPException(status_code=503, detail="Employee CSV not found")

    with CSV_PATH.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


@app.get("/health")
def health():
    return {"status": "healthy", "service": "Employee Directory API"}


@app.get("/api/v1/employees", dependencies=[Security(verify_api_key)])
def get_employees(
    page: int = Query(1, ge=1),
    pageSize: int = Query(100, ge=1, le=1000)
):
    employees = load_employees()
    total = len(employees)
    start = (page - 1) * pageSize

    return {
        "success": True,
        "totalRecords": total,
        "page": page,
        "pageSize": pageSize,
        "data": employees[start:start + pageSize]
    }


@app.get("/api/v1/employees/count", dependencies=[Security(verify_api_key)])
def employee_count():
    return {
        "success": True,
        "totalRecords": len(load_employees())
    }


@app.get("/api/v1/employees/{employee_id}", dependencies=[Security(verify_api_key)])
def get_employee(employee_id: str):
    for employee in load_employees():
        if employee.get("EmployeeID") == employee_id:
            return {"success": True, "data": employee}

    raise HTTPException(status_code=404, detail="Employee not found")
