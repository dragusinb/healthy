"""
Email campaign automation service.

Handles welcome sequences, re-engagement, and scheduled email campaigns.
Runs via the scheduler to send drip emails based on user registration date.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def get_email_template_style():
    """Common email CSS used by all campaign emails."""
    return """
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #0ea5e9, #06b6d4); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
    .content { background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }
    .button { display: inline-block; background: linear-gradient(135deg, #f59e0b, #f97316); color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }
    .button-secondary { display: inline-block; background: #0ea5e9; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }
    .footer { text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; padding: 20px; }
    .highlight { background: #fef3c7; border: 1px solid #fde68a; border-radius: 8px; padding: 15px; margin: 15px 0; }
    .feature { padding: 10px 0; border-bottom: 1px solid #e2e8f0; display: flex; }
    .feature:last-child { border-bottom: none; }
    .unsubscribe { color: #94a3b8; font-size: 11px; text-decoration: underline; }
    """


# =============================================================================
# Welcome Sequence (5 emails over 14 days)
# =============================================================================

WELCOME_SEQUENCE = [
    {"day": 0, "key": "welcome_day0"},
    {"day": 1, "key": "welcome_day1"},
    {"day": 3, "key": "welcome_day3"},
    {"day": 7, "key": "welcome_day7"},
    {"day": 14, "key": "welcome_day14"},
]


def get_welcome_email(day_key: str, user_name: str, language: str = "ro", has_provider: bool = False) -> dict:
    """Get welcome sequence email content by day key."""
    style = get_email_template_style()
    app_url = "https://analize.online"
    name = user_name or "utilizator"

    emails = {
        "welcome_day0": {
            "ro": {
                "subject": "Bine ai venit pe Analize.Online! Conectează-ți primul provider",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header"><h1 style="margin:0;">Analize.online</h1></div>
                    <div class="content">
                        <h2>Bine ai venit, {name}!</h2>
                        <p>Contul tău a fost creat cu succes. Ești la un pas de a-ți vedea toate analizele medicale într-un singur loc.</p>
                        <div class="highlight">
                            <strong>Următorul pas:</strong> Conectează contul tău de la Regina Maria, Synevo sau alt provider medical. Noi descărcăm automat toate analizele tale.
                        </div>
                        <p style="text-align:center;"><a href="{app_url}/linked-accounts" class="button">Conectează un provider</a></p>
                        <p>Ai nevoie de ajutor? Răspunde direct la acest email.</p>
                    </div>
                    <div class="footer"><p>Analize.online - Platforma de sănătate digitală</p></div>
                </div></body></html>"""
            },
            "en": {
                "subject": "Welcome to Analize.Online! Connect your first provider",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header"><h1 style="margin:0;">Analize.online</h1></div>
                    <div class="content">
                        <h2>Welcome, {name}!</h2>
                        <p>Your account has been created successfully. You're one step away from seeing all your medical tests in one place.</p>
                        <div class="highlight">
                            <strong>Next step:</strong> Connect your Regina Maria, Synevo or other medical provider account. We'll automatically download all your tests.
                        </div>
                        <p style="text-align:center;"><a href="{app_url}/linked-accounts" class="button">Connect a provider</a></p>
                        <p>Need help? Reply directly to this email.</p>
                    </div>
                    <div class="footer"><p>Analize.online - Digital Health Platform</p></div>
                </div></body></html>"""
            }
        },
        "welcome_day1": {
            "ro": {
                "subject": "Ce face inteligența noastră artificială cu analizele tale",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header"><h1 style="margin:0;">Analize.online</h1></div>
                    <div class="content">
                        <h2>Cum te ajută AI-ul nostru?</h2>
                        <p>Salut {name},</p>
                        <p>Știai că Analize.Online are <strong>8+ specialiști AI</strong> care îți analizează rezultatele?</p>
                        <div class="feature"><strong>Generalist</strong> - Evaluare completă a sănătății tale</div>
                        <div class="feature"><strong>Cardiolog AI</strong> - Colesterol, trigliceride, risc cardiovascular</div>
                        <div class="feature"><strong>Endocrinolog AI</strong> - Tiroidă, glicemie, hormoni</div>
                        <div class="feature"><strong>Nutriționist AI</strong> - Plan de mâncare personalizat cu rețete românești</div>
                        <div class="feature"><strong>Fitness AI</strong> - Program de exerciții adaptat nivelului tău</div>
                        <p>Fiecare specialist analizează rezultatele din perspectiva domeniului său și îți oferă recomandări practice.</p>
                        <p style="text-align:center;"><a href="{app_url}/health-reports" class="button-secondary">Vezi rapoartele AI</a></p>
                    </div>
                    <div class="footer"><p>Analize.online - Platforma de sănătate digitală</p></div>
                </div></body></html>"""
            },
            "en": {
                "subject": "What our AI does with your test results",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header"><h1 style="margin:0;">Analize.online</h1></div>
                    <div class="content">
                        <h2>How does our AI help you?</h2>
                        <p>Hi {name},</p>
                        <p>Did you know Analize.Online has <strong>8+ AI specialists</strong> analyzing your results?</p>
                        <div class="feature"><strong>Generalist</strong> - Complete health evaluation</div>
                        <div class="feature"><strong>AI Cardiologist</strong> - Cholesterol, triglycerides, cardiovascular risk</div>
                        <div class="feature"><strong>AI Endocrinologist</strong> - Thyroid, blood sugar, hormones</div>
                        <div class="feature"><strong>AI Nutritionist</strong> - Personalized meal plan</div>
                        <div class="feature"><strong>AI Fitness</strong> - Exercise program adapted to your level</div>
                        <p>Each specialist analyzes results from their domain perspective and gives practical recommendations.</p>
                        <p style="text-align:center;"><a href="{app_url}/health-reports" class="button-secondary">View AI reports</a></p>
                    </div>
                    <div class="footer"><p>Analize.online - Digital Health Platform</p></div>
                </div></body></html>"""
            }
        },
        "welcome_day3": {
            "ro": {
                "subject": f"Ai folosit analizele AI gratuite, {name}?",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header"><h1 style="margin:0;">Analize.online</h1></div>
                    <div class="content">
                        <h2>Planul tău Free include 2 analize AI/lună</h2>
                        <p>Salut {name},</p>
                        <p>Doar un reminder că planul tău gratuit include <strong>2 analize AI pe lună</strong>. Le-ai folosit?</p>
                        {"<div class='highlight'><strong>Nu ai conectat încă un provider medical.</strong> Conectează Regina Maria sau Synevo ca să-ți importăm automat analizele.</div><p style='text-align:center;'><a href='" + app_url + "/linked-accounts' class='button'>Conectează acum</a></p>" if not has_provider else "<p>Documentele tale sunt importate. Acum poți rula o analiză AI pentru a primi recomandări personalizate.</p><p style='text-align:center;'><a href='" + app_url + "/health-reports' class='button'>Rulează o analiză AI</a></p>"}
                    </div>
                    <div class="footer"><p>Analize.online - Platforma de sănătate digitală</p></div>
                </div></body></html>"""
            },
            "en": {
                "subject": f"Have you used your free AI analyses, {name}?",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header"><h1 style="margin:0;">Analize.online</h1></div>
                    <div class="content">
                        <h2>Your Free plan includes 2 AI analyses/month</h2>
                        <p>Hi {name},</p>
                        <p>Just a reminder that your free plan includes <strong>2 AI analyses per month</strong>. Have you used them?</p>
                        {"<div class='highlight'><strong>You haven't connected a medical provider yet.</strong> Connect Regina Maria or Synevo to auto-import your tests.</div><p style='text-align:center;'><a href='" + app_url + "/linked-accounts' class='button'>Connect now</a></p>" if not has_provider else "<p>Your documents are imported. Now you can run an AI analysis for personalized recommendations.</p><p style='text-align:center;'><a href='" + app_url + "/health-reports' class='button'>Run AI analysis</a></p>"}
                    </div>
                    <div class="footer"><p>Analize.online - Digital Health Platform</p></div>
                </div></body></html>"""
            }
        },
        "welcome_day7": {
            "ro": {
                "subject": "Dashboard-ul tău de sănătate te așteaptă",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header"><h1 style="margin:0;">Analize.online</h1></div>
                    <div class="content">
                        <h2>A trecut o săptămână...</h2>
                        <p>Salut {name},</p>
                        {"<p>Nu ai conectat încă un provider medical. <strong>Durează sub 2 minute</strong> și noi facem restul - descărcăm toate analizele tale automat.</p><p style='text-align:center;'><a href='" + app_url + "/linked-accounts' class='button'>Conectează în 2 minute</a></p>" if not has_provider else "<p>Totul arată bine! Continuă să-ți monitorizezi sănătatea cu Analize.Online.</p><p style='text-align:center;'><a href='" + app_url + "/' class='button-secondary'>Vezi dashboard-ul</a></p>"}
                        <div class="highlight">
                            <strong>Știai?</strong> Cu Premium (29 RON/lună) primești acces la toți specialiștii AI, planuri de nutriție personalizate și sincronizare automată cu toți providerii medicali.
                        </div>
                    </div>
                    <div class="footer"><p>Analize.online - Platforma de sănătate digitală</p></div>
                </div></body></html>"""
            },
            "en": {
                "subject": "Your health dashboard is waiting",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header"><h1 style="margin:0;">Analize.online</h1></div>
                    <div class="content">
                        <h2>It's been a week...</h2>
                        <p>Hi {name},</p>
                        {"<p>You haven't connected a medical provider yet. <strong>It takes under 2 minutes</strong> and we do the rest - downloading all your tests automatically.</p><p style='text-align:center;'><a href='" + app_url + "/linked-accounts' class='button'>Connect in 2 minutes</a></p>" if not has_provider else "<p>Everything looks good! Keep monitoring your health with Analize.Online.</p><p style='text-align:center;'><a href='" + app_url + "/' class='button-secondary'>View dashboard</a></p>"}
                        <div class="highlight">
                            <strong>Did you know?</strong> With Premium (29 RON/month) you get access to all AI specialists, personalized nutrition plans, and automatic sync with all medical providers.
                        </div>
                    </div>
                    <div class="footer"><p>Analize.online - Digital Health Platform</p></div>
                </div></body></html>"""
            }
        },
        "welcome_day14": {
            "ro": {
                "subject": "Upgrade la Premium - vezi ce pierzi",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header"><h1 style="margin:0;">Analize.online</h1></div>
                    <div class="content">
                        <h2>Ce pierzi fără Premium?</h2>
                        <p>Salut {name},</p>
                        <p>Cu planul gratuit ai acces la funcțiile de bază. Iată ce deblochezi cu <strong>Premium (29 RON/lună)</strong>:</p>
                        <div class="feature">8+ specialiști AI - Cardiolog, Endocrinolog, Nutriționist, Fitness</div>
                        <div class="feature">30 analize AI pe lună (vs 2 în Free)</div>
                        <div class="feature">Planuri de nutriție cu rețete românești</div>
                        <div class="feature">Program de exerciții personalizat</div>
                        <div class="feature">Export PDF pentru medici</div>
                        <div class="feature">Provideri medicali nelimitați</div>
                        <div class="feature">500 documente (vs 20 în Free)</div>
                        <div class="highlight">
                            <strong>Ofertă specială:</strong> Plătește anual la 199 RON/an și economisești 43% (doar 16,58 RON/lună).
                        </div>
                        <p style="text-align:center;"><a href="{app_url}/billing" class="button">Upgrade la Premium</a></p>
                    </div>
                    <div class="footer"><p>Analize.online - Platforma de sănătate digitală</p></div>
                </div></body></html>"""
            },
            "en": {
                "subject": "Upgrade to Premium - see what you're missing",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header"><h1 style="margin:0;">Analize.online</h1></div>
                    <div class="content">
                        <h2>What are you missing without Premium?</h2>
                        <p>Hi {name},</p>
                        <p>With the free plan you have basic access. Here's what you unlock with <strong>Premium (29 RON/month)</strong>:</p>
                        <div class="feature">8+ AI specialists - Cardiologist, Endocrinologist, Nutritionist, Fitness</div>
                        <div class="feature">30 AI analyses per month (vs 2 in Free)</div>
                        <div class="feature">Personalized nutrition plans</div>
                        <div class="feature">Custom exercise program</div>
                        <div class="feature">PDF export for doctors</div>
                        <div class="feature">Unlimited medical providers</div>
                        <div class="feature">500 documents (vs 20 in Free)</div>
                        <div class="highlight">
                            <strong>Special offer:</strong> Pay yearly at 199 RON/year and save 43% (only 16.58 RON/month).
                        </div>
                        <p style="text-align:center;"><a href="{app_url}/billing" class="button">Upgrade to Premium</a></p>
                    </div>
                    <div class="footer"><p>Analize.online - Digital Health Platform</p></div>
                </div></body></html>"""
            }
        },
    }

    content = emails.get(day_key, {}).get(language, emails.get(day_key, {}).get("ro", {}))
    return content


def run_welcome_email_campaigns():
    """Check for users who should receive welcome sequence emails.

    Called by the scheduler every hour.
    """
    try:
        from backend_v2.database import SessionLocal
        from backend_v2.models import User, Notification, LinkedAccount
        from backend_v2.services.email_service import get_email_service
    except ImportError:
        from database import SessionLocal
        from models import User, Notification, LinkedAccount
        from services.email_service import get_email_service

    email_service = get_email_service()
    if not email_service.is_configured():
        return

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        for step in WELCOME_SEQUENCE:
            day = step["day"]
            key = step["key"]

            # Calculate the target registration window
            # Users who registered 'day' days ago (within a 1-hour window)
            target_time = now - timedelta(days=day)
            window_start = target_time - timedelta(hours=1)
            window_end = target_time

            # Find users who registered in this window
            users = db.query(User).filter(
                User.created_at >= window_start,
                User.created_at < window_end,
                User.is_active == True,
                User.email_verified == True  # Only verified users
            ).all()

            for user in users:
                # Check if we already sent this email (using notification tracking)
                already_sent = db.query(Notification).filter(
                    Notification.user_id == user.id,
                    Notification.notification_type == f"campaign_{key}"
                ).first()

                if already_sent:
                    continue

                # Check if user has a provider connected
                has_provider = db.query(LinkedAccount).filter(
                    LinkedAccount.user_id == user.id
                ).count() > 0

                # Skip day 7/14 "connect provider" nudge if they already have one
                language = user.language or "ro"
                user_name = user.full_name or user.email.split("@")[0]

                content = get_welcome_email(key, user_name, language, has_provider)
                if not content:
                    continue

                # Send the email
                sent = email_service.send_email(user.email, content["subject"], content["html"])

                # Track that we sent it
                notification = Notification(
                    user_id=user.id,
                    notification_type=f"campaign_{key}",
                    title=content["subject"],
                    message=f"Welcome email day {day}",
                    is_sent_email=sent,
                    sent_at=now if sent else None
                )
                db.add(notification)

            db.commit()

    except Exception as e:
        logger.error(f"Error in welcome email campaigns: {e}")
    finally:
        db.close()


def run_monthly_health_digest():
    """Send monthly health digest emails.

    Called by scheduler on the 1st of each month.
    Summarizes: new documents synced, biomarker changes, alerts.
    """
    try:
        from backend_v2.database import SessionLocal
        from backend_v2.models import User, Document, TestResult, Notification, NotificationPreference
        from backend_v2.services.email_service import get_email_service
    except ImportError:
        from database import SessionLocal
        from models import User, Document, TestResult, Notification, NotificationPreference
        from services.email_service import get_email_service

    email_service = get_email_service()
    if not email_service.is_configured():
        return

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        month_ago = now - timedelta(days=30)
        style = get_email_template_style()
        app_url = "https://analize.online"

        # Get all active users with email reminders enabled
        users = db.query(User).filter(
            User.is_active == True,
            User.email_verified == True
        ).all()

        for user in users:
            # Check notification preferences
            prefs = db.query(NotificationPreference).filter(
                NotificationPreference.user_id == user.id
            ).first()
            if prefs and not prefs.email_reminders:
                continue

            # Already sent this month?
            already_sent = db.query(Notification).filter(
                Notification.user_id == user.id,
                Notification.notification_type == "monthly_digest",
                Notification.created_at >= now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            ).first()
            if already_sent:
                continue

            # Gather stats for this user
            new_docs = db.query(Document).filter(
                Document.user_id == user.id,
                Document.upload_date >= month_ago
            ).count()

            abnormal_count = db.query(TestResult).join(Document).filter(
                Document.user_id == user.id,
                Document.upload_date >= month_ago,
                TestResult.flags.in_(["HIGH", "LOW"])
            ).count()

            total_biomarkers = db.query(TestResult).join(Document).filter(
                Document.user_id == user.id,
                Document.upload_date >= month_ago
            ).count()

            # Skip if no activity
            if new_docs == 0 and total_biomarkers == 0:
                continue

            language = user.language or "ro"
            name = user.full_name or user.email.split("@")[0]

            if language == "ro":
                subject = f"Rezumatul tău de sănătate - {now.strftime('%B %Y')}"
                html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header"><h1 style="margin:0;">Rezumat Lunar</h1><p style="margin:5px 0 0 0; opacity:0.9;">Analize.online</p></div>
                    <div class="content">
                        <h2>Salut {name},</h2>
                        <p>Iată rezumatul sănătății tale din ultima lună:</p>
                        <table style="width:100%; border-collapse:collapse; margin: 15px 0;">
                            <tr style="background:#f0f9ff;"><td style="padding:12px; border:1px solid #e2e8f0;"><strong>Documente noi</strong></td><td style="padding:12px; border:1px solid #e2e8f0; text-align:center;"><strong>{new_docs}</strong></td></tr>
                            <tr><td style="padding:12px; border:1px solid #e2e8f0;"><strong>Biomarkeri analizați</strong></td><td style="padding:12px; border:1px solid #e2e8f0; text-align:center;"><strong>{total_biomarkers}</strong></td></tr>
                            <tr style="background:{('#fef2f2' if abnormal_count > 0 else '#f0fdf4')};"><td style="padding:12px; border:1px solid #e2e8f0;"><strong>Valori în afara intervalului</strong></td><td style="padding:12px; border:1px solid #e2e8f0; text-align:center; color:{('#dc2626' if abnormal_count > 0 else '#16a34a')};"><strong>{abnormal_count}</strong></td></tr>
                        </table>
                        {f'<div class="highlight"><strong>Atenție:</strong> Ai {abnormal_count} biomarkeri în afara intervalului normal. Consultă rapoartele AI pentru recomandări.</div>' if abnormal_count > 0 else ''}
                        <p style="text-align:center;"><a href="{app_url}/" class="button-secondary">Vezi Dashboard-ul</a></p>
                    </div>
                    <div class="footer"><p>Analize.online - Platforma de sănătate digitală</p></div>
                </div></body></html>"""
            else:
                subject = f"Your health summary - {now.strftime('%B %Y')}"
                html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header"><h1 style="margin:0;">Monthly Summary</h1><p style="margin:5px 0 0 0; opacity:0.9;">Analize.online</p></div>
                    <div class="content">
                        <h2>Hi {name},</h2>
                        <p>Here's your health summary for the past month:</p>
                        <table style="width:100%; border-collapse:collapse; margin: 15px 0;">
                            <tr style="background:#f0f9ff;"><td style="padding:12px; border:1px solid #e2e8f0;"><strong>New documents</strong></td><td style="padding:12px; border:1px solid #e2e8f0; text-align:center;"><strong>{new_docs}</strong></td></tr>
                            <tr><td style="padding:12px; border:1px solid #e2e8f0;"><strong>Biomarkers analyzed</strong></td><td style="padding:12px; border:1px solid #e2e8f0; text-align:center;"><strong>{total_biomarkers}</strong></td></tr>
                            <tr style="background:{('#fef2f2' if abnormal_count > 0 else '#f0fdf4')};"><td style="padding:12px; border:1px solid #e2e8f0;"><strong>Out of range values</strong></td><td style="padding:12px; border:1px solid #e2e8f0; text-align:center; color:{('#dc2626' if abnormal_count > 0 else '#16a34a')};"><strong>{abnormal_count}</strong></td></tr>
                        </table>
                        {f'<div class="highlight"><strong>Attention:</strong> You have {abnormal_count} biomarkers out of normal range. Check AI reports for recommendations.</div>' if abnormal_count > 0 else ''}
                        <p style="text-align:center;"><a href="{app_url}/" class="button-secondary">View Dashboard</a></p>
                    </div>
                    <div class="footer"><p>Analize.online - Digital Health Platform</p></div>
                </div></body></html>"""

            sent = email_service.send_email(user.email, subject, html)

            notification = Notification(
                user_id=user.id,
                notification_type="monthly_digest",
                title=subject,
                message=f"Monthly digest: {new_docs} docs, {abnormal_count} alerts",
                is_sent_email=sent,
                sent_at=now if sent else None
            )
            db.add(notification)

        db.commit()

    except Exception as e:
        logger.error(f"Error in monthly health digest: {e}")
    finally:
        db.close()
