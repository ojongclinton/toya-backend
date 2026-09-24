
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

class EmailSender:
    def __init__(self):
        pass

    def send_email(self, receiver_email, subject, body, html=True, sender_email=None, attachments=None):
        smtp_server = os.environ.get('EMAIL_HOST')
        smtp_port = int(os.environ.get('EMAIL_PORT', '465'))
        username = os.environ.get('EMAIL_HOST_USER')
        password = os.environ.get('EMAIL_HOST_PASSWORD')
        sender_email = sender_email or os.environ.get('DEFAULT_FROM_EMAIL', username)

        if not all([smtp_server, username, password, sender_email]):
            raise RuntimeError('Email service environment variables are incomplete.')


        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject

        mime_body = MIMEText(body, "html" if html else "plain")
        message.attach(mime_body)

        if attachments:
            for file_path in attachments:
                try:
                    with open(file_path, "rb") as attachment_file:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(attachment_file.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(file_path)}")
                    message.attach(part)
                except Exception as e:
                    print(f"Erreur lors de l'ajout de la pièce jointe '{file_path}': {e}")

        try:
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(username, password)
                server.sendmail(sender_email, receiver_email, message.as_string())
            print("E-mail envoyé avec succès !")
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'e-mail : {e}")
