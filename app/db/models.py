"""
Central Registry for all SQLAlchemy models.
This file prevents circular imports across the application and ensures 
Alembic detects all tables for auto-generating migrations.

Whenever you create a new module (e.g., Library, Transport), import its models here.
"""

from app.db.base import Base 

from app.auth.models import User
from app.schools.models import School, SchoolConfiguration
from app.classes.models import Class
from app.students.models import Student
from app.teachers.models import Teacher, TeacherAssignment 
from app.subjects.models import Subject, TeacherSubject 
from app.attendance.models import Attendance
from app.exams.models import Exam, Result
from app.fees.models import FeeStructure, FeePayment
from app.grades.models import GradingScale
from app.notifications.models import Notification
from app.parents.models import ParentStudentLink

__all__ = ["Base"]