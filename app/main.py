from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import date
from pydantic import BaseModel
from app.ai_service import process_ai_request

from app.database import get_db
from app.models import (
    EmployeeDB,
    DepartmentDB,
    UserDB,
    ProjectDB,
    LeaveRequestDB,
)
from app.schemas import (
    EmployeeResponse,
    EmployeeCreate,
    EmployeeUpdate,
    DepartmentResponse,
    UserCreate,
    UserResponse,
    TokenResponse,
    LoginRequest,
    ProjectResponse,
    LeaveRequestResponse,
    LeaveRequestCreate
)
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_role
)


app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def render_page(request: Request, page: str, title: str):
    return templates.TemplateResponse(
        request=request,
        name=f"{page}.html",
        context={
            "page": page,
            "title": title,
            "protected": page != "login",
        },
    )


# UI routes are separate from the JSON API routes below.
@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse(url="/dashboard")


@app.get("/login", include_in_schema=False)
def login_page(request: Request):
    return render_page(request, "login", "Sign in")


@app.get("/dashboard", include_in_schema=False)
def dashboard_page(request: Request):
    return render_page(request, "dashboard", "Dashboard")


@app.get("/ui/projects", include_in_schema=False)
def projects_page(request: Request):
    return render_page(request, "projects", "Projects")


@app.get("/leave", include_in_schema=False)
def leave_page(request: Request):
    return render_page(request, "leave", "Leave")


@app.get("/ui/employees", include_in_schema=False)
def employees_page(request: Request):
    return render_page(request, "employees", "Employees")


@app.get("/ai-assistant", include_in_schema=False)
def ai_assistant_page(request: Request):
    return render_page(request, "ai_assistant", "AI Assistant")

class AIChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None

@app.get("/auth/me", response_model=UserResponse)
def get_current_user_info(
    current_user: UserDB = Depends(get_current_user)
):
    return current_user

@app.get("/admin/test")
def admin_test(
    current_user: dict = Depends(require_role("admin"))
):
    return {
        "message": "Admin access granted",
        "user": current_user
    }

@app.get("/employees", response_model=list[EmployeeResponse])
def get_employees(
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    employees = db.query(EmployeeDB).all()
    return employees


@app.get("/employees/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    employee = (
        db.query(EmployeeDB)
        .filter(EmployeeDB.id == employee_id)
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    return employee

@app.post(
    "/employees",
    response_model=EmployeeResponse,
    status_code=201
)
def create_employee(
    employee: EmployeeCreate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_employee = EmployeeDB(
        name=employee.name,
        email=employee.email,
        department_id=employee.department_id,
        salary=employee.salary
    )
    try:
        db.add(new_employee)
        db.commit()
        db.refresh(new_employee)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Employee with this email already exists"
        )
    return new_employee

@app.patch(
    "/employees/{employee_id}",
    response_model=EmployeeResponse
)
def update_employee(
    employee_id: int,
    employee: EmployeeUpdate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing_employee = (
        db.query(EmployeeDB)
        .filter(EmployeeDB.id == employee_id)
        .first()
    )

    if existing_employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    updates = employee.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(existing_employee, field, value)

    try:
        db.commit()
        db.refresh(existing_employee)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Employee with this email already exists"
        )

    return existing_employee

@app.delete("/employees/{employee_id}", status_code=204)
def delete_employee(
    employee_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = (
        db.query(EmployeeDB)
        .filter(EmployeeDB.id == employee_id)
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    db.delete(employee)
    db.commit()

@app.get("/departments", response_model=list[DepartmentResponse])
def get_departments(
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    departments = db.query(DepartmentDB).all()
    return departments

@app.get(
    "/departments/{department_id}",
    response_model=DepartmentResponse
)
def get_department(
    department_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    department = (
        db.query(DepartmentDB)
        .filter(DepartmentDB.id == department_id)
        .first()
    )

    if department is None:
        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    return department

@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=201
)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    new_user = UserDB(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
        role="employee"
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists"
        )

    return new_user

@app.post("/auth/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    user = (
        db.query(UserDB)
        .filter(UserDB.username == credentials.username)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not verify_password(
        credentials.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    access_token = create_access_token(
        {
            "sub": str(user.id),
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/projects", response_model=list[ProjectResponse])
def get_projects(
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    projects = db.query(ProjectDB).all()
    return projects

@app.get(
    "/employees/{employee_id}/projects",
    response_model=list[ProjectResponse]
)
def get_employee_projects(
    employee_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    employee = (
        db.query(EmployeeDB)
        .filter(EmployeeDB.id == employee_id)
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    return employee.projects

@app.post(
    "/leave-requests",
    response_model=LeaveRequestResponse,
    status_code=201
)
def create_leave_request(
    leave: LeaveRequestCreate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.employee_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not linked to an employee"
        )

    if leave.start_date > leave.end_date:
        raise HTTPException(
            status_code=400,
            detail="Start date cannot be after end date"
        )

    employee = current_user.employee

    # Check for overlapping leave
    overlapping_leave = (
        db.query(LeaveRequestDB)
        .filter(
            LeaveRequestDB.employee_id == employee.id,
            LeaveRequestDB.start_date <= leave.end_date,
            LeaveRequestDB.end_date >= leave.start_date,
            LeaveRequestDB.status != "rejected"
        )
        .first()
    )

    if overlapping_leave:
        raise HTTPException(
            status_code=409,
            detail="Leave request overlaps with an existing leave"
        )

    new_leave = LeaveRequestDB(
        employee_id=employee.id,
        start_date=leave.start_date,
        end_date=leave.end_date,
        leave_type=leave.leave_type,
        reason=leave.reason,
        status="pending"
    )

    db.add(new_leave)
    db.commit()
    db.refresh(new_leave)

    return new_leave

@app.get(
    "/leave-requests/me",
    response_model=list[LeaveRequestResponse]
)
def get_my_leave_requests(
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.employee_id is None:
        raise HTTPException(
            status_code=400,
            detail="User is not linked to an employee"
        )

    leave_requests = (
        db.query(LeaveRequestDB)
        .filter(
            LeaveRequestDB.employee_id == current_user.employee_id
        )
        .order_by(LeaveRequestDB.start_date.desc())
        .all()
    )

    return leave_requests

@app.post("/ai/chat")
def ai_chat(
    request: AIChatRequest,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return process_ai_request(
            user_message=request.message,
            current_user=current_user,
            db=db,
            conversation_id=request.conversation_id,
        )
    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this conversation",
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid AI chat request",
        )
