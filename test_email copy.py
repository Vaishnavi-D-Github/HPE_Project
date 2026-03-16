import os
from flask import Flask
from flask_mail import Mail, Message
from dotenv import load_dotenv

# Load variables from your .env file
load_dotenv()

# Set up a dummy Flask app just for testing
app = Flask(__name__)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

# Send the test email
with app.app_context():
    try:
        # Sending it to yourself to test
        msg = Message("RRO Platform - Email Test", recipients=[os.getenv('MAIL_USERNAME')])
        msg.body = "If you are reading this, your Google App Password is working perfectly!"
        mail.send(msg)
        print("✅ Success! Check your inbox.")
    except Exception as e:
        print(f"❌ Error: {e}")