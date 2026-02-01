ACTIVITY_SCORE_MAP = {
    "call": 10,
    "email": 5,
    "meeting": 20,
    "note": 2,
    "task": 3,
    "attachments": 15,
}


def update_lead_score(lead, activity_type):
    score_increment = ACTIVITY_SCORE_MAP.get(activity_type, 0)
    lead.score = min(lead.score + score_increment, 100)
    lead.save(update_fields=["score"])


from django.utils import timezone


def get_activity_status(activity):
    now = timezone.now()

    if activity.is_completed:
        return "completed"
    elif activity.due_date < now:
        return "overdue"
    return "upcoming"
