"""
Email campaign automation service.

Handles trial conversion sequences, re-engagement, and scheduled email campaigns.
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
    .header-trial { background: linear-gradient(135deg, #f59e0b, #f97316); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
    .content { background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }
    .button { display: inline-block; background: linear-gradient(135deg, #f59e0b, #f97316); color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }
    .button-secondary { display: inline-block; background: #0ea5e9; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }
    .button-urgent { display: inline-block; background: linear-gradient(135deg, #dc2626, #ef4444); color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; }
    .footer { text-align: center; color: #64748b; font-size: 12px; margin-top: 20px; padding: 20px; }
    .highlight { background: #fef3c7; border: 1px solid #fde68a; border-radius: 8px; padding: 15px; margin: 15px 0; }
    .highlight-red { background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 15px; margin: 15px 0; }
    .feature { padding: 10px 0; border-bottom: 1px solid #e2e8f0; }
    .feature:last-child { border-bottom: none; }
    .badge { display: inline-block; background: #f59e0b; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; }
    .unsubscribe { color: #94a3b8; font-size: 11px; text-decoration: underline; }
    """


# =============================================================================
# Trial Conversion Sequence (7 emails over 30 days)
# =============================================================================

TRIAL_SEQUENCE = [
    {"day": 0, "key": "trial_day0"},
    {"day": 1, "key": "trial_day1"},
    {"day": 7, "key": "trial_week1"},
    {"day": 14, "key": "trial_week2"},
    {"day": 21, "key": "trial_week3"},
    {"day": 27, "key": "trial_day27"},
    {"day": 30, "key": "trial_day30"},
]


def get_trial_email(day_key: str, user_name: str, language: str = "ro", has_provider: bool = False) -> dict:
    """Get trial sequence email content by day key."""
    style = get_email_template_style()
    app_url = "https://analize.online"
    name = user_name or "utilizator"
    footer_ro = '<div class="footer"><p>Analize.online - Platforma de sănătate digitală</p></div>'
    footer_en = '<div class="footer"><p>Analize.online - Digital Health Platform</p></div>'

    emails = {
        "trial_day0": {
            "ro": {
                "subject": "Bine ai venit! Ai 30 de zile de Premium gratuit",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header-trial">
                        <span class="badge">PREMIUM TRIAL</span>
                        <h1 style="margin:10px 0 0 0;">Analize.online</h1>
                    </div>
                    <div class="content">
                        <h2>Bine ai venit, {name}!</h2>
                        <p>Contul tău a fost creat cu succes și ai primit <strong>30 de zile de acces Premium gratuit</strong>!</p>
                        <div class="highlight">
                            <strong>Ce ai inclus în trial:</strong>
                            <ul style="margin: 10px 0;">
                                <li>Provideri medicali nelimitați (Regina Maria, Synevo, etc.)</li>
                                <li>30 de analize AI pe lună</li>
                                <li>8+ specialiști AI (Cardiolog, Nutriționist, Fitness, etc.)</li>
                                <li>Plan de nutriție personalizat cu rețete românești</li>
                                <li>Program de exerciții adaptat sănătății tale</li>
                                <li>Export PDF și partajare cu medicii</li>
                            </ul>
                        </div>
                        <p><strong>Următorul pas:</strong> Conectează contul tău de la Regina Maria sau Synevo. Noi descărcăm automat toate analizele tale.</p>
                        <p style="text-align:center;"><a href="{app_url}/linked-accounts" class="button">Conectează un provider</a></p>
                        <p>Ai nevoie de ajutor? Răspunde direct la acest email.</p>
                    </div>
                    {footer_ro}
                </div></body></html>"""
            },
            "en": {
                "subject": "Welcome! You have 30 days of free Premium",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header-trial">
                        <span class="badge">PREMIUM TRIAL</span>
                        <h1 style="margin:10px 0 0 0;">Analize.online</h1>
                    </div>
                    <div class="content">
                        <h2>Welcome, {name}!</h2>
                        <p>Your account is ready and you have <strong>30 days of free Premium access</strong>!</p>
                        <div class="highlight">
                            <strong>What's included in your trial:</strong>
                            <ul style="margin: 10px 0;">
                                <li>Unlimited medical providers (Regina Maria, Synevo, etc.)</li>
                                <li>30 AI analyses per month</li>
                                <li>8+ AI specialists (Cardiologist, Nutritionist, Fitness, etc.)</li>
                                <li>Personalized nutrition plan with local recipes</li>
                                <li>Exercise program adapted to your health</li>
                                <li>PDF export and sharing with doctors</li>
                            </ul>
                        </div>
                        <p><strong>Next step:</strong> Connect your Regina Maria or Synevo account. We'll automatically download all your tests.</p>
                        <p style="text-align:center;"><a href="{app_url}/linked-accounts" class="button">Connect a provider</a></p>
                        <p>Need help? Reply directly to this email.</p>
                    </div>
                    {footer_en}
                </div></body></html>"""
            }
        },
        "trial_day1": {
            "ro": {
                "subject": "Ai 8+ specialiști AI la dispoziție — încearcă-i acum",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header"><h1 style="margin:0;">Analize.online</h1></div>
                    <div class="content">
                        <h2>Specialiștii tăi AI te așteaptă</h2>
                        <p>Salut {name},</p>
                        <p>Cu trialul tău Premium, ai acces la <strong>toți specialiștii AI</strong>:</p>
                        <div class="feature"><strong>🏥 Generalist</strong> — Evaluare completă a sănătății tale</div>
                        <div class="feature"><strong>❤️ Cardiolog AI</strong> — Colesterol, trigliceride, risc cardiovascular</div>
                        <div class="feature"><strong>🧬 Endocrinolog AI</strong> — Tiroidă, glicemie, hormoni</div>
                        <div class="feature"><strong>🩸 Hematolog AI</strong> — Hemoglobină, anemie, coagulare</div>
                        <div class="feature"><strong>🥗 Nutriționist AI</strong> — Plan alimentar personalizat cu rețete românești</div>
                        <div class="feature"><strong>🏋️ Fitness AI</strong> — Program de exerciții adaptat nivelului tău</div>
                        {"<div class='highlight'><strong>Nu ai conectat încă un provider.</strong> Conectează-l ca să-ți rulezi prima analiză AI!</div><p style='text-align:center;'><a href='" + app_url + "/linked-accounts' class='button'>Conectează acum</a></p>" if not has_provider else "<p>Documentele tale sunt importate. Rulează o analiză AI pentru recomandări personalizate!</p><p style='text-align:center;'><a href='" + app_url + "/health-reports' class='button'>Rulează o analiză AI</a></p>"}
                    </div>
                    {footer_ro}
                </div></body></html>"""
            },
            "en": {
                "subject": "You have 8+ AI specialists — try them now",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header"><h1 style="margin:0;">Analize.online</h1></div>
                    <div class="content">
                        <h2>Your AI specialists are ready</h2>
                        <p>Hi {name},</p>
                        <p>With your Premium trial, you have access to <strong>all AI specialists</strong>:</p>
                        <div class="feature"><strong>🏥 Generalist</strong> — Complete health evaluation</div>
                        <div class="feature"><strong>❤️ AI Cardiologist</strong> — Cholesterol, triglycerides, cardiovascular risk</div>
                        <div class="feature"><strong>🧬 AI Endocrinologist</strong> — Thyroid, blood sugar, hormones</div>
                        <div class="feature"><strong>🩸 AI Hematologist</strong> — Hemoglobin, anemia, coagulation</div>
                        <div class="feature"><strong>🥗 AI Nutritionist</strong> — Personalized meal plan with local recipes</div>
                        <div class="feature"><strong>🏋️ AI Fitness</strong> — Exercise program adapted to your level</div>
                        {"<div class='highlight'><strong>You haven't connected a provider yet.</strong> Connect one to run your first AI analysis!</div><p style='text-align:center;'><a href='" + app_url + "/linked-accounts' class='button'>Connect now</a></p>" if not has_provider else "<p>Your documents are imported. Run an AI analysis for personalized recommendations!</p><p style='text-align:center;'><a href='" + app_url + "/health-reports' class='button'>Run AI analysis</a></p>"}
                    </div>
                    {footer_en}
                </div></body></html>"""
            }
        },
        "trial_week1": {
            "ro": {
                "subject": f"{name}, nutriționistul tău AI ți-a pregătit un plan alimentar",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header-trial">
                        <span class="badge">SĂPTĂMÂNA 1</span>
                        <h1 style="margin:10px 0 0 0;">Nutriția ta personalizată</h1>
                    </div>
                    <div class="content">
                        <h2>Planul tău alimentar te așteaptă!</h2>
                        <p>Salut {name},</p>
                        <p>Ai trecut prima săptămână din trialul Premium! Știai că <strong>Nutriționistul tău AI</strong> poate crea un plan alimentar complet bazat pe biomarkerii tăi?</p>
                        <div class="highlight">
                            <strong>Ce primești:</strong>
                            <ul style="margin: 10px 0;">
                                <li>Plan de mâncare pentru 7 zile</li>
                                <li>Rețete românești cu porții exacte</li>
                                <li>Lista de cumpărături</li>
                                <li>Recomandări bazate pe analizele tale de sânge</li>
                                <li>Ajustări pentru preferințele tale alimentare</li>
                            </ul>
                        </div>
                        <p>De exemplu, dacă ai colesterolul crescut, planul va include alimente care scad LDL-ul. Dacă ai fierul scăzut, vei primi rețete bogate în fier.</p>
                        <p style="text-align:center;"><a href="{app_url}/lifestyle" class="button">Vezi planul meu de nutriție</a></p>
                        <p style="color: #64748b; font-size: 13px;">Funcționalitatea de nutriție este inclusă în trialul tău Premium. Mai ai 23 de zile de acces complet.</p>
                    </div>
                    {footer_ro}
                </div></body></html>"""
            },
            "en": {
                "subject": f"{name}, your AI nutritionist prepared a meal plan for you",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header-trial">
                        <span class="badge">WEEK 1</span>
                        <h1 style="margin:10px 0 0 0;">Your Personalized Nutrition</h1>
                    </div>
                    <div class="content">
                        <h2>Your meal plan is waiting!</h2>
                        <p>Hi {name},</p>
                        <p>You've completed your first week on Premium trial! Did you know your <strong>AI Nutritionist</strong> can create a complete meal plan based on your biomarkers?</p>
                        <div class="highlight">
                            <strong>What you get:</strong>
                            <ul style="margin: 10px 0;">
                                <li>7-day meal plan</li>
                                <li>Local recipes with exact portions</li>
                                <li>Shopping list</li>
                                <li>Recommendations based on your blood tests</li>
                                <li>Adjustments for your food preferences</li>
                            </ul>
                        </div>
                        <p>For example, if your cholesterol is high, the plan will include LDL-lowering foods. If your iron is low, you'll get iron-rich recipes.</p>
                        <p style="text-align:center;"><a href="{app_url}/lifestyle" class="button">See my nutrition plan</a></p>
                        <p style="color: #64748b; font-size: 13px;">Nutrition features are included in your Premium trial. You have 23 days of full access remaining.</p>
                    </div>
                    {footer_en}
                </div></body></html>"""
            }
        },
        "trial_week2": {
            "ro": {
                "subject": f"{name}, programul tău de exerciții personalizat este gata",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header-trial">
                        <span class="badge">SĂPTĂMÂNA 2</span>
                        <h1 style="margin:10px 0 0 0;">Fitness adaptat sănătății tale</h1>
                    </div>
                    <div class="content">
                        <h2>Antrenamentul tău personalizat</h2>
                        <p>Salut {name},</p>
                        <p>Pe lângă nutriție, <strong>Fitness AI</strong> îți creează un program de exerciții adaptat 100% stării tale de sănătate.</p>
                        <div class="highlight">
                            <strong>Ce primești:</strong>
                            <ul style="margin: 10px 0;">
                                <li>Program de exerciții pentru 7 zile</li>
                                <li>Seturi, repetări și durate exacte</li>
                                <li>Adaptat nivelului tău (începător → avansat)</li>
                                <li>Exerciții ajustate pe baza analizelor medicale</li>
                                <li>Cardio + forță + flexibilitate</li>
                            </ul>
                        </div>
                        <p>Dacă ai probleme articulare sau cardiovasculare, programul ține cont de limitările tale. Sănătatea pe primul loc!</p>
                        <p style="text-align:center;"><a href="{app_url}/lifestyle" class="button">Vezi programul meu de exerciții</a></p>
                        <p style="color: #64748b; font-size: 13px;">Mai ai 16 zile din trialul Premium. Profită la maximum!</p>
                    </div>
                    {footer_ro}
                </div></body></html>"""
            },
            "en": {
                "subject": f"{name}, your personalized exercise program is ready",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header-trial">
                        <span class="badge">WEEK 2</span>
                        <h1 style="margin:10px 0 0 0;">Fitness Adapted to Your Health</h1>
                    </div>
                    <div class="content">
                        <h2>Your personalized workout</h2>
                        <p>Hi {name},</p>
                        <p>Beyond nutrition, <strong>Fitness AI</strong> creates an exercise program 100% adapted to your health status.</p>
                        <div class="highlight">
                            <strong>What you get:</strong>
                            <ul style="margin: 10px 0;">
                                <li>7-day exercise program</li>
                                <li>Exact sets, reps, and durations</li>
                                <li>Adapted to your level (beginner → advanced)</li>
                                <li>Exercises adjusted based on your medical tests</li>
                                <li>Cardio + strength + flexibility</li>
                            </ul>
                        </div>
                        <p>If you have joint or cardiovascular issues, the program respects your limitations. Health first!</p>
                        <p style="text-align:center;"><a href="{app_url}/lifestyle" class="button">See my exercise program</a></p>
                        <p style="color: #64748b; font-size: 13px;">You have 16 days left on your Premium trial. Make the most of it!</p>
                    </div>
                    {footer_en}
                </div></body></html>"""
            }
        },
        "trial_week3": {
            "ro": {
                "subject": f"{name}, mai ai 7 zile de Premium — iată ce vei pierde",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header-trial">
                        <span class="badge">7 ZILE RĂMASE</span>
                        <h1 style="margin:10px 0 0 0;">Trialul tău se apropie de final</h1>
                    </div>
                    <div class="content">
                        <h2>Ce vei pierde în 7 zile?</h2>
                        <p>Salut {name},</p>
                        <p>Trialul tău Premium expiră în 7 zile. După aceea, vei trece la planul Free care include doar:</p>
                        <div class="highlight-red">
                            <strong>Planul Free:</strong>
                            <ul style="margin: 10px 0;">
                                <li>❌ Doar 1 provider medical (vs. nelimitat acum)</li>
                                <li>❌ Doar 20 documente (vs. 500 acum)</li>
                                <li>❌ Doar 2 analize AI/lună (vs. 30 acum)</li>
                                <li>❌ Doar specialistul General (pierzi Nutriționist, Fitness, Cardiolog, etc.)</li>
                                <li>❌ Fără export PDF</li>
                                <li>❌ Fără partajare cu medicii</li>
                                <li>❌ Fără comparație istorică</li>
                            </ul>
                        </div>
                        <p>Păstrează totul pentru doar <strong>29 RON/lună</strong> sau economisește 43% cu planul anual la <strong>199 RON/an</strong> (doar 16,58 RON/lună).</p>
                        <p style="text-align:center;"><a href="{app_url}/billing" class="button">Păstrează Premium</a></p>
                    </div>
                    {footer_ro}
                </div></body></html>"""
            },
            "en": {
                "subject": f"{name}, 7 days left on Premium — here's what you'll lose",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header-trial">
                        <span class="badge">7 DAYS LEFT</span>
                        <h1 style="margin:10px 0 0 0;">Your trial is ending soon</h1>
                    </div>
                    <div class="content">
                        <h2>What you'll lose in 7 days</h2>
                        <p>Hi {name},</p>
                        <p>Your Premium trial expires in 7 days. After that, you'll move to the Free plan which only includes:</p>
                        <div class="highlight-red">
                            <strong>Free plan:</strong>
                            <ul style="margin: 10px 0;">
                                <li>❌ Only 1 medical provider (vs. unlimited now)</li>
                                <li>❌ Only 20 documents (vs. 500 now)</li>
                                <li>❌ Only 2 AI analyses/month (vs. 30 now)</li>
                                <li>❌ Only General specialist (lose Nutritionist, Fitness, Cardiologist, etc.)</li>
                                <li>❌ No PDF export</li>
                                <li>❌ No sharing with doctors</li>
                                <li>❌ No historical comparison</li>
                            </ul>
                        </div>
                        <p>Keep everything for just <strong>29 RON/month</strong> or save 43% with the annual plan at <strong>199 RON/year</strong> (only 16.58 RON/month).</p>
                        <p style="text-align:center;"><a href="{app_url}/billing" class="button">Keep Premium</a></p>
                    </div>
                    {footer_en}
                </div></body></html>"""
            }
        },
        "trial_day27": {
            "ro": {
                "subject": f"Ultimele 3 zile de Premium, {name}!",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header-trial">
                        <span class="badge">3 ZILE RĂMASE</span>
                        <h1 style="margin:10px 0 0 0;">Ultima șansă!</h1>
                    </div>
                    <div class="content">
                        <h2>Nu pierde accesul Premium!</h2>
                        <p>Salut {name},</p>
                        <p>Mai ai doar <strong>3 zile</strong> din trialul Premium. După aceea, vei pierde accesul la:</p>
                        <ul>
                            <li>Planurile de nutriție personalizate</li>
                            <li>Programul de exerciții adaptat</li>
                            <li>Specialiștii AI (Cardiolog, Endocrinolog, Hematolog...)</li>
                            <li>Toate cele 30 de analize AI/lună</li>
                        </ul>
                        <div class="highlight">
                            <strong>Ofertă specială:</strong> Plătește anual la <strong>199 RON/an</strong> și economisești 43% — doar <strong>16,58 RON/lună</strong>!
                        </div>
                        <p style="text-align:center;"><a href="{app_url}/billing" class="button-urgent">Upgrade acum</a></p>
                    </div>
                    {footer_ro}
                </div></body></html>"""
            },
            "en": {
                "subject": f"Last 3 days of Premium, {name}!",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header-trial">
                        <span class="badge">3 DAYS LEFT</span>
                        <h1 style="margin:10px 0 0 0;">Last chance!</h1>
                    </div>
                    <div class="content">
                        <h2>Don't lose Premium access!</h2>
                        <p>Hi {name},</p>
                        <p>You only have <strong>3 days</strong> left on your Premium trial. After that, you'll lose access to:</p>
                        <ul>
                            <li>Personalized nutrition plans</li>
                            <li>Adapted exercise programs</li>
                            <li>AI specialists (Cardiologist, Endocrinologist, Hematologist...)</li>
                            <li>All 30 AI analyses per month</li>
                        </ul>
                        <div class="highlight">
                            <strong>Special offer:</strong> Pay annually at <strong>199 RON/year</strong> and save 43% — just <strong>16.58 RON/month</strong>!
                        </div>
                        <p style="text-align:center;"><a href="{app_url}/billing" class="button-urgent">Upgrade now</a></p>
                    </div>
                    {footer_en}
                </div></body></html>"""
            }
        },
        "trial_day30": {
            "ro": {
                "subject": "Trialul tău Premium s-a încheiat",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header"><h1 style="margin:0;">Analize.online</h1></div>
                    <div class="content">
                        <h2>Trialul Premium s-a încheiat</h2>
                        <p>Salut {name},</p>
                        <p>Trialul tău Premium de 30 de zile s-a încheiat. Contul tău a fost trecut pe planul <strong>Free</strong>.</p>
                        <p>Acum ai acces la:</p>
                        <ul>
                            <li>1 provider medical</li>
                            <li>20 de documente</li>
                            <li>2 analize AI pe lună (doar General)</li>
                        </ul>
                        <p>Datele tale sunt în siguranță și poți face upgrade oricând pentru a recăpăta accesul complet.</p>
                        <div class="highlight">
                            <strong>Recapătă Premium:</strong> Doar 29 RON/lună sau 199 RON/an (economisești 43%).
                        </div>
                        <p style="text-align:center;"><a href="{app_url}/billing" class="button">Upgrade la Premium</a></p>
                    </div>
                    {footer_ro}
                </div></body></html>"""
            },
            "en": {
                "subject": "Your Premium trial has ended",
                "html": f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{style}</style></head><body>
                <div class="container">
                    <div class="header"><h1 style="margin:0;">Analize.online</h1></div>
                    <div class="content">
                        <h2>Premium trial ended</h2>
                        <p>Hi {name},</p>
                        <p>Your 30-day Premium trial has ended. Your account has been moved to the <strong>Free</strong> plan.</p>
                        <p>You now have access to:</p>
                        <ul>
                            <li>1 medical provider</li>
                            <li>20 documents</li>
                            <li>2 AI analyses per month (General only)</li>
                        </ul>
                        <p>Your data is safe and you can upgrade anytime to regain full access.</p>
                        <div class="highlight">
                            <strong>Get Premium back:</strong> Just 29 RON/month or 199 RON/year (save 43%).
                        </div>
                        <p style="text-align:center;"><a href="{app_url}/billing" class="button">Upgrade to Premium</a></p>
                    </div>
                    {footer_en}
                </div></body></html>"""
            }
        },
    }

    content = emails.get(day_key, {}).get(language, emails.get(day_key, {}).get("ro", {}))
    return content


def run_welcome_email_campaigns():
    """Check for users who should receive trial sequence emails.

    Called by the scheduler every hour.
    """
    try:
        from backend_v2.database import SessionLocal
        from backend_v2.models import User, Notification, LinkedAccount, Subscription
        from backend_v2.services.email_service import get_email_service
    except ImportError:
        from database import SessionLocal
        from models import User, Notification, LinkedAccount, Subscription
        from services.email_service import get_email_service

    email_service = get_email_service()
    if not email_service.is_configured():
        return

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        for step in TRIAL_SEQUENCE:
            day = step["day"]
            key = step["key"]

            target_time = now - timedelta(days=day)
            window_start = target_time - timedelta(hours=1)
            window_end = target_time

            users = db.query(User).filter(
                User.created_at >= window_start,
                User.created_at < window_end,
                User.is_active == True,
                User.email_verified == True
            ).all()

            for user in users:
                already_sent = db.query(Notification).filter(
                    Notification.user_id == user.id,
                    Notification.notification_type == f"campaign_{key}"
                ).first()

                if already_sent:
                    continue

                # Skip paying users (converted mid-trial)
                sub = db.query(Subscription).filter(
                    Subscription.user_id == user.id
                ).first()
                if sub and sub.tier in ("premium", "family") and sub.status == "active":
                    continue

                has_provider = db.query(LinkedAccount).filter(
                    LinkedAccount.user_id == user.id
                ).count() > 0

                language = user.language or "ro"
                user_name = user.full_name or user.email.split("@")[0]

                content = get_trial_email(key, user_name, language, has_provider)
                if not content:
                    continue

                sent = email_service.send_email(user.email, content["subject"], content["html"])

                notification = Notification(
                    user_id=user.id,
                    notification_type=f"campaign_{key}",
                    title=content["subject"],
                    message=f"Trial email day {day}",
                    is_sent_email=sent,
                    sent_at=now if sent else None
                )
                db.add(notification)

            db.commit()

    except Exception as e:
        logger.error(f"Error in trial email campaigns: {e}")
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

        users = db.query(User).filter(
            User.is_active == True,
            User.email_verified == True
        ).all()

        for user in users:
            prefs = db.query(NotificationPreference).filter(
                NotificationPreference.user_id == user.id
            ).first()
            if prefs and not prefs.email_reminders:
                continue

            already_sent = db.query(Notification).filter(
                Notification.user_id == user.id,
                Notification.notification_type == "monthly_digest",
                Notification.created_at >= now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            ).first()
            if already_sent:
                continue

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
