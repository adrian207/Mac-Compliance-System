"""
Email Delivery System

Author: Adrian Johnson <adrian207@gmail.com>

Delivers reports via email with attachments and templates.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from typing import List, Optional
from datetime import datetime


class EmailDelivery:
    """
    Email delivery system for reports.
    
    Sends reports with attachments and customizable templates.
    """
    
    def __init__(
        self,
        smtp_host: str = "localhost",
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: bool = True,
        from_address: str = "zerotrust@example.com"
    ):
        """
        Initialize email delivery system.
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username (if authentication required)
            smtp_password: SMTP password (if authentication required)
            use_tls: Whether to use TLS encryption
            from_address: From email address
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.use_tls = use_tls
        self.from_address = from_address
    
    def send_report(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Send report email.
        
        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            body: Plain text email body
            attachments: Optional list of file paths to attach
            html_body: Optional HTML email body
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_address
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Add attachments
            if attachments:
                for attachment_path in attachments:
                    self._attach_file(msg, attachment_path)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to send email: {e}")
            return False
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """
        Attach file to email message.
        
        Args:
            msg: Email message object
            file_path: Path to file to attach
        """
        path = Path(file_path)
        
        if not path.exists():
            print(f"[WARN] Attachment not found: {file_path}")
            return
        
        with open(file_path, 'rb') as f:
            attachment = MIMEApplication(f.read())
            attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=path.name
            )
            msg.attach(attachment)
    
    def render_template(
        self,
        template_name: str,
        variables: dict
    ) -> str:
        """
        Render email template with variables.
        
        Args:
            template_name: Template name
            variables: Dictionary of template variables
        
        Returns:
            Rendered template string
        """
        # [Inference] In production, this would use a template engine like Jinja2
        # For now, provide basic string substitution
        
        templates = {
            "executive_dashboard": """
Hello,

Your Executive Dashboard report is ready.

Period: {period}
Generated: {generated_at}

Summary:
- Total Devices: {total_devices}
- Critical Risk Devices: {critical_risk_devices}
- Health Score: {health_score}/100

Please find the detailed report attached.

Best regards,
ZeroTrust Platform
            """,
            
            "compliance_report": """
Hello,

Your Compliance Report is ready.

Framework: {framework}
Generated: {generated_at}

Summary:
- Total Devices Assessed: {total_devices}
- Compliance Rate: {compliance_rate}%
- Non-Compliant Devices: {non_compliant_devices}

Please review the attached detailed report.

Best regards,
ZeroTrust Platform
            """,
            
            "scheduled_report": """
Hello,

Your scheduled {report_type} report is attached.

Generated: {generated_at}

{summary}

Best regards,
ZeroTrust Platform
            """
        }
        
        template = templates.get(template_name, templates["scheduled_report"])
        
        try:
            return template.format(**variables)
        except KeyError as e:
            print(f"[WARN] Missing template variable: {e}")
            return template

