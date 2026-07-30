from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = 'royal_spice_secret_key_2026'

DATA_FILE = 'orders.json'
REVIEWS_FILE = 'reviews.json'
ADMIN_PASSWORD = 'admin123'

def load_data(filename):
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_data(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving data: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')

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

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    orders = load_data(DATA_FILE)
    return render_template('admin.html', orders=orders)

@app.route('/analytics')
def analytics():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('analytics.html')

@app.route('/api/place-order', methods=['POST'])
def place_order():
    orders = load_data(DATA_FILE)
    data = request.json
    order_id = len(orders) + 1
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    new_order = {
        'id': order_id,
        'customer_name': data.get('name', 'Guest'),
        'table_no': data.get('table_no', 'N/A'),
        'phone': data.get('phone', 'N/A'),
        'items': data.get('items', []),
        'total': data.get('total', 0),
        'status': 'Pending',
        'date': today_str,
        'time': datetime.now().strftime('%I:%M %p')
    }
    
    orders.insert(0, new_order)
    save_data(DATA_FILE, orders)
    return jsonify({'success': True, 'order_id': new_order['id']})

@app.route('/api/orders', methods=['GET'])
def get_orders():
    orders = load_data(DATA_FILE)
    target_date = request.args.get('date')

    filtered_orders = orders
    if target_date:
        filtered_orders = [o for o in orders if o.get('date', '') == target_date]

    total_revenue = sum(order['total'] for order in filtered_orders if order['status'] == 'Completed')
    total_orders = len(filtered_orders)
    completed_orders = len([o for o in filtered_orders if o['status'] == 'Completed'])
    pending_orders = len([o for o in filtered_orders if o['status'] == 'Pending'])

    return jsonify({
        'orders': filtered_orders,
        'stats': {
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'pending_orders': pending_orders
        }
    })

@app.route('/api/update-status', methods=['POST'])
def update_status():
    orders = load_data(DATA_FILE)
    data = request.json
    order_id = data.get('order_id')
    new_status = data.get('status')
    
    for order in orders:
        if order['id'] == order_id:
            order['status'] = new_status
            save_data(DATA_FILE, orders)
            return jsonify({'success': True})
            
    return jsonify({'success': False})

@app.route('/api/submit-review', methods=['POST'])
def submit_review():
    reviews = load_data(REVIEWS_FILE)
    data = request.json
    
    new_review = {
        'name': data.get('name', 'Anonymous'),
        'rating': int(data.get('rating', 5)),
        'comment': data.get('comment', ''),
        'date': datetime.now().strftime('%Y-%m-%d %I:%M %p')
    }
    reviews.insert(0, new_review)
    save_data(REVIEWS_FILE, reviews)
    return jsonify({'success': True})

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    reviews = load_data(REVIEWS_FILE)
    avg_rating = round(sum(r['rating'] for r in reviews) / len(reviews), 1) if reviews else 5.0
    return jsonify({
        'reviews': reviews,
        'avg_rating': avg_rating,
        'total_reviews': len(reviews)
    })

if __name__ == '__main__':
    app.run(debug=True)
