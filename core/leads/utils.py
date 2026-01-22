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