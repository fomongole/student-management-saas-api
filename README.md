# Student Management SaaS (Enterprise Edition)

A high-performance, multi-tenant School Management System built with **FastAPI**, **SQLAlchemy 2.0**, and **PostgreSQL**. This platform is designed as a scalable SaaS where multiple schools (tenants) can manage students, academics, and finances in complete isolation.

---

## 🚀 Key Features

* **Strict Multi-Tenancy:** Data isolation at the database level using `school_id` filtering.
* **Role-Based Access Control (RBAC):** Granular permissions for Super Admins, School Admins, Teachers, Students, and Parents.
* **Academic Engine:** Attendance tracking with automated alerts, exam management, and dynamic report card generation.
* **Financial Ledger:** Immutable payment tracking, fee structures, and real-time balance calculations.
* **Communication Layer:** Asynchronous background notifications (Email/SMS) using FastAPI Background Tasks.
* **Parent Portal:** Secure bridging of parent accounts to multiple student profiles.
* **Analytics Dashboards:** Executive summaries for both School Admins and SaaS Platform Owners (Super Admins).

---

## 🛠 Tech Stack

* **Framework:** FastAPI (Python 3.12+)
* **Database:** PostgreSQL 15 (Async via `asyncpg`)
* **ORM:** SQLAlchemy 2.0 (Mapped Declarative Models)
* **Migrations:** Alembic
* **Validation:** Pydantic V2
* **Security:** JWT (OAuth2 with Password Flow), Passlib (Bcrypt)
* **Task Queue:** FastAPI BackgroundTasks
* **Infrastructure:** Docker & Docker Compose

---

## 📁 Project Structure

```text
Student Management SaaS/
├── app/
│   ├── auth/           # Authentication & User Management
│   ├── schools/        # Tenant (School) Onboarding & Platform Metrics
│   ├── students/       # Student Profiles & Admission
│   ├── classes/        # Academic Levels & Streams
│   ├── subjects/       # Curriculum Management
│   ├── attendance/     # Daily Tracking & Safety Alerts
│   ├── exams/          # Assessment Recording
│   ├── grades/         # Grading Scales & Report Card Engine
│   ├── fees/           # Financial Ledger & Invoicing
│   ├── notifications/  # Async Alert System
│   ├── reports/        # Admin Analytics Dashboards
│   ├── core/           # Security, Config, Enums, & Dependencies
│   ├── db/             # Base Models & Session Management
│   └── main.py         # App Entrypoint
├── alembic/            # Database Migration Scripts
├── tests/              # Pytest Suite
├── Dockerfile          # API Production Build
└── docker-compose.yml  # Multi-Container Orchestration
```

## 🔐 Multi-Tenant Security Policy

This system implements **Logical Isolation** to ensure data integrity across multiple school tenants. Every database table (with the exception of global `schools` and `users`) inherits from the `TenantModel` mixin, which enforces a mandatory `school_id` column.

### 🛡️ Core Security Pillars

* **Isolation:** The service layer provides implicit multi-tenancy. Every database query is automatically filtered by the `current_user.school_id` extracted from the JWT, ensuring one school can never "see" another's data.
* **Privacy:** Access is scoped by role. **Students** and **Parents** are further restricted by an ownership check; they can only access records specifically linked to their `user_id` or authorized through the `ParentStudentLink` bridge table.
* **Persistence:** To prevent "ghost data," the system uses strict foreign key constraints. Deleting a school tenant triggers a `CASCADE` delete, safely and permanently wiping all associated students, staff, academic records, and financial transactions.