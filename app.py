from flask import Flask, request, jsonify, send_from_directory
import json
import os
from datetime import datetime
from flask_mail import Mail, Message

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

# ==========================================
# EMAIL CONFIGURATION
# ==========================================
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'bhupiender2502@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'znqb edvb jwck uszb')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME', 'bhupiender2502@gmail.com')

mail = Mail(app)
YOUR_EMAIL = os.environ.get('YOUR_EMAIL', 'bhupiender2502@gmail.com')

# ==========================================
# ROUTES
# ==========================================

@app.route('/')
def index():
    """Serve index.html from root folder"""
    try:
        return send_from_directory(BASE_DIR, 'index.html')
    except Exception as e:
        return f"Error: {str(e)}. Make sure index.html is in the same folder as app.py", 500

@app.route('/api/appointment', methods=['POST'])
def submit_appointment():
    try:
        data = request.get_json()

        required_fields = ['fullName', 'email', 'phone']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field} is required'
                }), 400

        appointments_dir = os.path.join(BASE_DIR, 'appointments')
        if not os.path.exists(appointments_dir):
            os.makedirs(appointments_dir)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(appointments_dir, f'appointment_{timestamp}.json')

        data['serverReceivedAt'] = datetime.now().isoformat()

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Send email notification
        email_sent = False
        email_error_msg = None

        try:
            service_names = {
                'cancer-diet': 'Cancer Diet Plan',
                'weight-loss': 'Weight Loss / Gain',
                'chronic-disease': 'Chronic Disease (Diabetes, BP etc.)',
                'nutrition-coaching': 'Nutrition Coaching',
                'wellness-general': 'General Wellness'
            }

            service_name = service_names.get(data.get('serviceInterest', ''), 'General Inquiry')

            email_subject = f"New Appointment Request - {data['fullName']}"

            email_body = f"""Hello Dr. Bhupendra,

You have received a new appointment request from your website!

PATIENT DETAILS
----------------
Name: {data['fullName']}
Email: {data['email']}
Phone: {data['phone']}
Service: {service_name}
Submitted At: {datetime.now().strftime('%d %B %Y, %I:%M %p')}

MESSAGE / HEALTH GOALS
----------------------
{data.get('message', 'No message provided')}

Next Steps:
- Contact the patient within 24 hours
- Confirm appointment date and time
- Prepare their medical history form

Bhupendra Diet & Wellness Clinic
WZ-09/Shop no.09 New Mahavir Nagar, New Delhi 110018
Phone: +91 9582082682

---
This is an automated notification from your clinic website.
            """

            msg = Message(
                subject=email_subject,
                recipients=[YOUR_EMAIL],
                body=email_body
            )

            mail.send(msg)
            email_sent = True

        except Exception as email_error:
            email_error_msg = str(email_error)
            email_sent = False

        return jsonify({
            'success': True,
            'message': 'Appointment request submitted successfully! We will contact you within 24 hours.',
            'appointmentId': timestamp,
            'emailNotification': email_sent,
            'emailError': email_error_msg
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/test-email', methods=['GET'])
def test_email():
    try:
        msg = Message(
            subject='Test Email - Bhupendra Clinic Website',
            recipients=[YOUR_EMAIL],
            body='This is a test email from your clinic website. If you received this, email is working!'
        )
        mail.send(msg)
        return jsonify({
            'success': True,
            'message': f'Test email sent to {YOUR_EMAIL}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/appointments', methods=['GET'])
def list_appointments():
    try:
        appointments_dir = os.path.join(BASE_DIR, 'appointments')
        if not os.path.exists(appointments_dir):
            return jsonify({'appointments': []})

        appointments = []
        for filename in sorted(os.listdir(appointments_dir), reverse=True):
            if filename.endswith('.json'):
                with open(os.path.join(appointments_dir, filename), 'r', encoding='utf-8') as f:
                    appointments.append(json.load(f))

        return jsonify({
            'count': len(appointments),
            'appointments': appointments
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
