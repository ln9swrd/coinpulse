# -*- coding: utf-8 -*-
"""
Email Notification Service
Sends email notifications for trading signals
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Email notification service using SMTP"""

    def __init__(self):
        """Initialize email service with SMTP credentials"""
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('SMTP_FROM_EMAIL', self.smtp_user)
        self.from_name = os.getenv('SMTP_FROM_NAME', 'CoinPulse')

        self.enabled = bool(self.smtp_user and self.smtp_password)

        if not self.enabled:
            logger.warning("[EmailService] SMTP credentials not configured.")
        else:
            logger.info(f"[EmailService] Initialized with SMTP: {self.smtp_host}")

    def send_signal_notification(self, recipient_email: str, signal_data: Dict) -> bool:
        """Send signal notification email"""
        if not self.enabled:
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"New Signal: {signal_data.get('market', 'Unknown')}"
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = recipient_email

            html = self._create_html(signal_data)
            msg.attach(MIMEText(html, 'html', 'utf-8'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"[EmailService] Sent to {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"[EmailService] Failed: {e}")
            return False

    def _create_html(self, data: Dict) -> str:
        """Create HTML email template"""
        market = data.get('market', 'Unknown')
        confidence = data.get('confidence', 0)
        entry = data.get('entry_price', 0)
        target = data.get('target_price', 0)
        stop = data.get('stop_loss', 0)
        reason = data.get('reason', '')
        
        return f"""
<!DOCTYPE html>
<html><body style="font-family:Arial;background:#f5f7fa;padding:20px;">
<div style="max-width:600px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;">
<div style="background:linear-gradient(135deg,#667eea,#764ba2);padding:30px;text-align:center;">
<h1 style="color:white;margin:0;">Trading Signal Alert</h1>
</div>
<div style="padding:30px;">
<h2 style="color:#1a202c;">{market}</h2>
<div style="background:#667eea;color:white;display:inline-block;padding:8px 16px;border-radius:20px;margin-bottom:20px;">
{confidence}% Confidence
</div>
<table style="width:100%;margin:20px 0;">
<tr>
<td style="background:#f8f9fa;padding:15px;border-radius:8px;">
<div style="color:#666;font-size:12px;">Entry Price</div>
<div style="color:#333;font-size:18px;font-weight:bold;">KRW {entry:,}</div>
</td>
<td style="width:20px;"></td>
<td style="background:#d1fae5;padding:15px;border-radius:8px;">
<div style="color:#666;font-size:12px;">Target Price</div>
<div style="color:#10b981;font-size:18px;font-weight:bold;">KRW {target:,}</div>
</td>
</tr>
<tr><td style="height:15px;"></td></tr>
<tr>
<td style="background:#fee2e2;padding:15px;border-radius:8px;">
<div style="color:#666;font-size:12px;">Stop Loss</div>
<div style="color:#ef4444;font-size:18px;font-weight:bold;">KRW {stop:,}</div>
</td>
</tr>
</table>
<div style="background:#f8f9fa;padding:20px;border-radius:8px;margin:20px 0;">
<strong>Reason:</strong> {reason}
</div>
<div style="text-align:center;margin:30px 0;">
<a href="https://coinpulse.sinsi.ai/my_signals.html" style="background:#10b981;color:white;text-decoration:none;padding:14px 32px;border-radius:8px;display:inline-block;">
View My Signals
</a>
</div>
</div>
<div style="background:#f8f9fa;padding:20px;text-align:center;color:#999;font-size:12px;">
Not investment advice. All risks are your own.
</div>
</div>
</body></html>
        """
