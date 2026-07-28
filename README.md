# CRM-Budiz

A scalable, multi-workspace Customer Relationship Management (CRM) backend built with **Django REST Framework**. The system enables organizations to manage leads, deals, contacts, workspaces, analytics, automation, and user permissions while maintaining strict workspace-level data isolation.

## 🚀 Features

### Authentication & Authorization
- JWT Authentication
- User Registration & Login
- Password Reset
- Refresh Tokens
- Role-Based Access Control (RBAC)
- Permission-Based API Access

### Multi-Workspace Architecture
- Multiple workspaces support
- Workspace invitations
- Workspace member management
- Workspace-specific roles
- Complete data isolation between workspaces

### Lead Management
- Create, update, retrieve, and delete leads
- Lead assignment
- Lead activities
- Lead attachments
- Lead status tracking
- Workspace-specific lead numbering

### Deal Management
- Full CRUD operations
- Deal pipelines
- Deal stages
- Deal assignment
- Deal activities
- Deal-contact relationships
- Workspace-specific deal numbering

### Contact Management
- Create contacts
- Update contacts
- Delete contacts
- Associate contacts with deals
- Global contact search

### Dashboard & Analytics
- Dashboard overview
- Lead analytics
- Deal analytics
- Revenue analytics
- Conversion funnel
- Performance metrics
- Trend analysis
- Workspace analytics

### Search
- Global search
- Lead search
- Deal search
- Contact search

### Subscription System
- Trial subscriptions
- Active subscription validation
- Subscription plans
- Workspace subscription management

### Notifications
- User notifications
- Workspace notifications

### Automation
- Business workflow support
- Activity tracking
- Event logging

---

# 🏗 Architecture

The project follows a modular architecture where each business domain is separated into individual Django apps.

```
CRM-Budiz
│
├── accounts/
├── workspaces/
├── leads/
├── deals/
├── contacts/
├── analytics/
├── dashboard/
├── subscriptions/
├── automation/
├── notifications/
└── common/
```

Key architectural principles:

- Workspace-first architecture
- Separation of concerns
- RESTful API design
- Modular application structure
- Role-based authorization
- Scalable database design

---

# 🛠 Tech Stack

Backend

- Python
- Django
- Django REST Framework

Database

- PostgreSQL

Authentication

- JWT Authentication

Task Queue

- Celery

Deployment

- Gunicorn
- Nginx

Other Tools

- Git
- GitHub
- Postman

---

# 🔒 Security

- JWT authentication
- Role-based access control
- Workspace-level data isolation
- Object-level permission checks
- Secure password hashing
- Input validation
- Serializer validation

---

# 📊 Core Modules

- Authentication
- User Management
- Workspace Management
- Lead Management
- Deal Management
- Contact Management
- Analytics
- Dashboard
- Notifications
- Subscription Management
- Automation

---

# 📌 API Design

The backend follows RESTful API principles.

Example endpoints:

```
POST   /api/auth/login/
POST   /api/auth/register/

GET    /api/workspaces/
POST   /api/workspaces/

GET    /api/leads/
POST   /api/leads/

GET    /api/deals/
POST   /api/deals/

GET    /api/contacts/
POST   /api/contacts/

GET    /api/analytics/
GET    /api/dashboard/
```

---

# ⚡ Highlights

- Multi-tenant CRM architecture
- Workspace-based data isolation
- JWT Authentication
- Role & Permission Management
- Analytics Dashboard
- Lead & Deal Pipelines
- Contact Management
- Global Search
- Subscription System
- Clean REST API Design
- PostgreSQL integration
- Production-ready backend architecture

---

# 📈 Future Enhancements

- Email Integration
- Calendar Integration
- WebSocket-based Real-time Notifications
- AI-powered Lead Scoring
- Advanced Reporting
- Audit Logs
- CRM Workflow Automation
- Third-party Integrations (Slack, Google, Outlook)

---

# 👨‍💻 Author

**Saibaj Alam**

Backend Developer

**Tech Stack**

Python • Django • Django REST Framework • PostgreSQL • REST APIs
