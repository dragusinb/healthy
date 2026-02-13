"""
Email service using AWS SES via SMTP.
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "email-smtp.eu-central-1.amazonaws.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASS")
        self.from_email = os.getenv("SMTP_FROM", "noreply@analize.online")
        self.app_url = os.getenv("APP_URL", "https://analize.online")

    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(self.smtp_user and self.smtp_pass)

    def send_email(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        """
        Send an email via AWS SES SMTP.

        Returns True if sent successfully, False otherwise.
        """
        if not self.is_configured():
            logger.warning("Email service not configured - SMTP credentials missing")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"Analize.online <{self.from_email}>"
            msg["To"] = to_email

            # Plain text fallback
            if text_body:
                msg.attach(MIMEText(text_body, "plain", "utf-8"))

            # HTML version
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.sendmail(self.from_email, to_email, msg.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_verification_email(self, to_email: str, token: str, language: str = "ro") -> bool:
        """Send email verification link."""
        verify_url = f"{self.app_url}/verify-email?token={token}"

        if language == "ro":
            subject = "Confirmă adresa de email - Analize.online"
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #0ea5e9, #06b6d4); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .button {{ display: inline-block; background: #0ea5e9; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                    .footer {{ text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin:0;">🏥 Analize.online</h1>
                    </div>
                    <div class="content">
                        <h2>Bine ai venit!</h2>
                        <p>Mulțumim că te-ai înregistrat pe Analize.online. Pentru a-ți activa contul, te rugăm să confirmi adresa de email.</p>
                        <p style="text-align: center;">
                            <a href="{verify_url}" class="button">Confirmă Email</a>
                        </p>
                        <p style="color: #64748b; font-size: 14px;">Dacă butonul nu funcționează, copiază și lipește acest link în browser:</p>
                        <p style="word-break: break-all; color: #0ea5e9; font-size: 12px;">{verify_url}</p>
                        <p style="color: #64748b; font-size: 14px;">Link-ul expiră în 24 de ore.</p>
                    </div>
                    <div class="footer">
                        <p>Acest email a fost trimis de Analize.online<br>Dacă nu ai creat un cont, poți ignora acest email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            text_body = f"""
Bine ai venit pe Analize.online!

Pentru a-ți activa contul, accesează acest link:
{verify_url}

Link-ul expiră în 24 de ore.

Dacă nu ai creat un cont, poți ignora acest email.
            """
        else:
            subject = "Confirm your email - Analize.online"
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #0ea5e9, #06b6d4); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .button {{ display: inline-block; background: #0ea5e9; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                    .footer {{ text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin:0;">🏥 Analize.online</h1>
                    </div>
                    <div class="content">
                        <h2>Welcome!</h2>
                        <p>Thank you for signing up on Analize.online. Please confirm your email address to activate your account.</p>
                        <p style="text-align: center;">
                            <a href="{verify_url}" class="button">Confirm Email</a>
                        </p>
                        <p style="color: #64748b; font-size: 14px;">If the button doesn't work, copy and paste this link in your browser:</p>
                        <p style="word-break: break-all; color: #0ea5e9; font-size: 12px;">{verify_url}</p>
                        <p style="color: #64748b; font-size: 14px;">This link expires in 24 hours.</p>
                    </div>
                    <div class="footer">
                        <p>This email was sent by Analize.online<br>If you didn't create an account, you can ignore this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            text_body = f"""
Welcome to Analize.online!

To activate your account, visit this link:
{verify_url}

This link expires in 24 hours.

If you didn't create an account, you can ignore this email.
            """

        return self.send_email(to_email, subject, html_body, text_body)

    def send_password_reset_email(self, to_email: str, token: str, language: str = "ro") -> bool:
        """Send password reset link."""
        reset_url = f"{self.app_url}/reset-password?token={token}"

        if language == "ro":
            subject = "Resetare parolă - Analize.online"
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #0ea5e9, #06b6d4); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .button {{ display: inline-block; background: #0ea5e9; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                    .footer {{ text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin:0;">🏥 Analize.online</h1>
                    </div>
                    <div class="content">
                        <h2>Resetare parolă</h2>
                        <p>Ai solicitat resetarea parolei pentru contul tău. Apasă pe butonul de mai jos pentru a seta o parolă nouă.</p>
                        <p style="text-align: center;">
                            <a href="{reset_url}" class="button">Resetează Parola</a>
                        </p>
                        <p style="color: #64748b; font-size: 14px;">Dacă butonul nu funcționează, copiază și lipește acest link în browser:</p>
                        <p style="word-break: break-all; color: #0ea5e9; font-size: 12px;">{reset_url}</p>
                        <p style="color: #64748b; font-size: 14px;">Link-ul expiră în 1 oră.</p>
                    </div>
                    <div class="footer">
                        <p>Dacă nu ai solicitat resetarea parolei, poți ignora acest email.<br>Parola ta rămâne neschimbată.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            text_body = f"""
Resetare parolă - Analize.online

Ai solicitat resetarea parolei. Accesează acest link pentru a seta o parolă nouă:
{reset_url}

Link-ul expiră în 1 oră.

Dacă nu ai solicitat resetarea parolei, poți ignora acest email.
            """
        else:
            subject = "Password Reset - Analize.online"
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #0ea5e9, #06b6d4); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .button {{ display: inline-block; background: #0ea5e9; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                    .footer {{ text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin:0;">🏥 Analize.online</h1>
                    </div>
                    <div class="content">
                        <h2>Password Reset</h2>
                        <p>You requested a password reset for your account. Click the button below to set a new password.</p>
                        <p style="text-align: center;">
                            <a href="{reset_url}" class="button">Reset Password</a>
                        </p>
                        <p style="color: #64748b; font-size: 14px;">If the button doesn't work, copy and paste this link in your browser:</p>
                        <p style="word-break: break-all; color: #0ea5e9; font-size: 12px;">{reset_url}</p>
                        <p style="color: #64748b; font-size: 14px;">This link expires in 1 hour.</p>
                    </div>
                    <div class="footer">
                        <p>If you didn't request a password reset, you can ignore this email.<br>Your password will remain unchanged.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            text_body = f"""
Password Reset - Analize.online

You requested a password reset. Visit this link to set a new password:
{reset_url}

This link expires in 1 hour.

If you didn't request a password reset, you can ignore this email.
            """

        return self.send_email(to_email, subject, html_body, text_body)

    def send_ticket_resolved_email(
        self,
        to_email: str,
        ticket_number: str,
        resolution_message: Optional[str] = None,
        language: str = "ro"
    ) -> bool:
        """Send notification when a support ticket is resolved."""
        tickets_url = f"{self.app_url}/support"

        if language == "ro":
            subject = f"Tichetul {ticket_number} a fost rezolvat - Analize.online"
            resolution_html = ""
            resolution_text = ""
            if resolution_message:
                resolution_html = f"""
                        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; color: #166534; font-weight: 500;">Mesaj de la echipa de suport:</p>
                            <p style="margin: 10px 0 0 0; color: #15803d; white-space: pre-wrap;">{resolution_message}</p>
                        </div>
                """
                resolution_text = f"\nMesaj de la echipa de suport:\n{resolution_message}\n"

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #22c55e, #16a34a); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .button {{ display: inline-block; background: #22c55e; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                    .footer {{ text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; }}
                    .ticket-badge {{ display: inline-block; background: #dcfce7; color: #166534; padding: 6px 12px; border-radius: 6px; font-family: monospace; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin:0;">✅ Tichet Rezolvat</h1>
                    </div>
                    <div class="content">
                        <p>Bună,</p>
                        <p>Tichetul tău <span class="ticket-badge">{ticket_number}</span> a fost rezolvat.</p>
                        {resolution_html}
                        <p>Mulțumim că ne-ai semnalat problema! Feedback-ul tău ne ajută să îmbunătățim aplicația.</p>
                        <p style="text-align: center;">
                            <a href="{tickets_url}" class="button">Vezi Tichetele</a>
                        </p>
                    </div>
                    <div class="footer">
                        <p>Acest email a fost trimis automat de Analize.online</p>
                    </div>
                </div>
            </body>
            </html>
            """
            text_body = f"""
Bună,

Tichetul tău {ticket_number} a fost rezolvat.
{resolution_text}
Mulțumim că ne-ai semnalat problema! Feedback-ul tău ne ajută să îmbunătățim aplicația.

Vezi tichetele tale: {tickets_url}
            """
        else:
            subject = f"Ticket {ticket_number} has been resolved - Analize.online"
            resolution_html = ""
            resolution_text = ""
            if resolution_message:
                resolution_html = f"""
                        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; color: #166534; font-weight: 500;">Message from support team:</p>
                            <p style="margin: 10px 0 0 0; color: #15803d; white-space: pre-wrap;">{resolution_message}</p>
                        </div>
                """
                resolution_text = f"\nMessage from support team:\n{resolution_message}\n"

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #22c55e, #16a34a); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .button {{ display: inline-block; background: #22c55e; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                    .footer {{ text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; }}
                    .ticket-badge {{ display: inline-block; background: #dcfce7; color: #166534; padding: 6px 12px; border-radius: 6px; font-family: monospace; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1 style="margin:0;">✅ Ticket Resolved</h1>
                    </div>
                    <div class="content">
                        <p>Hello,</p>
                        <p>Your ticket <span class="ticket-badge">{ticket_number}</span> has been resolved.</p>
                        {resolution_html}
                        <p>Thank you for reporting the issue! Your feedback helps us improve the application.</p>
                        <p style="text-align: center;">
                            <a href="{tickets_url}" class="button">View Tickets</a>
                        </p>
                    </div>
                    <div class="footer">
                        <p>This email was sent automatically by Analize.online</p>
                    </div>
                </div>
            </body>
            </html>
            """
            text_body = f"""
Hello,

Your ticket {ticket_number} has been resolved.
{resolution_text}
Thank you for reporting the issue! Your feedback helps us improve the application.

View your tickets: {tickets_url}
            """

        return self.send_email(to_email, subject, html_body, text_body)


# Singleton instance
_email_service = None

def get_email_service() -> EmailService:
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
