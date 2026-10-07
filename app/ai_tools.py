from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.models import UserDB,LeaveRequestDB, EmployeeDB

class GetMyProjectsArgs(BaseModel):
    model_config = {"extra": "forbid"}


class GetMyLeaveRequestsArgs(BaseModel):
    leave_type: str | None = Field(
        default=None,
        max_length=50,
    )

    model_config = {"extra": "forbid"}


class SearchEmployeesArgs(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=100,
    )

    model_config = {"extra": "forbid"}

def get_my_projects(current_user: UserDB, db: Session) -> list[dict]:
    """
    Return the projects assigned to the authenticated employee.
    """

    if current_user.employee_id is None:
        raise ValueError("User is not linked to an employee")

    employee = current_user.employee

    if employee is None:
        raise ValueError("Employee record not found")

    return [
        {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
        }
        for project in employee.projects
    ]

def get_my_leave_requests(
    current_user: UserDB,
    db: Session,
    leave_type: str | None = None,
) -> list[dict]:
    """
    Return leave requests belonging to the authenticated employee.
    Optionally filter by leave type.
    """

    if current_user.employee_id is None:
        raise ValueError("User is not linked to an employee")

    query = (
        db.query(LeaveRequestDB)
        .filter(
            LeaveRequestDB.employee_id == current_user.employee_id
        )
    )

    if leave_type:
        query = query.filter(
            LeaveRequestDB.leave_type == leave_type
        )

    leave_requests = query.order_by(
        LeaveRequestDB.start_date.desc()
    ).all()

    return [
        {
            "id": leave.id,
            "start_date": leave.start_date.isoformat(),
            "end_date": leave.end_date.isoformat(),
            "leave_type": leave.leave_type,
            "reason": leave.reason,
            "status": leave.status,
        }
        for leave in leave_requests
    ]

def search_employees(
    current_user: UserDB,
    db: Session,
    query: str,
) -> list[dict]:
    """
    Search employees by name or email.
    """

    query = query.strip()

    if not query:
        raise ValueError("Search query cannot be empty")

    if len(query) > 100:
        raise ValueError("Search query is too long")

    employees = (
        db.query(EmployeeDB)
        .filter(
            (EmployeeDB.name.ilike(f"%{query}%"))
            | (EmployeeDB.email.ilike(f"%{query}%"))
        )
        .order_by(EmployeeDB.name)
        .limit(20)
        .all()
    )

    return [
        {
            "id": employee.id,
            "name": employee.name,
            "email": employee.email,
        }
        for employee in employees
    ]

TOOL_REGISTRY = {
    "get_my_projects": {
        "function": get_my_projects,
        "description": (
            "Get the projects assigned to the authenticated employee."
        ),
        "allowed_roles": ["employee", "admin"],
        "args_model": GetMyProjectsArgs,
    },

    "get_my_leave_requests": {
        "function": get_my_leave_requests,
        "description": (
            "Get leave requests belonging to the authenticated employee. "
            "Optionally filter by leave type."
        ),
        "allowed_roles": ["employee", "admin"],
        "args_model": GetMyLeaveRequestsArgs,
    },

    "search_employees": {
        "function": search_employees,
        "description": (
            "Search company employees by name or email address."
        ),
        "allowed_roles": ["employee", "admin"],
        "args_model": SearchEmployeesArgs,
    },
}

def build_tool_definitions() -> list[dict]:
    """
    Build LLM-compatible tool definitions from the
    registered tools and their Pydantic argument models.
    """

    definitions = []

    for tool_name, tool_config in TOOL_REGISTRY.items():
        args_model = tool_config["args_model"]

        definitions.append(
            {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool_config["description"],
                    "parameters": args_model.model_json_schema(),
                },
            }
        )

    return definitions


TOOL_DEFINITIONS = build_tool_definitions()

if __name__ == "__main__":
    for tool in TOOL_DEFINITIONS:
        print(tool)
        print()
