from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = 'royal_spice_secret_key_2026'

ADMIN_PASSWORD = 'admin123'

# 🌐 MongoDB Connection Setup
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/hotel_db")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['hotel_database']
    orders_collection = db['orders']
    reviews_collection = db['reviews']
except Exception as e:
    print("Database Connection Error:", e)

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
    try:
        orders = list(orders_collection.find({}, {'_id': 0}))
        orders.sort(key=lambda x: x.get('id', 0), reverse=True)
    except Exception as e:
        orders = []
    return render_template('admin.html', orders=orders)

@app.route('/analytics')
def analytics():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('analytics.html')

@app.route('/api/place-order', methods=['POST'])
def place_order():
    try:
        data = request.get_json(silent=True) or {}
        
        # Safe count of documents
        try:
            total_orders = orders_collection.count_documents({})
        except:
            total_orders = 0

        order_id = total_orders + 1
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        new_order = {
            'id': int(order_id),
            'customer_name': str(data.get('name', 'Guest')),
            'table_no': str(data.get('table_no', 'N/A')),
            'phone': str(data.get('phone', 'N/A')),
            'items': data.get('items', []),
            'total': float(data.get('total', 0)),
            'status': 'Pending',
            'date': today_str,
            'time': datetime.now().strftime('%I:%M %p')
        }
        
        orders_collection.insert_one(new_order)
        return jsonify({'success': True, 'order_id': order_id})
    except Exception as e:
        print("Place Order Error:", str(e))
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    target_date = request.args.get('date')
    try:
        if target_date:
            orders = list(orders_collection.find({'date': target_date}, {'_id': 0}))
        else:
            orders = list(orders_collection.find({}, {'_id': 0}))

        orders.sort(key=lambda x: x.get('id', 0), reverse=True)

        total_revenue = sum(float(order.get('total', 0)) for order in orders if order.get('status') == 'Completed')
        total_orders = len(orders)
        completed_orders = len([o for o in orders if o.get('status') == 'Completed'])
        pending_orders = len([o for o in orders if o.get('status') == 'Pending'])

        return jsonify({
            'orders': orders,
            'stats': {
                'total_revenue': total_revenue,
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'pending_orders': pending_orders
            }
        })
    except Exception as e:
        return jsonify({'orders': [], 'stats': {'total_revenue': 0, 'total_orders': 0, 'completed_orders': 0, 'pending_orders': 0}})

@app.route('/api/update-status', methods=['POST'])
def update_status():
    try:
        data = request.get_json(silent=True) or {}
        order_id = int(data.get('order_id'))
        new_status = str(data.get('status'))
        
        result = orders_collection.update_one({'id': order_id}, {'$set': {'status': new_status}})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/submit-review', methods=['POST'])
def submit_review():
    try:
        data = request.get_json(silent=True) or {}
        new_review = {
            'name': str(data.get('name', 'Anonymous')),
            'rating': int(data.get('rating', 5)),
            'comment': str(data.get('comment', '')),
            'date': datetime.now().strftime('%Y-%m-%d %I:%M %p')
        }
        reviews_collection.insert_one(new_review)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    try:
        reviews = list(reviews_collection.find({}, {'_id': 0}))
        avg_rating = round(sum(r.get('rating', 5) for r in reviews) / len(reviews), 1) if reviews else 5.0
        return jsonify({
            'reviews': reviews,
            'avg_rating': avg_rating,
            'total_reviews': len(reviews)
        })
    except Exception as e:
        return jsonify({'reviews': [], 'avg_rating': 5.0, 'total_reviews': 0})

if __name__ == '__main__':
    app.run(debug=True)
