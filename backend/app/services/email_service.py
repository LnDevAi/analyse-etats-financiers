"""
Service d'envoi d'emails transactionnels via SMTP.
Utilisé pour : réinitialisation de mot de passe, alertes de sécurité.
"""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_reset_email(recipient: str, reset_link: str, full_name: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Réinitialisation de votre mot de passe — E-DÉFENCE"
    msg["From"] = f"E-DÉFENCE <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = recipient

    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head><meta charset="utf-8"></head>
    <body style="font-family:Arial,sans-serif;background:#F8FAFC;margin:0;padding:20px;">
      <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:8px;padding:32px;box-shadow:0 1px 3px rgba(0,0,0,.1);">
        <div style="text-align:center;margin-bottom:24px;">
          <h1 style="color:#1e293b;font-size:24px;margin:0;">E-DÉFENCE</h1>
          <p style="color:#64748b;font-size:12px;margin:4px 0 0;">Analyse Financière IA — SYSCOHADA</p>
        </div>
        <h2 style="color:#1e293b;font-size:18px;">Bonjour {full_name},</h2>
        <p style="color:#374151;line-height:1.6;">
          Nous avons reçu une demande de réinitialisation de mot de passe pour votre compte E-DÉFENCE.
        </p>
        <p style="color:#374151;line-height:1.6;">
          Cliquez sur le bouton ci-dessous pour définir un nouveau mot de passe.
          Ce lien expire dans <strong>30 minutes</strong>.
        </p>
        <div style="text-align:center;margin:32px 0;">
          <a href="{reset_link}"
             style="background:#1e293b;color:#fff;text-decoration:none;padding:14px 28px;border-radius:6px;font-weight:bold;font-size:15px;">
            Réinitialiser mon mot de passe
          </a>
        </div>
        <p style="color:#6b7280;font-size:13px;line-height:1.6;">
          Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.
          Votre mot de passe restera inchangé.
        </p>
        <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
        <p style="color:#9ca3af;font-size:11px;text-align:center;">
          E-DÉFENCE SaaS — Burkina Faso &amp; UEMOA<br>
          Cet email est envoyé automatiquement, merci de ne pas y répondre.
        </p>
      </div>
    </body>
    </html>
    """

    plain = (
        f"Bonjour {full_name},\n\n"
        f"Pour réinitialiser votre mot de passe E-DÉFENCE, cliquez sur ce lien (valable 30 min) :\n"
        f"{reset_link}\n\n"
        f"Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.\n"
    )

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    return msg


async def send_password_reset_email(recipient: str, full_name: str, reset_token: str) -> bool:
    """Envoie un email de réinitialisation de mot de passe. Retourne True si succès."""
    if not settings.SMTP_HOST:
        logger.warning("SMTP non configuré — email de réinitialisation non envoyé.")
        return False

    frontend_url = settings.FRONTEND_URL.rstrip("/")
    reset_link = f"{frontend_url}/auth/reset-password?token={reset_token}"
    msg = _build_reset_email(recipient, reset_link, full_name)

    try:
        if settings.SMTP_USE_TLS:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            if settings.SMTP_USE_STARTTLS:
                server.starttls()

        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

        server.sendmail(settings.SMTP_FROM_EMAIL, [recipient], msg.as_string())
        server.quit()
        logger.info(f"Email réinitialisation envoyé à {recipient}")
        return True

    except Exception as e:
        logger.error(f"Échec envoi email à {recipient}: {e}")
        return False
