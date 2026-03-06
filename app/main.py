from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    integrity_error_handler,
    global_exception_handler,
)

from app.auth.router import router as auth_router
from app.schools.router import router as schools_router
from app.classes.router import router as classes_router
from app.students.router import router as students_router
from app.teachers.router import router as teachers_router
from app.subjects.router import router as subjects_router
from app.attendance.router import router as attendance_router
from app.exams.router import router as exams_router
from app.grades.router import router as grades_router
from app.fees.router import router as fees_router
from app.notifications.router import router as notifications_router
from app.parents.router import router as parents_router
from app.reports.router import router as reports_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(Exception, global_exception_handler)


# Routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(schools_router, prefix=f"{settings.API_V1_STR}/schools", tags=["Schools"])
app.include_router(classes_router, prefix=f"{settings.API_V1_STR}/classes", tags=["Classes"])
app.include_router(students_router, prefix=f"{settings.API_V1_STR}/students", tags=["Students"])
app.include_router(teachers_router, prefix=f"{settings.API_V1_STR}/teachers", tags=["Teachers"])
app.include_router(subjects_router, prefix=f"{settings.API_V1_STR}/subjects", tags=["Subjects"])
app.include_router(attendance_router, prefix=f"{settings.API_V1_STR}/attendance", tags=["Attendance"])
app.include_router(exams_router, prefix=f"{settings.API_V1_STR}/exams", tags=["Exams"])
app.include_router(grades_router, prefix=f"{settings.API_V1_STR}/grades", tags=["Grades"])
app.include_router(fees_router, prefix=f"{settings.API_V1_STR}/fees", tags=["Fees"])
app.include_router(notifications_router, prefix=f"{settings.API_V1_STR}/notifications", tags=["Notifications"])
app.include_router(parents_router, prefix=f"{settings.API_V1_STR}/parents", tags=["Parents"])
app.include_router(reports_router, prefix=f"{settings.API_V1_STR}/reports", tags=["Reports"])

# Health check
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "message": "Student Management SaaS API is running smoothly.",
    }