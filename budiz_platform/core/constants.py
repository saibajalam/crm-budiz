LEAD_STATUS_CHOICES = (
    ("new", "New"),
    ("contacted", "Contacted"),
    ("qualified", "Qualified"),
    ("converted", "Converted"),
    ("unqualified", "Unqualified"),
    ("lost", "Lost"),
)

LEAD_SOURCE_CHOICES = (
    ("website", "Website"),
    ("referral", "Referral"),
    ("social_media", "Social Media"),
    ("email_campaign", "Email Campaign"),
    ("event", "Event"),
    ("cold_call", "Cold Call"),
    ("other", "Other"),
)

ROLE_SUPERADMIN = "SuperAdmin"
ROLE_ADMIN = "Admin"
ROLE_MANAGER = "Manager"
ROLE_SALES_REP = "Sales Representative"

DEFAULT_ROLES = [
    ROLE_SUPERADMIN,
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_SALES_REP,
]

PRIORITY_CHOICES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
]

ACTIVITY_TYPES = [
    ("call", "Call"),
    ("email", "Email"),
    ("meeting", "Meeting"),
    ("note", "Note"),
    ("task", "Task"),
]
