import smtplib
from email.message import EmailMessage

def send_email(sender_email, app_password, recipient_email, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Example usage:
send_email(
    sender_email="offer@cgi.com",
    app_password="abcdefghijkmnop",  # Use App Password, not Gmail password
    recipient_email="anandkumarsingh@gmail.com",
    subject="Test Email",
    body="Hello, this is a test email from Python!"
)
