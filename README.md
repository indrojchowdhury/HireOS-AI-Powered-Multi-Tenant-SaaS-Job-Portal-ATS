# 🤖 HireOS – AI-Powered Multi-Tenant SaaS Portal (Full-Stack)

HireOS is a production-grade recruitment software and Applicant Tracking System (ATS) built to handle multi-tenant business structures, automated AI resume screening, asynchronous background automation, and scalable subscription flows. It bridges a modern React frontend with a high-concurrency Django REST Framework backend.

---

## 📖 Project Summary

Managing recruitment at scale is often slow and resource-heavy for businesses. HireOS solves this by providing unique, isolated dashboards for multiple corporate clients (multi-tenancy) under one platform. The system uses AI to instantly parse and score candidate resumes, processes heavy workloads (like PDF generation and email queues) asynchronously to prevent system lag, and secures sensitive applicant files. It also includes the structural layout for B2B premium monetization and automated interview scheduling.

---

## 🔥 Key Features

### 1. Multi-Tenant SaaS Engine
- Built-in multi-tenancy layer allowing multiple companies to manage their data in strict isolation.
- Separate control panels and tailored workflows for Employers and Job Seekers.
- Custom server-side fixed pagination (10 items per page) to prevent browser memory leaks during massive listing loads.

### 2. AI-Powered ATS Pipelines
- Integrated Google Gemini LLM via background workers to automatically read uploaded candidate resumes.
- Generates structural matching scores, keyword analysis, and analytical insights instantly on the recruiter's panel.
- Built-in failure boundaries and database-level structural migrations to handle automated static scoring if the external AI APIs experience downtime, preventing dashboard crashes.

### 3. Dynamic Kanban Dashboard
- Designed an interactive drag-and-drop recruitment pipeline using React 19 and Tailwind CSS.
- Implemented optimistic frontend rendering paired with sequential backend PATCH requests, meaning the UI updates instantly while status switches sync seamlessly with the API.

### 4. Asynchronous Task Automation
- Coupled Celery with a Redis broker to handle all heavyweight, non-blocking application workloads.
- Automated professional PDF offer letter generation on the fly using ReportLab upon candidate approval.
- Background asynchronous bulk CSV analytical exports and email dispatchers with file attachments, keeping the main application thread completely free.
- Configured Celery Beat midnight clock automation to execute daily sweeps across the database, automatically updating status hooks to expire past-deadline job listings.

### 5. Advanced Security & Data Protection
- Engineered an email-based Custom User Model replacing default Django auth, integrated with granular Role-Based Access Control (RBAC).
- Stateless session management using SimpleJWT access and refresh token rotation with explicit HTTP cookie allowance rules.
- High-level media protection by moving uploaded candidate resumes out of public directories into a secure storage infrastructure, guarded by a custom API view restricting access exclusively to the applicant and the job-posting employer.

### 6. Database & Performance Optimization
- Eradicated SQL N+1 logging overhead across core application endpoints by implementing strict `select_related()` and `prefetch_related()` hooks, boosting query speeds by 10x.
- Encapsulated heavy bulk database transactions inside atomic blocks to prevent connection pool exhaustion during concurrent operations.

### 7. B2B Monetization & Third-Party Integration
- Built the structural framework for a premium B2B subscription tier, scaffolding payment test environments for Stripe and SSLCommerz verification loops.
- Integrated a Google Calendar API blueprint for automated candidate interview time-slot booking.

---

## 🧰 Tech Stack

- **Backend Framework:** Python, Django, Django REST Framework (DRF)
- **Task Orchestration:** Celery, Celery Beat, Redis Broker
- **Frontend Architecture:** React 19, Vite, Tailwind CSS, Axios, JavaScript (ES6+)
- **Database System:** PostgreSQL
- **DevOps & Tooling:** Docker, Docker Compose, Linux Bash Environment, Postman, Git
- **External APIs:** Google Gemini AI Engine, ReportLab PDF, SimpleJWT, SSLCommerz / Stripe Test Gateways
