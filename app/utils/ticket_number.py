from datetime import datetime, timezone


def generate_ticket_number():
    from app.models.ticket import Ticket
    today = datetime.now(timezone.utc)
    date_str = today.strftime('%Y%m%d')
    prefix = f'TICK-{date_str}-'

    count = Ticket.query.filter(
        Ticket.ticket_number.like(f'{prefix}%')
    ).count()

    return f'{prefix}{count + 1:04d}'
