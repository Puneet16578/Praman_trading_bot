from datetime import date

def outcome_firewall(event_date: str) -> None:
    """
    Firewall to prevent computing outcomes for events in the forward window (2026-09-16 onward)
    before 2027-06-01, as per pre-registration rules.
    """
    if event_date >= "2026-09-16":
        today = date.today().isoformat()
        if today < "2027-06-01":
            raise ValueError(f"FIREWALL BREACH: Outcome requested for {event_date} but it is strictly forward-window and today is {today} (< 2027-06-01).")
