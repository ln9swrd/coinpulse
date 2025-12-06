"""
Email Service for CoinPulse

Handles email sending for authentication and notifications.
Development mode: Logs to console
Production mode: Sends via SMTP
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional


class EmailService:
    """Email service for sending verification and notification emails"""

    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@coinpulse.com')
        self.from_name = os.getenv('FROM_NAME', 'CoinPulse')

        # Check if in production mode
        self.is_production = os.getenv('ENVIRONMENT', 'development') == 'production'
        self.base_url = os.getenv('BASE_URL', 'http://localhost:8080')

    def send_email(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        """
        Send an email

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML content
            text_body: Plain text fallback (optional)

        Returns:
            bool: Success status
        """
        if not self.is_production:
            # Development mode: Log to console
            return self._log_email(to_email, subject, html_body, text_body)

        # Production mode: Send via SMTP
        return self._send_smtp(to_email, subject, html_body, text_body)

    def _log_email(self, to_email: str, subject: str, html_body: str, text_body: Optional[str]) -> bool:
        """Log email to console (development mode)"""
        print("\n" + "="*60)
        print("EMAIL (Development Mode)")
        print("="*60)
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print("-"*60)
        print(text_body or html_body)
        print("="*60 + "\n")
        return True

    def _send_smtp(self, to_email: str, subject: str, html_body: str, text_body: Optional[str]) -> bool:
        """Send email via SMTP (production mode)"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email

            # Add plain text and HTML parts
            if text_body:
                part1 = MIMEText(text_body, 'plain')
                msg.attach(part1)

            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            print(f"[EmailService] Email sent to {to_email}")
            return True

        except Exception as e:
            print(f"[EmailService] Failed to send email: {str(e)}")
            return False

    def send_verification_email(self, to_email: str, username: str, token: str) -> bool:
        """
        Send email verification message

        Args:
            to_email: User email address
            username: Username
            token: Verification token

        Returns:
            bool: Success status
        """
        verification_url = f"{self.base_url}/api/auth/verify-email?token={token}"

        subject = "Verify your CoinPulse account"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #4CAF50;
                           color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to CoinPulse!</h1>
                </div>
                <div class="content">
                    <h2>Hi {username},</h2>
                    <p>Thank you for registering with CoinPulse. To complete your registration,
                       please verify your email address by clicking the button below:</p>

                    <a href="{verification_url}" class="button">Verify Email Address</a>

                    <p>Or copy and paste this link into your browser:</p>
                    <p><code>{verification_url}</code></p>

                    <p>This verification link will expire in 24 hours.</p>

                    <p>If you didn't create an account with CoinPulse, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2025 CoinPulse. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
Welcome to CoinPulse!

Hi {username},

Thank you for registering with CoinPulse. To complete your registration,
please verify your email address by visiting this link:

{verification_url}

This verification link will expire in 24 hours.

If you didn't create an account with CoinPulse, please ignore this email.

---
CoinPulse Team
        """

        return self.send_email(to_email, subject, html_body, text_body)

    def send_password_reset_email(self, to_email: str, username: str, token: str) -> bool:
        """
        Send password reset message

        Args:
            to_email: User email address
            username: Username
            token: Reset token

        Returns:
            bool: Success status
        """
        reset_url = f"{self.base_url}/reset-password?token={token}"

        subject = "Reset your CoinPulse password"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #FF9800; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #FF9800;
                           color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #777; }}
                .warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 12px; margin: 12px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <h2>Hi {username},</h2>
                    <p>We received a request to reset your password for your CoinPulse account.</p>

                    <a href="{reset_url}" class="button">Reset Password</a>

                    <p>Or copy and paste this link into your browser:</p>
                    <p><code>{reset_url}</code></p>

                    <div class="warning">
                        <strong>Security Notice:</strong> This reset link will expire in 1 hour.
                    </div>

                    <p>If you didn't request a password reset, please ignore this email or contact support
                       if you have concerns about your account security.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2025 CoinPulse. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
Password Reset Request

Hi {username},

We received a request to reset your password for your CoinPulse account.

Click this link to reset your password:
{reset_url}

SECURITY NOTICE: This reset link will expire in 1 hour.

If you didn't request a password reset, please ignore this email or contact
support if you have concerns about your account security.

---
CoinPulse Team
        """

        return self.send_email(to_email, subject, html_body, text_body)


# Global instance
email_service = EmailService()
