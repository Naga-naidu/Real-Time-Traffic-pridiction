from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
import datetime
import random
from flask_mail import Mail, Message
app =  Flask(__name__)
app.secret_key = 'fzfg ywln tgaw pjkg'
# Mail config
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='gajulanaga180@gmail.com',       # Change this
    MAIL_PASSWORD='your_email_app_password',    # App password from Gmail
)

mail = Mail(app)
CORS(app)
bcrypt = Bcrypt(app)

# Setup Login
login_manager = LoginManager()
login_manager.init_app(app)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['traffic_prediction']
users = db['users']
predictions = db['predictions']

# User Loader
class User(UserMixin):
    def init(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.role = user_data.get('role', 'user')

@login_manager.user_loader
def load_user(user_id):
    user_data = users.find_one({"_id": user_id})
    return User(user_data) if user_data else None

# --- Register User (Optional Route for initial setup) ---
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    hashed = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    users.insert_one({
        'username': data['username'],
        'password': hashed,
        'role': data.get('role', 'user')
    })
    return jsonify({'message': 'User registered successfully'}), 201

# --- Login ---
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user_data = users.find_one({'username': data['username']})
    if user_data and bcrypt.check_password_hash(user_data['password'], data['password']):
        user = User(user_data)
        login_user(user)
        return jsonify({'message': 'Login successful', 'role': user.role})
    return jsonify({'message': 'Invalid credentials'}), 401

# --- Logout ---
@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out'})

# --- Predict Traffic ---
@app.route('/predict', methods=['GET'])
def predict_traffic():
    traffic_levels = ['Light', 'Moderate', 'Heavy']
    prediction = random.choice(traffic_levels)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save to DB
    predictions.insert_one({
        'prediction': prediction,
        'timestamp': timestamp,
        'user': current_user.username if current_user.is_authenticated else 'guest'
    })

    return jsonify({'prediction': prediction, 'timestamp': timestamp})

# --- Admin Route: View All Predictions ---
@app.route('/admin/predictions', methods=['GET'])
@login_required
def view_predictions():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    data = list(predictions.find({}, {'_id': 0}))
    return jsonify(data)

if name == 'main':
    app.run(debug=True)
    import random

# Store OTPs temporarily
otp_store = {}

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data['email']
    user = users.find_one({'username': data['username']})
    if not user:
        return jsonify({'message': 'User not found'}), 404

    otp = random.randint(1000, 9999)
    otp_store[email] = otp

    msg = Message("🔐 OTP for Password Reset",
                  sender="your.email@gmail.com",
                  recipients=[email])
    msg.body = f"Your OTP is: {otp}"
    mail.send(msg)

    return jsonify({'message': 'OTP sent to email'})
@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    otp = int(data['otp'])
    email = data['email']
    new_password = bcrypt.generate_password_hash(data['new_password']).decode('utf-8')

    if otp_store.get(email) == otp:
        users.update_one({'username': data['username']}, {'$set': {'password': new_password}})
        del otp_store[email]
        return jsonify({'message': 'Password reset successful'})
    return jsonify({'message': 'Invalid OTP'}), 400
import csv
from flask import Response

@app.route('/admin/download', methods=['GET'])
@login_required
def download_csv():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    output = []
    for row in predictions.find():
        output.append([row.get('user', 'guest'), row['prediction'], row['timestamp']])

    def generate():
        yield 'User,Prediction,Timestamp\n'
        for line in output:
            yield ','.join(line) + '\n'

    return Response(generate(), mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=traffic_predictions.csv"})