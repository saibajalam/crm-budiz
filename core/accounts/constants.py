LEAD_STATUS_CHOICES = (
    ("NEW", "New"),
    ("CONTACTED", "Contacted"),
    ("QUALIFIED", "Qualified"),
    ("UNQUALIFIED", "Unqualified"),
    ("LOST", "Lost"),
)

LEAD_SOURCE_CHOICES = (
    ("WEBSITE", "Website"),
    ("REFERRAL", "Referral"),
    ("SOCIAL_MEDIA", "Social Media"),
    ("EMAIL_CAMPAIGN", "Email Campaign"),
    ("EVENT", "Event"),
    ("COLD_CALL", "Cold Call"),
    ("OTHER", "Other"),
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