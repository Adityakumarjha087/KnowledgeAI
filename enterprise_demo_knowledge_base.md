# ACME Global Technologies - Enterprise Employee Handbook & Operational Guidelines

## 1. Overview & Workplace Culture
Welcome to ACME Global Technologies. We provide next-generation cloud infrastructure, enterprise artificial intelligence solutions, and secure data storage. Our mission is to empower global businesses with resilient, scalable software systems.

---

## 2. Working Hours, Flexibility & Remote Work Policy
- **Core Hours:** Core collaboration hours are 10:00 AM to 4:00 PM in your local time zone.
- **Remote Work:** ACME operates as a hybrid-first company. Team members may work from home up to 3 days per week with manager coordination.
- **Home Office Stipend:** Every full-time employee receives a one-time $1,000 reimbursement for ergonomic home office furniture and necessary peripherals upon joining.

---

## 3. Leave & Paid Time Off (PTO) Policies

### 3.1 Annual Leave
- Full-time regular employees are entitled to **20 days of paid annual leave** per calendar year.
- Up to 5 unused leave days can be rolled over to the subsequent calendar year.
- Leave requests exceeding 3 consecutive business days must be submitted at least 2 weeks in advance via the HR Portal.

### 3.2 Sick & Medical Leave
- Employees receive **10 days of paid sick leave** annually.
- For medical absences extending beyond 2 consecutive business days, manager approval and a formal doctor's certificate are required.

### 3.3 Parental Leave
- Primary caregivers are eligible for **16 weeks of 100% paid parental leave**.
- Secondary caregivers receive **6 weeks of 100% paid parental leave**.
- Parental leave must be taken within the first 12 months of the child's birth or legal adoption.

### 3.4 Public Holidays
- ACME observes 11 standard national public holidays. Thanksgiving occurs in November and Christmas is celebrated on December 25th.

---

## 4. Health, Wellness & Benefits

### 4.1 Medical & Dental Insurance
- ACME covers 90% of healthcare premiums for employees and 75% for eligible dependents under the Premium Health Plan.
- Annual optical and dental wellness allowance of $500 is available through payroll claims.

### 4.2 Professional Development
- Each engineer and product team member has an annual **$1,500 continuous learning budget** for certifications, books, and conference tickets.

---

## 5. Travel & Expense Reimbursement

- **Meals & Daily Incidentals (Per Diem):** Up to $75/day during domestic business travel and $110/day during international travel without prior executive approval.
- **Flight Policy:** Economy class for flights under 6 hours; Premium Economy or Business Class allowed for international flights exceeding 6 continuous hours.
- **Expense Submission:** All receipts must be uploaded to the Expensify portal within 30 days of expense incurrence.

---

## 6. Information Security & Engineering Standards

### 6.1 Authentication & Device Security
- All employees must enforce Multi-Factor Authentication (MFA / 2FA) on their corporate email, GitHub, and cloud provider consoles.
- Hardcoded credentials, private keys, or raw API secrets must **never** be committed into Git repositories.
- Workstations must be encrypted using BitLocker (Windows) or FileVault (macOS) and locked whenever left unattended.

### 6.2 Code Review & Deployment Standards
- All code pull requests require approval from at least one senior peer before merging into `main`.
- Continuous Integration (CI) pipelines must pass linting, type checks, unit tests, and security dependency audits prior to production deployment.
- High-severity security vulnerabilities detected in production must be triaged within 4 hours by the on-call Site Reliability Engineer (SRE).

---

## 7. AI & Enterprise Data Confidentiality Policy
- Proprietary customer data and source code must not be submitted into unapproved, public AI consumer tools.
- When utilizing internal AI assistants, ensure data classifications (Confidential vs Public) are respected.
- Automated retrieval-augmented generation (RAG) pipelines must maintain vector privacy isolation across distinct tenant accounts.

---

## 8. Emergency Contacts & Support Directory
- **IT & Security Helpdesk:** `security-helpdesk@acme-global.com` (Slack: `#it-support`)
- **HR & People Operations:** `people-ops@acme-global.com` (Slack: `#ask-hr`)
- **Facilities & Office Management:** `workplace@acme-global.com`
