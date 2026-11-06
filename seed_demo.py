"""
Seed script: creates a complete, realistic demo tenant for the Elimu SaaS demo.

Run inside the API container:
    docker compose exec api python seed_demo.py

All demo accounts use the password:  Elimu@2026
"""

import asyncio
import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

# Register every model before touching the mapper registry
import app.db.models  # noqa: F401

from app.db.session import AsyncSessionLocal
from app.auth.models import User
from app.schools.models import School, SchoolLevel, SchoolConfiguration
from app.classes.models import Class
from app.subjects.models import Subject, TeacherSubject
from app.teachers.models import Teacher, TeacherAssignment
from app.students.models import Student
from app.parents.models import ParentStudentLink
from app.fees.models import FeeStructure, FeePayment
from app.exams.models import Exam, Result
from app.attendance.models import Attendance
from app.grades.models import GradingScale
from app.notifications.models import Notification, NotificationType, NotificationStatus
from app.core.enums import (
    UserRole,
    AcademicLevel,
    ALevelCategory,
    AttendanceStatus,
    EnrollmentStatus,
)
from app.core.security import get_password_hash

PASSWORD = "Elimu@2026"
SCHOOL_EMAIL = "info@stkizito.ac.ug"
YEAR = 2026
TERM = 1

random.seed(42)


def hash_pw() -> str:
    return get_password_hash(PASSWORD)


async def create_user(db, email, first, last, role, school_id=None):
    user = User(
        email=email,
        hashed_password=hash_pw(),
        first_name=first,
        last_name=last,
        role=role,
        school_id=school_id,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


async def main():
    async with AsyncSessionLocal() as db:
        existing = await db.scalar(select(School).where(School.email == SCHOOL_EMAIL))
        if existing:
            print("⚠️  Demo school already exists — nothing to do.")
            print(f"    School id: {existing.id}")
            return

        # ---------------------------------------------------------------
        # 1. SUPER ADMIN (platform owner)
        # ---------------------------------------------------------------
        super_admin = await create_user(
            db, "admin@elimu.ug", "Fred", "Omongole", UserRole.SUPER_ADMIN
        )

        # ---------------------------------------------------------------
        # 2. SCHOOL
        # ---------------------------------------------------------------
        school = School(
            name="St. Kizito Secondary School",
            email=SCHOOL_EMAIL,
            phone="+256 772 123 456",
            address="Plot 14, Bukoto Street, Kampala, Uganda",
            is_active=True,
        )
        db.add(school)
        await db.flush()

        for level in (AcademicLevel.PRIMARY, AcademicLevel.O_LEVEL, AcademicLevel.A_LEVEL):
            db.add(SchoolLevel(school_id=school.id, level=level))

        db.add(
            SchoolConfiguration(
                school_id=school.id,
                current_academic_year=YEAR,
                current_term=TERM,
                currency_symbol="UGX",
            )
        )

        # ---------------------------------------------------------------
        # 3. GRADING SCALE (UNEB O-Level)
        # ---------------------------------------------------------------
        uneb = [
            ("D1", 90, 100, "Distinction", 1),
            ("D2", 80, 89.99, "Distinction", 2),
            ("C3", 70, 79.99, "Credit", 3),
            ("C4", 60, 69.99, "Credit", 4),
            ("P5", 55, 59.99, "Pass", 5),
            ("P6", 50, 54.99, "Pass", 6),
            ("P7", 45, 49.99, "Pass", 7),
            ("P8", 40, 44.99, "Pass", 8),
            ("F9", 0, 39.99, "Fail", 9),
        ]
        for symbol, lo, hi, label, points in uneb:
            db.add(
                GradingScale(
                    school_id=school.id,
                    grade_symbol=symbol,
                    min_score=lo,
                    max_score=hi,
                    label=label,
                    points=points,
                )
            )

        # ---------------------------------------------------------------
        # 4. STAFF USERS
        # ---------------------------------------------------------------
        headteacher = await create_user(
            db, "headteacher@elimu.ug", "Grace", "Nakato", UserRole.SCHOOL_ADMIN, school.id
        )
        t1 = await create_user(db, "teacher@elimu.ug", "Daniel", "Mukasa", UserRole.TEACHER, school.id)
        t2 = await create_user(db, "teacher2@elimu.ug", "Sarah", "Auma", UserRole.TEACHER, school.id)
        t3 = await create_user(db, "teacher3@elimu.ug", "Peter", "Okello", UserRole.TEACHER, school.id)
        t4 = await create_user(db, "teacher4@elimu.ug", "Immaculate", "Nabirye", UserRole.TEACHER, school.id)

        teacher_rows = [
            Teacher(user_id=t1.id, school_id=school.id, employee_number="TCH-001",
                    qualification="BSc Education (Mathematics)", specialization="Mathematics"),
            Teacher(user_id=t2.id, school_id=school.id, employee_number="TCH-002",
                    qualification="BA Education (Languages)", specialization="English & Literature"),
            Teacher(user_id=t3.id, school_id=school.id, employee_number="TCH-003",
                    qualification="BSc Education (Sciences)", specialization="Physics"),
            Teacher(user_id=t4.id, school_id=school.id, employee_number="TCH-004",
                    qualification="BSc Education (Sciences)", specialization="Biology & Chemistry"),
        ]
        db.add_all(teacher_rows)
        await db.flush()
        daniel, sarah, peter, immaculate = teacher_rows

        # ---------------------------------------------------------------
        # 5. CLASSES
        # ---------------------------------------------------------------
        classes = [
            Class(school_id=school.id, name="P7", stream=None, level=AcademicLevel.PRIMARY, capacity=45,
                  form_teacher_id=immaculate.id),
            Class(school_id=school.id, name="S1", stream="East", level=AcademicLevel.O_LEVEL, capacity=50,
                  form_teacher_id=daniel.id),
            Class(school_id=school.id, name="S1", stream="West", level=AcademicLevel.O_LEVEL, capacity=50,
                  form_teacher_id=sarah.id),
            Class(school_id=school.id, name="S2", stream="East", level=AcademicLevel.O_LEVEL, capacity=50,
                  form_teacher_id=peter.id),
            Class(school_id=school.id, name="S5", stream=None, level=AcademicLevel.A_LEVEL, capacity=40,
                  category=ALevelCategory.SCIENCES, form_teacher_id=peter.id),
            Class(school_id=school.id, name="S5", stream=None, level=AcademicLevel.A_LEVEL, capacity=40,
                  category=ALevelCategory.ARTS, form_teacher_id=sarah.id),
        ]
        db.add_all(classes)
        await db.flush()
        p7, s1e, s1w, s2e, s5sci, s5arts = classes

        # ---------------------------------------------------------------
        # 6. SUBJECTS
        # ---------------------------------------------------------------
        subject_defs = [
            # (name, code, level, core)
            ("Mathematics", "MTH-P", AcademicLevel.PRIMARY, True),
            ("English", "ENG-P", AcademicLevel.PRIMARY, True),
            ("Science", "SCI-P", AcademicLevel.PRIMARY, True),
            ("Social Studies", "SST-P", AcademicLevel.PRIMARY, True),
            ("Mathematics", "MTH-O", AcademicLevel.O_LEVEL, True),
            ("English", "ENG-O", AcademicLevel.O_LEVEL, True),
            ("Physics", "PHY-O", AcademicLevel.O_LEVEL, True),
            ("Chemistry", "CHE-O", AcademicLevel.O_LEVEL, True),
            ("Biology", "BIO-O", AcademicLevel.O_LEVEL, True),
            ("History", "HIS-O", AcademicLevel.O_LEVEL, False),
            ("Geography", "GEO-O", AcademicLevel.O_LEVEL, False),
            ("Mathematics", "MTH-A", AcademicLevel.A_LEVEL, True),
            ("Physics", "PHY-A", AcademicLevel.A_LEVEL, True),
            ("Chemistry", "CHE-A", AcademicLevel.A_LEVEL, True),
            ("Biology", "BIO-A", AcademicLevel.A_LEVEL, True),
        ]
        subjects = []
        for name, code, level, core in subject_defs:
            s = Subject(school_id=school.id, name=name, code=code, level=level, is_core=core)
            subjects.append(s)
        db.add_all(subjects)
        await db.flush()

        by_code = {s.code: s for s in subjects}
        mth_o, eng_o, phy_o, che_o, bio_o = (
            by_code["MTH-O"], by_code["ENG-O"], by_code["PHY-O"], by_code["CHE-O"], by_code["BIO-O"],
        )
        mth_a, phy_a, che_a, bio_a = (
            by_code["MTH-A"], by_code["PHY-A"], by_code["CHE-A"], by_code["BIO-A"],
        )
        mth_p, eng_p, sci_p, sst_p = (
            by_code["MTH-P"], by_code["ENG-P"], by_code["SCI-P"], by_code["SST-P"],
        )

        # Teacher -> subject qualifications
        for subj in (mth_o, mth_a, mth_p):
            db.add(TeacherSubject(school_id=school.id, teacher_id=daniel.id, subject_id=subj.id))
        for subj in (eng_o, eng_p, by_code["HIS-O"]):
            db.add(TeacherSubject(school_id=school.id, teacher_id=sarah.id, subject_id=subj.id))
        for subj in (phy_o, phy_a, sci_p):
            db.add(TeacherSubject(school_id=school.id, teacher_id=peter.id, subject_id=subj.id))
        for subj in (bio_o, bio_a, che_o, che_a, sst_p):
            db.add(TeacherSubject(school_id=school.id, teacher_id=immaculate.id, subject_id=subj.id))

        # Teacher -> subject -> class assignments
        assignments = [
            (daniel, mth_o, s1e), (daniel, mth_o, s1w), (daniel, mth_o, s2e), (daniel, mth_a, s5sci),
            (sarah, eng_o, s1e), (sarah, eng_o, s1w), (sarah, eng_o, s2e), (sarah, eng_p, p7),
            (peter, phy_o, s1e), (peter, phy_o, s1w), (peter, phy_a, s5sci), (peter, sci_p, p7),
            (immaculate, bio_o, s1e), (immaculate, bio_o, s2e), (immaculate, che_a, s5sci),
            (immaculate, sst_p, p7),
        ]
        for teacher, subj, cls in assignments:
            db.add(TeacherAssignment(
                school_id=school.id, teacher_id=teacher.id, subject_id=subj.id, class_id=cls.id
            ))

        # ---------------------------------------------------------------
        # 7. STUDENTS (and their user accounts)
        # ---------------------------------------------------------------
        student_seed = [
            # first, last, admission_no, class, gender_hint
            ("Brian", "Ssemakula", "STK/2026/001", s1e, date(2012, 3, 14)),
            ("Mercy", "Achieng", "STK/2026/002", s1e, date(2012, 7, 2)),
            ("Joshua", "Kato", "STK/2026/003", s1e, date(2011, 11, 21)),
            ("Patience", "Namu", "STK/2026/004", s1e, date(2012, 1, 9)),
            ("Samuel", "Okumu", "STK/2026/005", s1e, date(2012, 5, 30)),
            ("Esther", "Nakimuli", "STK/2026/006", s1w, date(2012, 2, 18)),
            ("Ivan", "Tumusiime", "STK/2026/007", s1w, date(2011, 12, 4)),
            ("Diana", "Kyomuhendo", "STK/2026/008", s1w, date(2012, 8, 27)),
            ("Ronald", "Byaruhanga", "STK/2026/009", s1w, date(2012, 4, 11)),
            ("Faith", "Nabukenya", "STK/2026/010", s2e, date(2011, 6, 15)),
            ("Alex", "Opio", "STK/2026/011", s2e, date(2011, 9, 3)),
            ("Sylvia", "Namutebi", "STK/2026/012", s2e, date(2011, 10, 25)),
            ("Emmanuel", "Wasswa", "STK/2026/013", s2e, date(2011, 2, 7)),
            ("Brenda", "Atim", "STK/2026/014", s2e, date(2011, 12, 19)),
            ("Derrick", "Ssekandi", "STK/2026/015", s5sci, date(2009, 5, 8)),
            ("Joan", "Kirabo", "STK/2026/016", s5sci, date(2009, 3, 22)),
            ("Michael", "Anguyo", "STK/2026/017", s5sci, date(2009, 7, 16)),
            ("Prossy", "Nansubuga", "STK/2026/018", s5sci, date(2009, 1, 30)),
            ("Timothy", "Ekwaro", "STK/2026/019", s5arts, date(2009, 4, 6)),
            ("Sandra", "Nakanwagi", "STK/2026/020", s5arts, date(2009, 11, 12)),
            ("Godfrey", "Ssentongo", "STK/2026/021", p7, date(2013, 2, 4)),
            ("Mary", "Akello", "STK/2026/022", p7, date(2013, 6, 9)),
            ("Victor", "Mugisha", "STK/2026/023", p7, date(2013, 9, 28)),
            ("Ritah", "Nabirye", "STK/2026/024", p7, date(2013, 12, 1)),
        ]

        students = []
        student_users = {}
        for first, last, adm, cls, dob in student_seed:
            email = f"{first.lower()}.{last.lower()}@student.elimu.ug"
            user = await create_user(db, email, first, last, UserRole.STUDENT, school.id)
            st = Student(
                user_id=user.id,
                school_id=school.id,
                class_id=cls.id,
                admission_number=adm,
                date_of_birth=dob,
                enrollment_status=EnrollmentStatus.ACTIVE,
            )
            students.append(st)
            student_users[adm] = user

        db.add_all(students)
        await db.flush()

        by_adm = {s.admission_number: s for s in students}

        # ---------------------------------------------------------------
        # 8. PARENTS
        # ---------------------------------------------------------------
        parent = await create_user(db, "parent@elimu.ug", "Joseph", "Ssemakula", UserRole.PARENT, school.id)
        parent2 = await create_user(db, "parent2@elimu.ug", "Rose", "Achieng", UserRole.PARENT, school.id)

        # Joseph has two children at the school (a key demo point: one login, many kids)
        db.add(ParentStudentLink(school_id=school.id, parent_id=parent.id, student_id=by_adm["STK/2026/001"].id))
        db.add(ParentStudentLink(school_id=school.id, parent_id=parent.id, student_id=by_adm["STK/2026/023"].id))
        db.add(ParentStudentLink(school_id=school.id, parent_id=parent2.id, student_id=by_adm["STK/2026/002"].id))

        # ---------------------------------------------------------------
        # 9. FEE STRUCTURES + PAYMENTS
        # ---------------------------------------------------------------
        fee_defs = [
            ("Term 1 Tuition - P7", 450_000, p7),
            ("Term 1 Tuition - S1", 600_000, s1e),
            ("Term 1 Tuition - S1 (West)", 600_000, s1w),
            ("Term 1 Tuition - S2", 650_000, s2e),
            ("Term 1 Tuition - S5", 800_000, s5sci),
            ("Term 1 Tuition - S5 (Arts)", 800_000, s5arts),
            ("Library & Reading Fund", 20_000, None),
            ("Co-curricular & Development", 50_000, None),
        ]
        fee_rows = []
        for name, amount, cls in fee_defs:
            f = FeeStructure(
                school_id=school.id, name=name, amount=amount, year=YEAR, term=TERM,
                class_id=cls.id if cls else None,
            )
            fee_rows.append(f)
        db.add_all(fee_rows)
        await db.flush()

        # class -> tuition fee
        tuition = {
            p7.id: fee_rows[0], s1e.id: fee_rows[1], s1w.id: fee_rows[2],
            s2e.id: fee_rows[3], s5sci.id: fee_rows[4], s5arts.id: fee_rows[5],
        }
        extras = [fee_rows[6], fee_rows[7]]

        methods = ["Mobile Money", "Bank Deposit", "Cash"]
        ref = 1000
        for idx, st in enumerate(students):
            applicable = [tuition[st.class_id]] + extras
            # Distribution: ~40% fully paid, ~35% partial, ~25% nothing
            bucket = idx % 10
            paid_ratio = 1.0 if bucket < 4 else (0.55 if bucket < 7.5 else 0.0)
            if paid_ratio == 0.0:
                continue
            for f in applicable:
                amount = round(f.amount * paid_ratio, -3)
                if amount <= 0:
                    continue
                ref += 1
                db.add(FeePayment(
                    school_id=school.id,
                    student_id=st.id,
                    fee_structure_id=f.id,
                    amount_paid=amount,
                    payment_date=date(2026, 2, 5 + (idx % 20)),
                    payment_method=methods[idx % 3],
                    reference_number=f"REC-{ref}",
                ))

        # ---------------------------------------------------------------
        # 10. EXAMS + RESULTS
        # ---------------------------------------------------------------
        exam_defs = [
            ("Beginning of Term Test", mth_o), ("Beginning of Term Test", eng_o),
            ("Beginning of Term Test", phy_o), ("Beginning of Term Test", bio_o),
            ("Beginning of Term Test", mth_a), ("Beginning of Term Test", phy_a),
            ("Beginning of Term Test", mth_p), ("Beginning of Term Test", eng_p),
        ]
        exams = []
        for name, subj in exam_defs:
            e = Exam(school_id=school.id, name=name, year=YEAR, term=TERM, subject_id=subj.id)
            exams.append(e)
        db.add_all(exams)
        await db.flush()

        o_exams = {e.subject_id: e for e in exams if e.subject_id in (mth_o.id, eng_o.id, phy_o.id, bio_o.id)}
        a_exams = {e.subject_id: e for e in exams if e.subject_id in (mth_a.id, phy_a.id)}
        p_exams = {e.subject_id: e for e in exams if e.subject_id in (mth_p.id, eng_p.id)}

        o_subjects = [mth_o, eng_o, phy_o, bio_o]
        a_subjects = [mth_a, phy_a]
        p_subjects = [mth_p, eng_p]

        comments_hi = ["Excellent work", "Very good progress", "Strong performance", "Keep it up"]
        comments_mid = ["Fair effort, can improve", "Satisfactory", "More practice needed"]
        comments_lo = ["Needs close attention", "Below expectation — extra support required"]

        for st in students:
            if st.class_id in (s1e.id, s1w.id, s2e.id):
                subject_map, exam_map = o_subjects, o_exams
            elif st.class_id in (s5sci.id, s5arts.id):
                subject_map, exam_map = a_subjects, a_exams
            elif st.class_id == p7.id:
                subject_map, exam_map = p_subjects, p_exams
            else:
                continue

            base = random.randint(48, 88)
            for subj in subject_map:
                score = max(12, min(99, base + random.randint(-18, 12)))
                if score >= 80:
                    comment = random.choice(comments_hi)
                elif score >= 60:
                    comment = random.choice(comments_mid)
                else:
                    comment = random.choice(comments_lo)
                db.add(Result(
                    school_id=school.id,
                    exam_id=exam_map[subj.id].id,
                    student_id=st.id,
                    score=float(score),
                    teacher_comment=comment,
                ))

        # ---------------------------------------------------------------
        # 11. ATTENDANCE (last 8 weekdays for S1 East + P7)
        # ---------------------------------------------------------------
        days = []
        d = date(2026, 10, 26)
        while len(days) < 8:
            if d.weekday() < 5:
                days.append(d)
            d += timedelta(days=1)

        for cls in (s1e, p7):
            class_students = [s for s in students if s.class_id == cls.id]
            for day in days:
                for st in class_students:
                    roll = random.random()
                    if roll < 0.86:
                        status = AttendanceStatus.PRESENT
                    elif roll < 0.94:
                        status = AttendanceStatus.ABSENT
                    else:
                        status = AttendanceStatus.LATE
                    db.add(Attendance(
                        school_id=school.id, student_id=st.id, class_id=cls.id,
                        attendance_date=day, status=status,
                        remarks="Reported late" if status == AttendanceStatus.LATE else None,
                    ))

        # ---------------------------------------------------------------
        # 12. NOTIFICATIONS
        # ---------------------------------------------------------------
        notes = [
            (headteacher, "Term 1 Opening", "Welcome back to Term 1 2026. Classes resume on 2 February.", NotificationType.IN_APP),
            (parent, "Fee Balance Reminder", "Please clear the outstanding balance for Brian before the mid-term break.", NotificationType.IN_APP),
            (t1.id, "Staff Meeting", "There will be a staff meeting on Friday at 4:00 PM in the main hall.", NotificationType.IN_APP),
        ]
        for recipient, title, msg, ntype in notes:
            recipient_id = recipient.id if hasattr(recipient, "id") else recipient
            db.add(Notification(
                school_id=school.id, recipient_id=recipient_id, title=title, message=msg,
                type=ntype, status=NotificationStatus.SENT, is_read=False,
            ))

        await db.commit()

        print("✅ Demo tenant seeded successfully.\n")
        print("=" * 62)
        print("  ELIMU DEMO — LOGIN CREDENTIALS (password for all: Elimu@2026)")
        print("=" * 62)
        print(f"  Super Admin   : admin@elimu.ug")
        print(f"  School Admin  : headteacher@elimu.ug")
        print(f"  Teacher       : teacher@elimu.ug")
        print(f"  Student       : brian.ssemakula@student.elimu.ug")
        print(f"  Parent        : parent@elimu.ug")
        print("=" * 62)
        print(f"  School        : {school.name}")
        print(f"  Students      : {len(students)}")
        print(f"  Classes       : {len(classes)}")
        print(f"  Academic year : {YEAR} / Term {TERM}")
        print("=" * 62)


if __name__ == "__main__":
    asyncio.run(main())
