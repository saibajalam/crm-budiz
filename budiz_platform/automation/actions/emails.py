def execute(payload, params, workspace, user):
    """
    Send an email.
    params = {"to": "email@example.com", "subject": "Test", "body": "Hello"}
    """
    to_email = params.get("to")
    subject = params.get("subject")
    body = params.get("body")

    if not to_email:
        return False

    # For now, just print (replace with actual email later)
    print(f"Sending email to {to_email}: {subject}\n{body}")
    return True
