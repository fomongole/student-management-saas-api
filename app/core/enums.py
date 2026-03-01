from enum import Enum

class UserRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    SCHOOL_ADMIN = "SCHOOL_ADMIN"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"
    PARENT = "PARENT"
    
class AcademicLevel(str, Enum):
    NURSERY = "NURSERY"
    PRIMARY = "PRIMARY"
    O_LEVEL = "O_LEVEL"
    A_LEVEL = "A_LEVEL"
    
class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"

class EnrollmentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    GRADUATED = "GRADUATED"
    TRANSFERRED = "TRANSFERRED"
    EXPELLED = "EXPELLED"
    DROPPED_OUT = "DROPPED_OUT"