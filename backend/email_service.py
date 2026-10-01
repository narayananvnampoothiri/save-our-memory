import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config import Config

def send_reset_code_email(to_email: str, code: str) -> tuple[bool, str]:
    """
    Sends a 6-digit one-time password reset code to the specified email address via SMTP.
    If SMTP credentials are not configured, logs the code for local development/testing.
    Returns (success: bool, status_message: str).
    """
    subject = "Your Save Our Memory One-Time Verification Code"
    
    # Text fallback
    text_content = (
        f"Save Our Memory • Password Reset\n\n"
        f"You requested to reset your password. Your 6-digit one-time verification code is:\n\n"
        f"    {code}\n\n"
        f"This code will expire in {Config.RESET_CODE_EXPIRE_MINUTES} minutes.\n"
        f"If you did not request this, please ignore this email.\n"
    )

    # HTML Template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #FBF8F6; color: #2D2526; margin: 0; padding: 24px; }}
        .card {{ max-width: 520px; margin: 0 auto; background: #FFFFFF; border-radius: 16px; padding: 36px 32px; border: 1px solid #F0E6E4; box-shadow: 0 4px 20px rgba(0,0,0,0.04); }}
        .logo {{ font-size: 26px; font-weight: 700; color: #D46B6B; text-align: center; margin-bottom: 24px; }}
        .title {{ font-size: 20px; font-weight: 600; text-align: center; margin-bottom: 12px; color: #1E1A1B; }}
        .subtitle {{ font-size: 14px; color: #6F6668; text-align: center; line-height: 1.5; margin-bottom: 28px; }}
        .otp-box {{ background: #FFF5F5; border: 2px dashed #E5989B; border-radius: 12px; padding: 20px; text-align: center; margin: 0 auto 28px; }}
        .otp-code {{ font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #D46B6B; font-family: monospace; }}
        .expiry-note {{ font-size: 13px; color: #8F8486; text-align: center; margin-bottom: 24px; }}
        .footer {{ font-size: 12px; color: #A09698; text-align: center; border-top: 1px solid #F4EDED; padding-top: 20px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="logo">❤️ Save Our Memory</div>
        <div class="title">Password Reset Request</div>
        <div class="subtitle">
          We received a request to reset the password for your account. Enter the one-time verification code below into the app:
        </div>
        <div class="otp-box">
          <div class="otp-code">{code}</div>
        </div>
        <div class="expiry-note">
          ⏳ This verification code will expire in <strong>{Config.RESET_CODE_EXPIRE_MINUTES} minutes</strong>.
          <br>For your security, never share this code with anyone.
        </div>
        <div class="footer">
          If you did not request a password reset, you can safely ignore this email. Your memory vault remains secure.
        </div>
      </div>
    </body>
    </html>
    """

    # If SMTP is not configured, log to console for development testing
    if not Config.SMTP_HOST or not Config.SMTP_USER:
        print(f"[SECURITY / EMAIL LOG] (SMTP not configured) Verification code for {to_email}: {code}")
        return False, "SMTP email server is not configured in .env. Code logged to terminal."

    # Build MIME message
    msg = MIMEMultipart("alternative")
    sender = Config.SMTP_FROM or Config.SMTP_USER
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email

    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        # Determine port & SSL/TLS
        if Config.SMTP_PORT == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT, context=context, timeout=15) as server:
                if Config.SMTP_USER and Config.SMTP_PASSWORD:
                    server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                server.sendmail(sender, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=15) as server:
                if Config.SMTP_TLS:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                if Config.SMTP_USER and Config.SMTP_PASSWORD:
                    server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                server.sendmail(sender, [to_email], msg.as_string())

        print(f"[EMAIL SUCCESS] Verification code successfully sent via SMTP to {to_email}")
        return True, "Verification code sent to your email successfully."
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email via SMTP to {to_email}: {e}")
        return False, f"Could not send email: {str(e)}"
