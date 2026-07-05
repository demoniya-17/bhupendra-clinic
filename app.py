from flask import Flask, request, jsonify, send_from_directory
import json
import os
from datetime import datetime
import urllib.request
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

# ==========================================
# CORS SUPPORT
# ==========================================
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# ==========================================
# TELEGRAM CONFIGURATION
# ==========================================
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8697310770:AAFdSoN7Ux3SiatE8o1qSLxVICFSi2mTEuc')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '7472435105')

# ==========================================
# TELEGRAM SEND FUNCTION
# ==========================================
def send_telegram_message(token, chat_id, message):
    """Send Telegram message using Bot API"""
    try:
        encoded_message = urllib.parse.quote(message)
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={encoded_message}&parse_mode=Markdown"

        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as response:
            result = response.read().decode('utf-8')
            return True, result

    except Exception as e:
        return False, str(e)

# ==========================================
# ROUTES
# ==========================================

@app.route('/')
def index():
    try:
        return send_from_directory(BASE_DIR, 'index.html')
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/api/appointment', methods=['POST', 'OPTIONS'])
def submit_appointment():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'No data received'
            }), 400

        required_fields = ['fullName', 'email', 'phone']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field} is required'
                }), 400

        # Save appointment
        appointments_dir = os.path.join(BASE_DIR, 'appointments')
        if not os.path.exists(appointments_dir):
            os.makedirs(appointments_dir)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(appointments_dir, f'appointment_{timestamp}.json')

        data['serverReceivedAt'] = datetime.now().isoformat()

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # ==========================================
        # SEND TELEGRAM NOTIFICATION
        # ==========================================
        telegram_sent = False
        telegram_error = None

        try:
            service_names = {
                'cancer-diet': 'Cancer Diet Plan',
                'weight-loss': 'Weight Loss / Gain',
                'chronic-disease': 'Chronic Disease (Diabetes, BP etc.)',
                'nutrition-coaching': 'Nutrition Coaching',
                'wellness-general': 'General Wellness'
            }

            service_name = service_names.get(data.get('serviceInterest', ''), 'General Inquiry')

            telegram_message = f"""🆕 *New Appointment Request*

👤 *Name:* {data['fullName']}
📧 *Email:* {data['email']}
📱 *Phone:* {data['phone']}
🩺 *Service:* {service_name}
⏰ *Time:* {datetime.now().strftime('%d %b %Y, %I:%M %p')}

📝 *Message:*
{data.get('message', 'No message')}

📞 Please contact within 24 hours."""

            success, result = send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, telegram_message)

            if success:
                telegram_sent = True
            else:
                telegram_error = result

        except Exception as e:
            telegram_error = str(e)
            telegram_sent = False

        return jsonify({
            'success': True,
            'message': 'Appointment request submitted successfully! We will contact you within 24 hours.',
            'appointmentId': timestamp,
            'telegramNotification': telegram_sent,
            'telegramError': telegram_error
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
        'timestamp': datetime.now().isoformat(),
        'telegram_configured': True
    })

@app.route('/api/test-telegram', methods=['GET'])
def test_telegram():
    try:
        message = "🧪 *Test message* from Bhupendra Clinic website. Telegram integration is working!"
        success, result = send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)

        if success:
            return jsonify({
                'success': True,
                'message': 'Test message sent to Telegram'
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 500

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
