from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone


def send_lead_conversion_notification(lead, deal, converted_by):
    """
    Send email notification when a lead is converted to a deal.

    Args:
        lead: The Lead instance that was converted
        deal: The Deal instance that was created
        converted_by: The User who performed the conversion
    """
    subject = f"Lead Converted: {lead.first_name} {lead.last_name}"

    # Get workspace members to notify (excluding the converter)
    workspace_members = lead.workspace.members.exclude(user=converted_by)

    recipient_emails = []
    for member in workspace_members:
        if member.user.email:
            recipient_emails.append(member.user.email)

    if not recipient_emails:
        return  # No one to notify

    # Prepare context for email template
    context = {
        "lead": lead,
        "deal": deal,
        "converted_by": converted_by,
        "workspace": lead.workspace,
        "conversion_date": timezone.now(),
        "frontend_url": settings.FRONTEND_URL,
    }

    # Render email content
    html_message = render_to_string("emails/lead_conversion.html", context)
    plain_message = render_to_string("emails/lead_conversion.txt", context)

    # Send email
    send_mail(
        subject=subject,
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_emails,
        fail_silently=True,  # Don't crash if email fails
    )


def send_lead_conversion_confirmation(lead, deal, converted_by):
    """
    Send confirmation email to the user who performed the conversion.

    Args:
        lead: The Lead instance that was converted
        deal: The Deal instance that was created
        converted_by: The User who performed the conversion
    """
    if not converted_by.email:
        return

    subject = f"Lead Conversion Confirmed: {lead.first_name} {lead.last_name}"

    context = {
        "lead": lead,
        "deal": deal,
        "converted_by": converted_by,
        "workspace": lead.workspace,
        "conversion_date": timezone.now(),
        "frontend_url": settings.FRONTEND_URL,
    }

    # Render email content
    html_message = render_to_string("emails/lead_conversion_confirmation.html", context)
    plain_message = render_to_string("emails/lead_conversion_confirmation.txt", context)

    # Send email
    send_mail(
        subject=subject,
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[converted_by.email],
        fail_silently=True,
    )
