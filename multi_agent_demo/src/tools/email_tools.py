from langchain_core.tools import tool
import json
from datetime import datetime, timedelta
from typing import List, Dict

# Mock email database
MOCK_EMAILS = [
    {
        "id": "email_001",
        "from": "boss@company.com",
        "subject": "Quarterly Review Meeting",
        "body": "Please join us for the quarterly review meeting tomorrow at 2 PM.",
        "timestamp": "2025-09-02 10:30:00",
        "priority": "high",
        "read": False
    },
    {
        "id": "email_002", 
        "from": "client@business.com",
        "subject": "Project Proposal Feedback",
        "body": "We've reviewed your proposal and have some questions about the timeline.",
        "timestamp": "2025-09-01 14:15:00",
        "priority": "medium",
        "read": True
    },
    {
        "id": "email_003",
        "from": "newsletter@marketing.com",
        "subject": "Weekly Industry Update",
        "body": "Here are this week's top industry news and trends...",
        "timestamp": "2025-08-30 08:00:00",
        "priority": "low",
        "read": False
    }
]

SENT_EMAILS = []

@tool
def get_recent_emails(limit: int = 10, unread_only: bool = False) -> str:
    """
    Retrieve recent emails from the inbox.
    
    Args:
        limit: Maximum number of emails to return
        unread_only: If True, only return unread emails
        
    Returns:
        JSON string with email list
    """
    emails = MOCK_EMAILS.copy()
    
    if unread_only:
        emails = [e for e in emails if not e["read"]]
    
    # Sort by timestamp (most recent first)
    emails.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Limit results
    emails = emails[:limit]
    
    return json.dumps({
        "emails": emails,
        "count": len(emails),
        "unread_only": unread_only,
        "retrieved_at": datetime.now().isoformat()
    })

@tool
def get_email_by_id(email_id: str) -> str:
    """
    Get full details of a specific email by ID.
    
    Args:
        email_id: Unique identifier of the email
        
    Returns:
        JSON string with email details
    """
    email = next((e for e in MOCK_EMAILS if e["id"] == email_id), None)
    
    if not email:
        return json.dumps({"error": "Email not found", "email_id": email_id})
    
    # Mark as read when accessed
    email["read"] = True
    
    return json.dumps({
        "email": email,
        "retrieved_at": datetime.now().isoformat()
    })

@tool
def draft_email(to_address: str, subject: str, body: str, priority: str = "medium") -> str:
    """
    Draft a new email. Does not send automatically - requires user confirmation.
    
    Args:
        to_address: Recipient email address
        subject: Email subject line
        body: Email content
        priority: Priority level (low, medium, high)
        
    Returns:
        JSON string with draft details
    """
    draft_id = f"draft_{len(SENT_EMAILS) + 1:03d}"
    
    draft = {
        "draft_id": draft_id,
        "to": to_address,
        "subject": subject,
        "body": body,
        "priority": priority,
        "status": "draft",
        "created_at": datetime.now().isoformat()
    }
    
    return json.dumps({
        "draft": draft,
        "message": "Email drafted successfully. Use send_email to send.",
        "requires_confirmation": True
    })

@tool
def send_email(to_address: str, subject: str, body: str, draft_id: str = None) -> str:
    """
    Send an email. REQUIRES USER CONFIRMATION for external addresses.
    
    Args:
        to_address: Recipient email address
        subject: Email subject line  
        body: Email content
        draft_id: Optional draft ID if sending from draft
        
    Returns:
        JSON string with send confirmation
    """
    # Check if external email (security consideration)
    is_external = not to_address.endswith("@company.com")
    
    if is_external:
        return json.dumps({
            "status": "requires_confirmation",
            "message": "External email requires user confirmation",
            "to_address": to_address,
            "subject": subject,
            "is_external": True
        })
    
    # Simulate sending
    email_id = f"sent_{len(SENT_EMAILS) + 1:03d}"
    sent_email = {
        "id": email_id,
        "to": to_address,
        "subject": subject,
        "body": body,
        "sent_at": datetime.now().isoformat(),
        "status": "sent"
    }
    
    SENT_EMAILS.append(sent_email)
    
    return json.dumps({
        "status": "sent",
        "email_id": email_id,
        "sent_at": sent_email["sent_at"],
        "message": "Email sent successfully"
    })

# Email tools collection  
email_tools = [get_recent_emails, get_email_by_id, draft_email, send_email]