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

class ALevelCategory(str, Enum):
    """
    Applicable ONLY to A_LEVEL classes.
    S5 and S6 each split into Sciences or Arts streams.
    e.g. "S5 Sciences", "S5 Arts" are distinct sections of the same base class S5.
    """
    SCIENCES = "SCIENCES"
    ARTS = "ARTS"
    
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