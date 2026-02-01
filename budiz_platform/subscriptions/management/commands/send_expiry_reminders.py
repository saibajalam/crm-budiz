from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from datetime import timedelta
from subscriptions.models import CompanySubscription, UserSubscription

class Command(BaseCommand):
    help = "Send subscription expiry reminders for both companies and individual users"

    def handle(self, *args, **kwargs):
        today = timezone.now().date()

        # Loop over all reminder days
        for days_before in settings.SUBSCRIPTION_REMINDER_DAYS:
            reminder_date = today + timedelta(days=days_before)

            # company subscriptions
            company_subs = CompanySubscription.objects.filter(
                ends_at__date=reminder_date,
                is_active=True
            )
            for sub in company_subs:
                if days_before in sub.reminder_sent_days:
                    continue  

                company = sub.company
                if hasattr(company, "email") and company.email:
                    send_mail(
                        subject="Your subscription is about to expire",
                        message=f"Hello {company.name}, your subscription will expire on {sub.ends_at.date()}. Please renew it to avoid interruption.",
                        from_email="noreply@yourcrm.com",
                        recipient_list=[company.email],
                        fail_silently=False,
                    )
                    sub.reminder_sent_days.append(days_before)
                    sub.save(update_fields=["reminder_sent_days"])
                    self.stdout.write(f"Reminder sent to company: {company.name} ({days_before} days before)")

            # user subscriptions
            user_subs = UserSubscription.objects.filter(
                ends_at__date=reminder_date,
                is_active=True
            )
            for sub in user_subs:
                if days_before in sub.reminder_sent_days:
                    continue  

                user = sub.user
                send_mail(
                    subject="Your trial is about to expire",
                    message=f"Hello {user.full_name}, your subscription ends on {sub.ends_at.date()}. Please upgrade to continue using our services.",
                    from_email="noreply@yourcrm.com",
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                sub.reminder_sent_days.append(days_before)
                sub.save(update_fields=["reminder_sent_days"])
                self.stdout.write(f"Reminder sent to user: {user.email} ({days_before} days before)")
