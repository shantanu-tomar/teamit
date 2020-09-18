import smtplib
from email.message import EmailMessage
from django.conf import settings


def send_mail(recp_email_list, subject, body):
    web_email_add = settings.EMAIL_HOST_USER
    web_email_pass = settings.EMAIL_HOST_PASSWORD
    email_host = settings.EMAIL_HOST
    email_port = settings.EMAIL_PORT
    
    for mail in recp_email_list:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = web_email_add
        msg['To'] = mail

        msg.set_content(body)

        with smtplib.SMTP_SSL(email_host, email_port) as smtp:
            smtp.login(web_email_add, web_email_pass)
            smtp.send_message(msg)
    return
