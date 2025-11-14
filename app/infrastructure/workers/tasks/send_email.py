"""Task: Send email."""

from app.infrastructure.workers.celery_app import celery_app


@celery_app.task(bind=True, name="send_email")
def send_email(
    self,
    to: str,
    subject: str,
    body: str,
    template: str = None
) -> dict:
    """
    Send email via AWS SES.
    
    MVP version: Just logs the email (no actual sending yet).
    Full implementation will use boto3 + SES.
    
    Args:
        to: Recipient email
        subject: Email subject
        body: Email body (plain text or HTML)
        template: Optional template name
    
    Returns:
        dict with status and message_id
    """
    try:
        # TODO: Actual email sending (AWS SES)
        # For MVP, just log
        print(f"📧 Email sent to {to}")
        print(f"   Subject: {subject}")
        print(f"   Body: {body[:100]}...")
        if template:
            print(f"   Template: {template}")
        
        return {
            "status": "success",
            "to": to,
            "message_id": f"mock-msg-{self.request.id}"
        }
    
    except Exception as e:
        print(f"❌ Email failed to {to}: {e}")
        raise
