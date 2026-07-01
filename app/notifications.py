from flask import current_app
from flask_mail import Message
from app.extensions import mail


def _send(subject, recipients, body):
    try:
        msg = Message(subject=subject, recipients=recipients, body=body)
        mail.send(msg)
    except Exception as e:
        current_app.logger.warning(f'Email send failed: {e}')


def notify_ticket_created(ticket):
    _send(
        subject=f'[{ticket.ticket_number}] Support ticket received',
        recipients=[ticket.customer_email],
        body=(
            f'Your support ticket has been created.\n'
            f'Ticket number: {ticket.ticket_number}\n'
            f'Subject: {ticket.subject}\n'
        ),
    )


def notify_ticket_assigned(ticket, agent):
    _send(
        subject=f'[{ticket.ticket_number}] Ticket assigned to you',
        recipients=[agent.email],
        body=(
            f'Ticket {ticket.ticket_number} has been assigned to you.\n'
            f'Subject: {ticket.subject}\n'
            f'Priority: {ticket.priority}\n'
        ),
    )


def notify_status_changed(ticket, new_status):
    recipients = [ticket.customer_email]
    if ticket.assignee:
        recipients.append(ticket.assignee.email)
    _send(
        subject=f'[{ticket.ticket_number}] Status updated: {new_status}',
        recipients=list(set(recipients)),
        body=(
            f'Ticket {ticket.ticket_number} status changed to "{new_status}".\n'
            f'Subject: {ticket.subject}\n'
        ),
    )


def notify_comment_added(ticket, comment):
    recipients = [ticket.customer_email]
    if ticket.assignee:
        recipients.append(ticket.assignee.email)
    _send(
        subject=f'[{ticket.ticket_number}] New comment added',
        recipients=list(set(recipients)),
        body=(
            f'A new comment was added to ticket {ticket.ticket_number}.\n'
            f'Subject: {ticket.subject}\n'
        ),
    )
