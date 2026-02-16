from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from datetime import timedelta
from subscriptions.models import (
    SubscriptionStatus,
    UserSubscription,
    WorkspaceSubscription,
)


class Command(BaseCommand):
    help = "Send subscription expiry reminders for both companies and individual users"

    def handle(self, *args, **kwargs):
        today = timezone.now().date()

        # Loop over all reminder days
        for days_before in settings.SUBSCRIPTION_REMINDER_DAYS:
            reminder_date = today + timedelta(days=days_before)

            workspace_subs = WorkspaceSubscription.objects.filter(
                expires_at__date=reminder_date,
                status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL],
            ).select_related("workspace", "workspace__owner")

            for sub in workspace_subs:
                if days_before in sub.reminder_sent_days:
                    continue

                workspace = sub.workspace
                owner_email = getattr(workspace.owner, "email", None)
                if owner_email:
                    send_mail(
                        subject="Your workspace subscription is about to expire",
                        message=(
                            f"Hello {workspace.owner.full_name}, your workspace "
                            f"subscription for {workspace.name} will expire on "
                            f"{sub.expires_at.date()}. Please renew it to avoid interruption."
                        ),
                        from_email="noreply@yourcrm.com",
                        recipient_list=[owner_email],
                        fail_silently=False,
                    )
                    sub.reminder_sent_days.append(days_before)
                    sub.save(update_fields=["reminder_sent_days"])
                    self.stdout.write(
                        f"Reminder sent to workspace: {workspace.name} ({days_before} days before)"
                    )

            # user subscriptions
            user_subs = UserSubscription.objects.filter(
                expires_at__date=reminder_date,
                status__in=[SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL],
            )
            for sub in user_subs:
                if days_before in sub.reminder_sent_days:
                    continue

                user = sub.user
                send_mail(
                    subject="Your trial is about to expire",
                    message=(
                        f"Hello {user.full_name}, your subscription ends on "
                        f"{sub.expires_at.date()}. Please upgrade to continue using our services."
                    ),
                    from_email="noreply@yourcrm.com",
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                sub.reminder_sent_days.append(days_before)
                sub.save(update_fields=["reminder_sent_days"])
                self.stdout.write(
                    f"Reminder sent to user: {user.email} ({days_before} days before)"
                )
