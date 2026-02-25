from enum import Enum

class UserRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"     # Manages the SaaS, creates schools
    SCHOOL_ADMIN = "SCHOOL_ADMIN"   # Manages a specific school
    TEACHER = "TEACHER"             # Manages classes, grades, attendance
    STUDENT = "STUDENT"             # Views their own data
    PARENT = "PARENT"               # Views their children's data
    
class AcademicLevel(str, Enum):
    NURSERY = "NURSERY"     # Baby, Middle, Top
    PRIMARY = "PRIMARY"     # P1 to P7
    O_LEVEL = "O_LEVEL"     # S1 to S4 (Broad subjects)
    A_LEVEL = "A_LEVEL"     # S5 to S6 (Combinations)
    
class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"