import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# try:
#     employees = db.query(EmployeeDB).all()
#
#     for employee in employees:
#         print(
#             employee.id,
#             employee.name,
#             employee.email,
#             employee.department_id,
#             employee.salary
#         )
# finally:
#     db.close()
