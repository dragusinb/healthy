"""
Notification service for sending email alerts to users.

Notification types:
- new_documents: New lab results available after sync
- abnormal_biomarker: Biomarker outside normal range detected
- analysis_complete: AI health analysis completed
- sync_failed: Provider sync failed
- reminder: Periodic health checkup reminder
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self._email_service = None

    @property
    def email_service(self):
        if self._email_service is None:
            try:
                from backend_v2.services.email_service import get_email_service
            except ImportError:
                from services.email_service import get_email_service
            self._email_service = get_email_service()
        return self._email_service

    def get_user_preferences(self, user_id: int):
        """Get or create notification preferences for user."""
        try:
            from backend_v2.models import NotificationPreference
        except ImportError:
            from models import NotificationPreference

        prefs = self.db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()

        if not prefs:
            # Create default preferences
            prefs = NotificationPreference(user_id=user_id)
            self.db.add(prefs)
            self.db.commit()
            self.db.refresh(prefs)

        return prefs

    def should_send_email(self, user_id: int, notification_type: str) -> bool:
        """Check if user wants email for this notification type."""
        prefs = self.get_user_preferences(user_id)

        type_to_pref = {
            "new_documents": prefs.email_new_documents,
            "abnormal_biomarker": prefs.email_abnormal_biomarkers,
            "analysis_complete": prefs.email_analysis_complete,
            "sync_failed": prefs.email_sync_failed,
            "reminder": prefs.email_reminders,
        }

        return type_to_pref.get(notification_type, True)

    def is_quiet_hours(self, user_id: int) -> bool:
        """Check if current time is in user's quiet hours."""
        prefs = self.get_user_preferences(user_id)

        if prefs.quiet_hours_start is None or prefs.quiet_hours_end is None:
            return False

        current_hour = datetime.now().hour

        if prefs.quiet_hours_start <= prefs.quiet_hours_end:
            # Normal range: e.g., 22 to 8
            return prefs.quiet_hours_start <= current_hour < prefs.quiet_hours_end
        else:
            # Overnight range: e.g., 22 to 8 (wraps around midnight)
            return current_hour >= prefs.quiet_hours_start or current_hour < prefs.quiet_hours_end

    def create_notification(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        send_email: bool = True
    ):
        """Create a notification and optionally send email."""
        try:
            from backend_v2.models import Notification, User
        except ImportError:
            from models import Notification, User

        # Create notification record
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            data=json.dumps(data) if data else None
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        # Check if we should send email
        if send_email and self.should_send_email(user_id, notification_type):
            prefs = self.get_user_preferences(user_id)

            # Check frequency preference
            if prefs.email_frequency == "immediate" and not self.is_quiet_hours(user_id):
                user = self.db.query(User).filter(User.id == user_id).first()
                if user:
                    self._send_notification_email(user, notification)

        return notification

    def _send_notification_email(self, user, notification):
        """Send email for a notification."""
        try:
            from backend_v2.models import Notification
        except ImportError:
            from models import Notification

        language = user.language or "ro"
        success = False

        if notification.notification_type == "new_documents":
            success = self._send_new_documents_email(user.email, notification, language)
        elif notification.notification_type == "abnormal_biomarker":
            success = self._send_abnormal_biomarker_email(user.email, notification, language)
        elif notification.notification_type == "analysis_complete":
            success = self._send_analysis_complete_email(user.email, notification, language)
        elif notification.notification_type == "sync_failed":
            success = self._send_sync_failed_email(user.email, notification, language)
        elif notification.notification_type == "reminder":
            success = self._send_reminder_email(user.email, notification, language)

        if success:
            notification.is_sent_email = True
            notification.sent_at = datetime.utcnow()
            self.db.commit()

        return success

    def _send_new_documents_email(self, to_email: str, notification, language: str) -> bool:
        """Send email about new documents."""
        data = json.loads(notification.data) if notification.data else {}
        doc_count = data.get("document_count", 1)
        provider = data.get("provider", "")
        biomarker_count = data.get("biomarker_count", 0)

        if language == "ro":
            subject = f"Rezultate noi disponibile - {provider}"
            html_body = self._email_template(
                title="Rezultate noi disponibile",
                content=f"""
                <p>Salut!</p>
                <p>Am descărcat <strong>{doc_count} document(e)</strong> noi de la <strong>{provider}</strong>.</p>
                {"<p>Am extras <strong>" + str(biomarker_count) + " biomarkeri</strong> din aceste documente.</p>" if biomarker_count else ""}
                <p>Intră pe platformă pentru a vedea rezultatele tale.</p>
                """,
                button_text="Vezi Rezultatele",
                button_url="https://analize.online/documents"
            )
        else:
            subject = f"New results available - {provider}"
            html_body = self._email_template(
                title="New Results Available",
                content=f"""
                <p>Hello!</p>
                <p>We downloaded <strong>{doc_count} new document(s)</strong> from <strong>{provider}</strong>.</p>
                {"<p>We extracted <strong>" + str(biomarker_count) + " biomarkers</strong> from these documents.</p>" if biomarker_count else ""}
                <p>Log in to view your results.</p>
                """,
                button_text="View Results",
                button_url="https://analize.online/documents"
            )

        return self.email_service.send_email(to_email, subject, html_body)

    def _send_abnormal_biomarker_email(self, to_email: str, notification, language: str) -> bool:
        """Send email about abnormal biomarker."""
        data = json.loads(notification.data) if notification.data else {}
        biomarker_name = data.get("biomarker_name", "")
        value = data.get("value", "")
        unit = data.get("unit", "")
        flag = data.get("flag", "")
        reference = data.get("reference_range", "")

        flag_color = "#dc2626" if flag == "HIGH" else "#f59e0b"  # Red for high, amber for low

        if language == "ro":
            flag_text = "RIDICAT" if flag == "HIGH" else "SCĂZUT"
            subject = f"Atenție: {biomarker_name} {flag_text}"
            html_body = self._email_template(
                title="Valoare anormală detectată",
                content=f"""
                <p>Am detectat o valoare în afara intervalului normal:</p>
                <div style="background: #fef3c7; border-left: 4px solid {flag_color}; padding: 15px; margin: 20px 0;">
                    <strong style="font-size: 18px;">{biomarker_name}</strong><br>
                    <span style="font-size: 24px; color: {flag_color}; font-weight: bold;">{value} {unit}</span>
                    <span style="background: {flag_color}; color: white; padding: 2px 8px; border-radius: 4px; margin-left: 10px;">{flag_text}</span><br>
                    <span style="color: #64748b;">Interval de referință: {reference}</span>
                </div>
                <p>Te recomandăm să consulți un medic pentru interpretarea acestui rezultat.</p>
                """,
                button_text="Vezi Detalii",
                button_url="https://analize.online/biomarkers"
            )
        else:
            subject = f"Attention: {biomarker_name} is {flag}"
            html_body = self._email_template(
                title="Abnormal Value Detected",
                content=f"""
                <p>We detected a value outside the normal range:</p>
                <div style="background: #fef3c7; border-left: 4px solid {flag_color}; padding: 15px; margin: 20px 0;">
                    <strong style="font-size: 18px;">{biomarker_name}</strong><br>
                    <span style="font-size: 24px; color: {flag_color}; font-weight: bold;">{value} {unit}</span>
                    <span style="background: {flag_color}; color: white; padding: 2px 8px; border-radius: 4px; margin-left: 10px;">{flag}</span><br>
                    <span style="color: #64748b;">Reference range: {reference}</span>
                </div>
                <p>We recommend consulting a doctor for interpretation of this result.</p>
                """,
                button_text="View Details",
                button_url="https://analize.online/biomarkers"
            )

        return self.email_service.send_email(to_email, subject, html_body)

    def _send_analysis_complete_email(self, to_email: str, notification, language: str) -> bool:
        """Send email when AI analysis is complete."""
        data = json.loads(notification.data) if notification.data else {}
        report_type = data.get("report_type", "general")
        risk_level = data.get("risk_level", "normal")

        risk_colors = {
            "normal": "#22c55e",
            "attention": "#f59e0b",
            "concern": "#f97316",
            "urgent": "#dc2626"
        }
        risk_color = risk_colors.get(risk_level, "#22c55e")

        if language == "ro":
            risk_labels = {
                "normal": "Normal",
                "attention": "Necesită atenție",
                "concern": "Îngrijorare",
                "urgent": "Urgent"
            }
            report_labels = {
                "general": "Generalist",
                "cardiology": "Cardiologie",
                "endocrinology": "Endocrinologie",
                "hematology": "Hematologie",
                "hepatology": "Hepatologie",
                "nephrology": "Nefrologie"
            }
            subject = f"Analiză AI completă - {report_labels.get(report_type, report_type)}"
            html_body = self._email_template(
                title="Analiză AI Completă",
                content=f"""
                <p>Analiza ta de sănătate a fost completată!</p>
                <div style="background: #f0fdf4; border-left: 4px solid {risk_color}; padding: 15px; margin: 20px 0;">
                    <strong>Tip raport:</strong> {report_labels.get(report_type, report_type)}<br>
                    <strong>Nivel de risc:</strong> <span style="color: {risk_color}; font-weight: bold;">{risk_labels.get(risk_level, risk_level)}</span>
                </div>
                <p>Intră pe platformă pentru a vedea raportul complet cu recomandări.</p>
                """,
                button_text="Vezi Raportul",
                button_url="https://analize.online/health"
            )
        else:
            risk_labels = {
                "normal": "Normal",
                "attention": "Needs attention",
                "concern": "Concerning",
                "urgent": "Urgent"
            }
            report_labels = {
                "general": "General",
                "cardiology": "Cardiology",
                "endocrinology": "Endocrinology",
                "hematology": "Hematology",
                "hepatology": "Hepatology",
                "nephrology": "Nephrology"
            }
            subject = f"AI Analysis Complete - {report_labels.get(report_type, report_type)}"
            html_body = self._email_template(
                title="AI Analysis Complete",
                content=f"""
                <p>Your health analysis has been completed!</p>
                <div style="background: #f0fdf4; border-left: 4px solid {risk_color}; padding: 15px; margin: 20px 0;">
                    <strong>Report type:</strong> {report_labels.get(report_type, report_type)}<br>
                    <strong>Risk level:</strong> <span style="color: {risk_color}; font-weight: bold;">{risk_labels.get(risk_level, risk_level)}</span>
                </div>
                <p>Log in to view the full report with recommendations.</p>
                """,
                button_text="View Report",
                button_url="https://analize.online/health"
            )

        return self.email_service.send_email(to_email, subject, html_body)

    def _send_sync_failed_email(self, to_email: str, notification, language: str) -> bool:
        """Send email when sync fails."""
        data = json.loads(notification.data) if notification.data else {}
        provider = data.get("provider", "")
        error_type = data.get("error_type", "unknown")

        error_messages = {
            "ro": {
                "wrong_password": "Parola sau utilizatorul sunt incorecte. Verifică datele de autentificare.",
                "captcha_failed": "Nu am reușit să trecem de CAPTCHA. Încearcă manual mai târziu.",
                "site_down": "Site-ul furnizorului nu este disponibil momentan.",
                "server_error": "Eroare de server. Echipa tehnică a fost notificată.",
                "session_expired": "Sesiunea a expirat. Trebuie să te reautentifici.",
                "timeout": "Operațiunea a durat prea mult. Vom reîncerca automat.",
                "unknown": "A apărut o eroare neașteptată. Vom investiga."
            },
            "en": {
                "wrong_password": "Password or username are incorrect. Please verify your credentials.",
                "captcha_failed": "We couldn't solve the CAPTCHA. Try manually later.",
                "site_down": "The provider's website is currently unavailable.",
                "server_error": "Server error. The technical team has been notified.",
                "session_expired": "Your session has expired. You need to re-authenticate.",
                "timeout": "The operation took too long. We'll retry automatically.",
                "unknown": "An unexpected error occurred. We'll investigate."
            }
        }

        error_msg = error_messages.get(language, error_messages["en"]).get(error_type, error_messages[language]["unknown"])

        if language == "ro":
            subject = f"Sincronizare eșuată - {provider}"
            html_body = self._email_template(
                title="Sincronizare Eșuată",
                content=f"""
                <p>Nu am putut sincroniza datele de la <strong>{provider}</strong>.</p>
                <div style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0;">
                    <strong>Motiv:</strong> {error_msg}
                </div>
                {"<p>Intră pe platformă pentru a actualiza datele de autentificare.</p>" if error_type == "wrong_password" else ""}
                """,
                button_text="Verifică Contul",
                button_url="https://analize.online/accounts"
            )
        else:
            subject = f"Sync Failed - {provider}"
            html_body = self._email_template(
                title="Sync Failed",
                content=f"""
                <p>We couldn't sync your data from <strong>{provider}</strong>.</p>
                <div style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 20px 0;">
                    <strong>Reason:</strong> {error_msg}
                </div>
                {"<p>Log in to update your credentials.</p>" if error_type == "wrong_password" else ""}
                """,
                button_text="Check Account",
                button_url="https://analize.online/accounts"
            )

        return self.email_service.send_email(to_email, subject, html_body)

    def _send_reminder_email(self, to_email: str, notification, language: str) -> bool:
        """Send periodic health checkup reminder."""
        data = json.loads(notification.data) if notification.data else {}
        days_since_last = data.get("days_since_last_test", 0)
        suggested_tests = data.get("suggested_tests", [])

        if language == "ro":
            subject = "Memento: Este timpul pentru analize"
            tests_html = ""
            if suggested_tests:
                tests_html = "<p><strong>Analize sugerate:</strong></p><ul>"
                for test in suggested_tests[:5]:
                    tests_html += f"<li>{test}</li>"
                tests_html += "</ul>"

            html_body = self._email_template(
                title="Memento Sănătate",
                content=f"""
                <p>Salut!</p>
                <p>Au trecut <strong>{days_since_last} de zile</strong> de la ultimele tale analize.</p>
                {tests_html}
                <p>Controalele regulate sunt importante pentru menținerea sănătății!</p>
                """,
                button_text="Vezi Istoricul",
                button_url="https://analize.online/biomarkers"
            )
        else:
            subject = "Reminder: Time for a checkup"
            tests_html = ""
            if suggested_tests:
                tests_html = "<p><strong>Suggested tests:</strong></p><ul>"
                for test in suggested_tests[:5]:
                    tests_html += f"<li>{test}</li>"
                tests_html += "</ul>"

            html_body = self._email_template(
                title="Health Reminder",
                content=f"""
                <p>Hello!</p>
                <p>It's been <strong>{days_since_last} days</strong> since your last tests.</p>
                {tests_html}
                <p>Regular checkups are important for maintaining your health!</p>
                """,
                button_text="View History",
                button_url="https://analize.online/biomarkers"
            )

        return self.email_service.send_email(to_email, subject, html_body)

    def _email_template(self, title: str, content: str, button_text: str, button_url: str) -> str:
        """Generate consistent email HTML template."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #0ea5e9, #06b6d4); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #0ea5e9; color: white !important; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }}
                .footer {{ text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin:0;">Analize.online</h1>
                </div>
                <div class="content">
                    <h2 style="color: #0f172a; margin-top: 0;">{title}</h2>
                    {content}
                    <p style="text-align: center;">
                        <a href="{button_url}" class="button">{button_text}</a>
                    </p>
                </div>
                <div class="footer">
                    <p>Acest email a fost trimis de Analize.online<br>
                    <a href="https://analize.online/settings" style="color: #0ea5e9;">Gestionează preferințele de notificare</a></p>
                </div>
            </div>
        </body>
        </html>
        """

    def process_pending_notifications(self):
        """Process notifications that haven't been emailed yet (for digest mode)."""
        try:
            from backend_v2.models import Notification, User
        except ImportError:
            from models import Notification, User

        # Find unsent notifications
        pending = self.db.query(Notification).filter(
            Notification.is_sent_email == False
        ).all()

        for notification in pending:
            user = self.db.query(User).filter(User.id == notification.user_id).first()
            if not user:
                continue

            prefs = self.get_user_preferences(user.id)

            # Skip if user doesn't want this type of notification
            if not self.should_send_email(user.id, notification.notification_type):
                notification.is_sent_email = True  # Mark as "sent" (skipped)
                continue

            # Skip if in quiet hours
            if self.is_quiet_hours(user.id):
                continue

            # For immediate, send right away
            if prefs.email_frequency == "immediate":
                self._send_notification_email(user, notification)

        self.db.commit()


def notify_new_documents(db: Session, user_id: int, provider: str, document_count: int, biomarker_count: int = 0):
    """Helper to notify user about new documents."""
    service = NotificationService(db)
    service.create_notification(
        user_id=user_id,
        notification_type="new_documents",
        title=f"Rezultate noi de la {provider}",
        message=f"{document_count} document(e) noi disponibile",
        data={
            "provider": provider,
            "document_count": document_count,
            "biomarker_count": biomarker_count
        }
    )


def notify_abnormal_biomarker(db: Session, user_id: int, biomarker_name: str, value: str, unit: str, flag: str, reference_range: str):
    """Helper to notify user about abnormal biomarker."""
    service = NotificationService(db)
    service.create_notification(
        user_id=user_id,
        notification_type="abnormal_biomarker",
        title=f"{biomarker_name} anormal",
        message=f"Valoare: {value} {unit} ({flag})",
        data={
            "biomarker_name": biomarker_name,
            "value": value,
            "unit": unit,
            "flag": flag,
            "reference_range": reference_range
        }
    )


def notify_analysis_complete(db: Session, user_id: int, report_type: str, risk_level: str):
    """Helper to notify user about completed AI analysis."""
    service = NotificationService(db)
    service.create_notification(
        user_id=user_id,
        notification_type="analysis_complete",
        title="Analiză AI completă",
        message=f"Raport {report_type} generat",
        data={
            "report_type": report_type,
            "risk_level": risk_level
        }
    )


def notify_sync_failed(db: Session, user_id: int, provider: str, error_type: str, error_message: str):
    """Helper to notify user about failed sync."""
    service = NotificationService(db)
    service.create_notification(
        user_id=user_id,
        notification_type="sync_failed",
        title=f"Sincronizare eșuată - {provider}",
        message=error_message,
        data={
            "provider": provider,
            "error_type": error_type,
            "error_message": error_message
        }
    )
