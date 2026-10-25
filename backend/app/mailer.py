"""Pengiriman email sederhana (smtplib, tanpa library tambahan)."""
import smtplib
import ssl
import threading
from email.message import EmailMessage

from flask import current_app


def _send_smtp(cfg, msg):
    try:
        if cfg["security"] == "ssl":
            server = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=15, context=ssl.create_default_context())
        else:
            server = smtplib.SMTP(cfg["host"], cfg["port"], timeout=15)
            if cfg["security"] == "starttls":
                server.starttls(context=ssl.create_default_context())
        with server:
            if cfg["user"]:
                server.login(cfg["user"], cfg["password"])
            server.send_message(msg)
    except Exception as exc:  # jangan menjatuhkan request; detail hanya di log server
        cfg["logger"].error("Gagal mengirim email: %s: %s", type(exc).__name__, exc)


def send_email(to, subject, text, html=None):
    """Kirim email di thread terpisah (tidak memperlambat respons). Tanpa SMTP: cetak ke log server."""
    app = current_app
    cfg_app = app.config
    if not cfg_app["SMTP_HOST"]:
        app.logger.warning(
            "\n=========== [EMAIL MODE PENGEMBANGAN - SMTP belum diatur] ===========\n"
            "Kepada : %s\nSubjek : %s\n\n%s\n"
            "======================================================================",
            to, subject, text,
        )
        return

    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = cfg_app["MAIL_FROM"], to, subject
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")
    cfg = {
        "host": cfg_app["SMTP_HOST"], "port": cfg_app["SMTP_PORT"], "user": cfg_app["SMTP_USER"],
        "password": cfg_app["SMTP_PASSWORD"], "security": cfg_app["SMTP_SECURITY"], "logger": app.logger,
    }
    threading.Thread(target=_send_smtp, args=(cfg, msg), daemon=True).start()


def _wrap(title, intro, button, link, outro):
    html = f"""<div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;color:#1f2a37">
<h2 style="color:#1e3a5f">{title}</h2><p>{intro}</p>
<p><a href="{link}" style="background:#1e3a5f;color:#fff;padding:12px 22px;border-radius:8px;text-decoration:none;display:inline-block">{button}</a></p>
<p style="font-size:13px;color:#5b6b7c">Kalau tombol tidak berfungsi, salin tautan ini ke browser:<br>{link}</p>
<p style="font-size:13px;color:#5b6b7c">{outro}</p></div>"""
    text = f"{title}\n\n{intro}\n\n{link}\n\n{outro}"
    return text, html


def send_verification_email(user, link, hours):
    text, html = _wrap(
        "Verifikasi email BudgetIn",
        f"Halo {user.name}, konfirmasi bahwa ini adalah email kamu agar akun BudgetIn aktif sepenuhnya.",
        "Verifikasi email", link,
        f"Tautan berlaku {hours} jam. Kalau kamu tidak merasa mendaftar, abaikan email ini.",
    )
    send_email(user.email, "Verifikasi email BudgetIn", text, html)


def send_reset_email(user, link, minutes):
    text, html = _wrap(
        "Reset password BudgetIn",
        f"Halo {user.name}, kami menerima permintaan untuk mengatur ulang password akunmu.",
        "Atur password baru", link,
        f"Tautan berlaku {minutes} menit dan hanya bisa dipakai sekali. Kalau bukan kamu yang meminta, abaikan email ini; password-mu tidak berubah.",
    )
    send_email(user.email, "Reset password BudgetIn", text, html)
