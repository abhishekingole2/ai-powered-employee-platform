from pydantic import BaseModel, Field
from datetime import date


class DepartmentResponse(BaseModel):
    id: int
    name: str

    model_config = {
        "from_attributes": True
    }


class EmployeeResponse(BaseModel):
    id: int
    name: str
    email: str
    salary: float
    department: DepartmentResponse

    model_config = {
        "from_attributes": True
    }

class EmployeeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str
    department_id: int
    salary: float = Field(gt=0)

class EmployeeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    email: str | None = None
    department_id: int | None = None
    salary: float | None = Field(default=None, gt=0)

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: str
    password: str = Field(min_length=8, max_length=128)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    employee_id: int | None = None

    model_config = {
        "from_attributes": True
    }

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None
    status: str

    model_config = {
        "from_attributes": True
    }

class LeaveRequestCreate(BaseModel):
    start_date: date
    end_date: date
    leave_type: str = "annual"
    reason: str | None = None

class LeaveRequestResponse(BaseModel):
    id: int
    employee_id: int
    start_date: date
    end_date: date
    leave_type: str
    reason: str | None
    status: str

    model_config = {
        "from_attributes": True
    }

class AIConversationResponse(BaseModel):
    id: int
    title: str | None

    model_config = {"from_attributes": True}


class AIMessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str

    model_config = {"from_attributes": True}
