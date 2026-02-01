class WorkspaceRole:
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    SALES = "sales"

    CHOICES = (
        (OWNER, "Owner"),
        (ADMIN, "Admin"),
        (MANAGER, "Manager"),
        (SALES, "Sales Representative"),
    )