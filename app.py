from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = 'royal_spice_secret_key_2026'  # Session साठी गुपित की

DATA_FILE = 'orders.json'
ADMIN_PASSWORD = 'theroyalspice'  # 🔑 तुमचा Admin/Analytics चा पासवर्ड इथे बदला

def load_orders():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def save_orders(orders):
    with open(DATA_FILE, 'w') as f:
        json.dump(orders, f, indent=4)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')

# 🔐 Login Page Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = 'Invalid Password! Please try again.'
    return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Login - The Royal Spice</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
            <style>
                body {{ background-color: #0d1117; color: white; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
                .login-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 30px; width: 100%; max-width: 380px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="login-card">
                <h3 class="text-warning mb-3">👑 Admin Access</h3>
                <p class="text-secondary small">Enter password to access Kitchen & Analytics</p>
                {"<div class='alert alert-danger py-2'>"+error+"</div>" if error else ""}
                <form method="POST">
                    <input type="password" name="password" class="form-control mb-3 text-center" placeholder="Enter Password" required autofocus>
                    <button type="submit" class="btn btn-warning w-100 fw-bold">Login</button>
                </form>
                <a href="/" class="btn btn-link text-secondary text-decoration-none mt-3 small">← Back to Home</a>
            </div>
        </body>
        </html>
    '''

# 🚪 Logout Route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# 🔒 Protected Admin Route
@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    orders = load_orders()
    return render_template('admin.html', orders=orders)

# 🔒 Protected Analytics Route
@app.route('/analytics')
def analytics():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('analytics.html')

@app.route('/api/place-order', methods=['POST'])
def place_order():
    orders = load_orders()
    data = request.json
    order_id = len(orders) + 1
    
    new_order = {
        'id': order_id,
        'customer_name': data.get('name', 'Guest'),
        'table_no': data.get('table_no', 'N/A'),
        'phone': data.get('phone', 'N/A'),
        'items': data.get('items', []),
        'total': data.get('total', 0),
        'status': 'Pending',
        'time': datetime.now().strftime('%I:%M %p')
    }
    
    orders.insert(0, new_order)
    save_orders(orders)
    return jsonify({'success': True, 'order_id': new_order['id']})

@app.route('/api/orders', methods=['GET'])
def get_orders():
    orders = load_orders()
    total_revenue = sum(order['total'] for order in orders if order['status'] == 'Completed')
    total_orders = len(orders)
    completed_orders = len([o for o in orders if o['status'] == 'Completed'])
    pending_orders = len([o for o in orders if o['status'] == 'Pending'])

    return jsonify({
        'orders': orders,
        'stats': {
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'pending_orders': pending_orders
        }
    })

@app.route('/api/update-status', methods=['POST'])
def update_status():
    orders = load_orders()
    data = request.json
    order_id = data.get('order_id')
    new_status = data.get('status')
    
    for order in orders:
        if order['id'] == order_id:
            order['status'] = new_status
            save_orders(orders)
            return jsonify({'success': True})
            
    return jsonify({'success': False})

if __name__ == '__main__':
    app.run(debug=True)
