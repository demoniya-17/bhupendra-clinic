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
# WHATSAPP CONFIGURATION (CallMeBot)
# ==========================================
# Step 1: Open https://api.callmebot.com/whatsapp.php in browser
# Step 2: Enter your WhatsApp number with country code (e.g., +919582082682)
# Step 3: Click "Send" to get verification code on WhatsApp
# Step 4: Enter verification code on website
# Step 5: Copy the API key shown
# Step 6: Update YOUR_API_KEY below

YOUR_PHONE = os.environ.get('WHATSAPP_PHONE', '+919582082682')  # Aapka WhatsApp number
YOUR_API_KEY = os.environ.get('WHATSAPP_API_KEY', 'YOUR_API_KEY_HERE')  # CallMeBot se milega

# ==========================================
# WHATSAPP SEND FUNCTION
# ==========================================
def send_whatsapp_message(phone, api_key, message):
    """Send WhatsApp message using CallMeBot API"""
    try:
        # URL encode the message
        encoded_message = urllib.parse.quote(message)

        # CallMeBot API URL
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_message}&apikey={api_key}"

        # Send request
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
    """Serve index.html from root folder"""
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
        # SEND WHATSAPP NOTIFICATION
        # ==========================================
        whatsapp_sent = False
        whatsapp_error = None

        try:
            service_names = {
                'cancer-diet': 'Cancer Diet Plan',
                'weight-loss': 'Weight Loss / Gain',
                'chronic-disease': 'Chronic Disease (Diabetes, BP etc.)',
                'nutrition-coaching': 'Nutrition Coaching',
                'wellness-general': 'General Wellness'
            }

            service_name = service_names.get(data.get('serviceInterest', ''), 'General Inquiry')

            # Format WhatsApp message
            whatsapp_message = f"""🆕 *New Appointment Request*

👤 *Name:* {data['fullName']}
📧 *Email:* {data['email']}
📱 *Phone:* {data['phone']}
🩺 *Service:* {service_name}
⏰ *Time:* {datetime.now().strftime('%d %b %Y, %I:%M %p')}

📝 *Message:*
{data.get('message', 'No message')}

📞 Please contact within 24 hours."""

            # Send WhatsApp
            success, result = send_whatsapp_message(YOUR_PHONE, YOUR_API_KEY, whatsapp_message)

            if success:
                whatsapp_sent = True
            else:
                whatsapp_error = result

        except Exception as e:
            whatsapp_error = str(e)
            whatsapp_sent = False

        return jsonify({
            'success': True,
            'message': 'Appointment request submitted successfully! We will contact you within 24 hours.',
            'appointmentId': timestamp,
            'whatsappNotification': whatsapp_sent,
            'whatsappError': whatsapp_error
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
        'whatsapp_configured': YOUR_API_KEY != 'YOUR_API_KEY_HERE'
    })

@app.route('/api/test-whatsapp', methods=['GET'])
def test_whatsapp():
    """Test WhatsApp integration"""
    if YOUR_API_KEY == 'YOUR_API_KEY_HERE':
        return jsonify({
            'success': False,
            'error': 'API key not configured. Please set up CallMeBot first.'
        }), 500

    try:
        message = "🧪 Test message from Bhupendra Clinic website. WhatsApp integration is working!"
        success, result = send_whatsapp_message(YOUR_PHONE, YOUR_API_KEY, message)

        if success:
            return jsonify({
                'success': True,
                'message': f'Test WhatsApp sent to {YOUR_PHONE}'
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
