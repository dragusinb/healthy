#!/usr/bin/env python3
"""
CLI tool for managing support tickets.

This script allows Claude Code to interact with support tickets:
- List pending tickets
- View ticket details and screenshots
- Mark tickets as resolved, skipped, or escalated

Usage:
    python tickets.py list [--status=pending]
    python tickets.py show <id>
    python tickets.py resolve <id> "response message"
    python tickets.py skip <id> "reason"
    python tickets.py escalate <id> "reason"
    python tickets.py stats

Examples:
    python tickets.py list
    python tickets.py list --status=fixed
    python tickets.py show 1
    python tickets.py resolve 1 "Fixed the button alignment issue in Dashboard.jsx"
    python tickets.py skip 1 "User error, no bug found"
    python tickets.py escalate 1 "Requires database migration"
"""

import sys
import os
from datetime import datetime, timezone
import argparse

# Add parent directory to path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# Load .env file before importing database module
from dotenv import load_dotenv
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import models
try:
    from backend_v2.models import SupportTicket, SupportTicketAttachment
    from backend_v2.database import DATABASE_URL
    from backend_v2.services.email_service import get_email_service
except ImportError:
    from models import SupportTicket, SupportTicketAttachment
    from database import DATABASE_URL
    from services.email_service import get_email_service


def get_db_session():
    """Create a database session."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()


def list_tickets(status=None):
    """List tickets filtered by AI status."""
    db = get_db_session()

    query = db.query(SupportTicket).order_by(SupportTicket.created_at.desc())

    if status:
        query = query.filter(SupportTicket.ai_status == status)

    tickets = query.all()

    if not tickets:
        print(f"No tickets found" + (f" with status '{status}'" if status else ""))
        return

    print(f"\n{'ID':<6} {'Ticket#':<12} {'Status':<12} {'AI Status':<12} {'Created':<20} {'Page URL'}")
    print("-" * 100)

    for t in tickets:
        created = t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else "N/A"
        page = t.page_url[:50] + "..." if len(t.page_url) > 50 else t.page_url
        print(f"{t.id:<6} {t.ticket_number:<12} {t.status:<12} {t.ai_status:<12} {created:<20} {page}")

    print(f"\nTotal: {len(tickets)} ticket(s)")
    db.close()


def show_ticket(ticket_id):
    """Show detailed information about a ticket."""
    db = get_db_session()

    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()

    if not ticket:
        print(f"Error: Ticket with ID {ticket_id} not found")
        db.close()
        return

    print("\n" + "=" * 60)
    print(f"TICKET: {ticket.ticket_number}")
    print("=" * 60)
    print(f"ID:           {ticket.id}")
    print(f"Status:       {ticket.status}")
    print(f"AI Status:    {ticket.ai_status}")
    print(f"Priority:     {ticket.priority}")
    print(f"Type:         {ticket.type}")
    print(f"Created:      {ticket.created_at}")
    print(f"Updated:      {ticket.updated_at}")
    print()
    print(f"Reporter:     {ticket.reporter_email}")
    if ticket.reporter_name:
        print(f"Reporter Name: {ticket.reporter_name}")
    print()
    print(f"Page URL:     {ticket.page_url}")
    print()
    print("DESCRIPTION:")
    print("-" * 40)
    print(ticket.description)
    print("-" * 40)

    if ticket.ai_response:
        print()
        print("AI RESPONSE:")
        print("-" * 40)
        print(ticket.ai_response)
        print("-" * 40)

    # Show attachments
    if ticket.attachments:
        print()
        print("ATTACHMENTS:")
        for att in ticket.attachments:
            print(f"  - {att.file_name}")
            print(f"    Path: {att.file_path}")
            print(f"    Type: {att.file_type}")
            print(f"    Size: {att.file_size} bytes")

    print()
    db.close()


def resolve_ticket(ticket_id, response):
    """Mark a ticket as fixed with a response."""
    db = get_db_session()

    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()

    if not ticket:
        print(f"Error: Ticket with ID {ticket_id} not found")
        db.close()
        return

    ticket.ai_status = "fixed"
    ticket.ai_response = response
    ticket.ai_fixed_at = datetime.now(timezone.utc)
    ticket.status = "resolved"
    ticket.resolved_at = datetime.now(timezone.utc)
    ticket.updated_at = datetime.now(timezone.utc)

    db.commit()
    print(f"Ticket {ticket.ticket_number} marked as FIXED")

    # Send email notification
    if ticket.reporter_email:
        try:
            email_service = get_email_service()
            if email_service.is_configured():
                sent = email_service.send_ticket_resolved_email(
                    to_email=ticket.reporter_email,
                    ticket_number=ticket.ticket_number,
                    resolution_message=response,
                    language="ro"
                )
                if sent:
                    print(f"Email notification sent to {ticket.reporter_email}")
                else:
                    print(f"Warning: Failed to send email notification")
            else:
                print("Warning: Email service not configured, notification not sent")
        except Exception as e:
            print(f"Warning: Failed to send email: {e}")

    db.close()


def skip_ticket(ticket_id, reason, send_email=True):
    """Mark a ticket as skipped (won't fix)."""
    db = get_db_session()

    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()

    if not ticket:
        print(f"Error: Ticket with ID {ticket_id} not found")
        db.close()
        return

    ticket.ai_status = "skipped"
    ticket.ai_response = f"Skipped: {reason}"
    ticket.status = "closed"
    ticket.updated_at = datetime.now(timezone.utc)

    db.commit()
    print(f"Ticket {ticket.ticket_number} marked as SKIPPED")

    # Send email notification
    if send_email and ticket.reporter_email:
        try:
            email_service = get_email_service()
            if email_service.is_configured():
                sent = email_service.send_ticket_resolved_email(
                    to_email=ticket.reporter_email,
                    ticket_number=ticket.ticket_number,
                    resolution_message=reason,
                    language="ro"
                )
                if sent:
                    print(f"Email notification sent to {ticket.reporter_email}")
                else:
                    print(f"Warning: Failed to send email notification")
            else:
                print("Warning: Email service not configured, notification not sent")
        except Exception as e:
            print(f"Warning: Failed to send email: {e}")

    db.close()


def escalate_ticket(ticket_id, reason):
    """Mark a ticket as needing human intervention."""
    db = get_db_session()

    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()

    if not ticket:
        print(f"Error: Ticket with ID {ticket_id} not found")
        db.close()
        return

    ticket.ai_status = "escalated"
    ticket.ai_response = f"Escalated: {reason}"
    ticket.updated_at = datetime.now(timezone.utc)

    db.commit()
    print(f"Ticket {ticket.ticket_number} marked as ESCALATED for human review")
    db.close()


def show_stats():
    """Show ticket statistics."""
    db = get_db_session()

    total = db.query(SupportTicket).count()
    pending = db.query(SupportTicket).filter(SupportTicket.ai_status == "pending").count()
    fixed = db.query(SupportTicket).filter(SupportTicket.ai_status == "fixed").count()
    skipped = db.query(SupportTicket).filter(SupportTicket.ai_status == "skipped").count()
    escalated = db.query(SupportTicket).filter(SupportTicket.ai_status == "escalated").count()
    processing = db.query(SupportTicket).filter(SupportTicket.ai_status == "processing").count()

    print("\n" + "=" * 40)
    print("TICKET STATISTICS")
    print("=" * 40)
    print(f"Total:      {total}")
    print(f"Pending:    {pending}")
    print(f"Processing: {processing}")
    print(f"Fixed:      {fixed}")
    print(f"Skipped:    {skipped}")
    print(f"Escalated:  {escalated}")
    print()
    db.close()


def main():
    parser = argparse.ArgumentParser(description="Support ticket management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List tickets")
    list_parser.add_argument("--status", help="Filter by AI status (pending, fixed, skipped, escalated)")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show ticket details")
    show_parser.add_argument("id", type=int, help="Ticket ID")

    # Resolve command
    resolve_parser = subparsers.add_parser("resolve", help="Mark ticket as fixed")
    resolve_parser.add_argument("id", type=int, help="Ticket ID")
    resolve_parser.add_argument("response", help="Resolution response/description of fix")

    # Skip command
    skip_parser = subparsers.add_parser("skip", help="Mark ticket as skipped (won't fix)")
    skip_parser.add_argument("id", type=int, help="Ticket ID")
    skip_parser.add_argument("reason", help="Reason for skipping")

    # Escalate command
    escalate_parser = subparsers.add_parser("escalate", help="Escalate ticket to human")
    escalate_parser.add_argument("id", type=int, help="Ticket ID")
    escalate_parser.add_argument("reason", help="Reason for escalation")

    # Stats command
    subparsers.add_parser("stats", help="Show ticket statistics")

    args = parser.parse_args()

    if args.command == "list":
        list_tickets(args.status)
    elif args.command == "show":
        show_ticket(args.id)
    elif args.command == "resolve":
        resolve_ticket(args.id, args.response)
    elif args.command == "skip":
        skip_ticket(args.id, args.reason)
    elif args.command == "escalate":
        escalate_ticket(args.id, args.reason)
    elif args.command == "stats":
        show_stats()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
