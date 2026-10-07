from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Date, Table, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Table
from datetime import date

Base = declarative_base()


class DepartmentDB(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)

    employees = relationship("EmployeeDB", back_populates="department")


class EmployeeDB(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    salary = Column(Numeric(10, 2), nullable=False)

    department = relationship("DepartmentDB", back_populates="employees")
    user = relationship(
        "UserDB",
        back_populates="employee",
        uselist=False
    )
    #Many2many with Projects
    projects = relationship(
        "ProjectDB",
        secondary="employee_projects",
        back_populates="employees"
    )
    leave_requests = relationship(
        "LeaveRequestDB",
        back_populates="employee"
    )
class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="employee")
    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        unique=True,
        nullable=True
    )

    employee = relationship(
        "EmployeeDB",
        back_populates="user"
    )

    ai_conversations = relationship(
        "AIConversationDB",
        back_populates="user",
        cascade="all, delete-orphan",
    )

employee_projects = Table(
    "employee_projects",
    Base.metadata,
    Column(
        "employee_id",
        ForeignKey("employees.id"),
        primary_key=True
    ),
    Column(
        "project_id",
        ForeignKey("projects.id"),
        primary_key=True
    )
)

class ProjectDB(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    description = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False, default="active")

    employees = relationship(
        "EmployeeDB",
        secondary="employee_projects",
        back_populates="projects"
    )

class LeaveRequestDB(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True)

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False
    )

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    leave_type = Column(String(50),nullable=False,default="annual")
    reason = Column(String(500), nullable=True)
    status = Column(String(50),nullable=False,default="pending")
    employee = relationship("EmployeeDB",back_populates="leave_requests")

class AIConversationDB(Base):
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=True)

    user = relationship("UserDB", back_populates="ai_conversations")
    messages = relationship(
        "AIMessageDB",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class AIMessageDB(Base):
    __tablename__ = "ai_messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(
        Integer,
        ForeignKey("ai_conversations.id"),
        nullable=False,
    )
    role = Column(String(50), nullable=False)
    content = Column(String, nullable=False)

    tool_calls_data = Column(JSON, nullable=True)

    conversation = relationship(
        "AIConversationDB",
        back_populates="messages",
    )

    tool_calls = relationship(
        "AIToolCallDB",
        back_populates="message",
        cascade="all, delete-orphan",
    )

class AIToolCallDB(Base):
    __tablename__ = "ai_tool_calls"

    id = Column(Integer, primary_key=True)

    message_id = Column(
        Integer,
        ForeignKey("ai_messages.id"),
        nullable=False,
    )

    tool_name = Column(String(100), nullable=False)

    arguments = Column(JSON, nullable=True)

    result = Column(JSON, nullable=True)

    status = Column(String(50), nullable=False, default="success")

    message = relationship(
        "AIMessageDB",
        back_populates="tool_calls",
    )

# Conversation #1
#     │
#     ├── User message
#     │
#     ├── Assistant message
#     │       │
#     │       └── get_my_projects
#     │
#     ├── User message
#     │
#     └── Assistant message
#             │
#             └── get_my_leave_requests