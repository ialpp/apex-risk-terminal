import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
import textwrap

def send_email(to_email: str, subject: str, body_html: str):
    """
    SMTP üzerinden e-posta gönderir.
    Zaman aşımı ve SSL sertifika desteği eklendi.
    """
    try:
        email_config = st.secrets.get("email", {})
        smtp_server = email_config.get("smtp_server")
        smtp_port = email_config.get("smtp_port", 465)
        smtp_user = email_config.get("smtp_user")
        smtp_pass = email_config.get("smtp_pass")

        if not all([smtp_server, smtp_user, smtp_pass]):
            st.error("❌ secrets.toml içinde [email] ayarları eksik!")
            return False

        msg = MIMEMultipart()
        msg['From'] = f"Apex Risk Terminal <{smtp_user}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body_html, 'html'))

        # Güvenlik Protokolleri
        context = ssl.create_default_context()

        # Sunucuya bağlan (10 saniye limit eklendi)
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=10)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
            server.starttls(context=context)

        with server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        
        return True
    except Exception as e:
        st.error(f"⚠️ E-posta Gönderim Hatası (Port {smtp_port}): {e}")
        st.info("İpucu: Eğer 10060 hatası devam ediyorsa, Windows Güvenlik Duvarı veya Antivirüs programın Python'ın dışarıya mail atmasını engelliyor olabilir.")
        return False

def send_otp_email(to_email: str, otp_code: str):
    """Giriş doğrulaması için OTP kodu gönderir."""
    subject = f"🔐 Apex Risk Terminal - Giriş Doğrulama Kodunuz: {otp_code}"
    body = textwrap.dedent(f"""
        <html>
        <body style="font-family: sans-serif; color: #1e293b;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">
                <h2 style="color: #004C91;">Apex Risk Terminal</h2>
                <p>Merhaba,</p>
                <p>Sisteme giriş yapabilmek için aşağıdaki 6 haneli güvenlik kodunu kullanın:</p>
                <div style="font-size: 2rem; font-weight: 800; letter-spacing: 5px; color: #38BDF8; padding: 20px 0; text-align: center; background: #f8fafc; border-radius: 8px;">
                    {otp_code}
                </div>
                <p style="font-size: 0.85rem; color: #64748b; margin-top: 20px;">
                    Bu kod 5 dakika boyunca geçerlidir. Eğer bu işlemi siz yapmadıysanız lütfen BT departmanına bildirin.
                </p>
                <hr style="border: none; border-top: 1px solid #f1f5f9; margin: 20px 0;">
                <p style="font-size: 0.75rem; color: #94a3b8;">
                    © 2026 ProQuant Institutional - Apex Risk Management Suite
                </p>
            </div>
        </body>
        </html>
    """)
    return send_email(to_email, subject, body)

def send_password_reset_email(to_email: str, temp_pass: str):
    """Şifre sıfırlama talebi için geçici şifre gönderir."""
    subject = "🔑 Apex Risk Terminal - Şifre Sıfırlama Talebi"
    body = textwrap.dedent(f"""
        <html>
        <body style="font-family: sans-serif; color: #1e293b;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">
                <h2 style="color: #004C91;">Apex Risk Terminal</h2>
                <p>Merhaba,</p>
                <p>Şifre sıfırlama talebiniz üzerine hesabınız için geçici bir şifre oluşturulmuştur:</p>
                <div style="font-size: 1.5rem; font-weight: 700; color: #ef4444; padding: 15px 0; text-align: center; background: #fff1f2; border-radius: 8px;">
                    {temp_pass}
                </div>
                <p>Sisteme bu şifre ile giriş yaptıktan sonra <b>Ayarlar</b> menüsünden şifrenizi değiştirmenizi önemle rica ederiz.</p>
                <hr style="border: none; border-top: 1px solid #f1f5f9; margin: 20px 0;">
                <p style="font-size: 0.75rem; color: #94a3b8;">
                    © 2026 ProQuant Institutional - Apex Risk Management Suite
                </p>
            </div>
        </body>
        </html>
    """)
    return send_email(to_email, subject, body)
