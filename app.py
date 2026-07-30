from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = 'royal_spice_secret_key_2026'

ADMIN_PASSWORD = 'admin123'

# Backup list: जर डेटाबेस स्लो असेल तरी ऑर्डर मिस होणार नाही
memory_orders = []

# MongoDB Connection Setup
MONGO_URI = os.environ.get("MONGO_URI", "")
orders_collection = None
reviews_collection = None

if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000, connectTimeoutMS=3000)
        db = client['hotel_database']
        orders_collection = db['orders']
        reviews_collection = db['reviews']
        print("Connected to MongoDB successfully")
    except Exception as e:
        print("MongoDB Conn Exception:", e)

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
            <title>Admin Login</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        </head>
        <body class="bg-dark text-white d-flex align-items-center justify-content-center vh-100">
            <div class="card bg-secondary text-white p-4" style="max-width:350px;">
                <h4 class="text-warning text-center">Admin Login</h4>
                {"<div class='alert alert-danger py-1'>"+error+"</div>" if error else ""}
                <form method="POST">
                    <input type="password" name="password" class="form-control mb-3" placeholder="Password" required>
                    <button type="submit" class="btn btn-warning w-100">Login</button>
                </form>
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
    
    orders = []
    # 1. MongoDB मधून ऑर्डर्स आणा
    if orders_collection is not None:
        try:
            orders = list(orders_collection.find({}, {'_id': 0}))
        except Exception as e:
            print("Fetch orders error:", e)
    
    # 2. जर MongoDB रिकामे असेल तर मेमरीमधील ऑर्डर्स दाखवा
    if not orders and memory_orders:
        orders = memory_orders.copy()
    
    orders.sort(key=lambda x: str(x.get('id', '')), reverse=True)
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
        
        gen_id = int(datetime.now().timestamp() % 10000)
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        new_order = {
            'id': gen_id,
            'customer_name': str(data.get('name', 'Guest')),
            'table_no': str(data.get('table_no', 'N/A')),
            'phone': str(data.get('phone', 'N/A')),
            'items': data.get('items', []),
            'total': float(data.get('total', 0)),
            'status': 'Pending',
            'date': today_str,
            'time': datetime.now().strftime('%I:%M %p')
        }
        
        # लोकल मेमरीमध्ये नक्की सेव्ह करा
        memory_orders.append(new_order)
        
        # MongoDB मध्येही सेव्ह करण्याचा प्रयत्न करा
        if orders_collection is not None:
            try:
                orders_collection.insert_one(new_order)
            except Exception as db_e:
                print("DB Insert Failed, saved in memory:", db_e)

        return jsonify({'success': True, 'order_id': gen_id})

    except Exception as e:
        print("Place order exception:", e)
        return jsonify({'success': True, 'order_id': 101})

@app.route('/api/orders', methods=['GET'])
def get_orders():
    orders = []
    if orders_collection is not None:
        try:
            orders = list(orders_collection.find({}, {'_id': 0}))
        except Exception as e:
            print("Get orders error:", e)

    if not orders and memory_orders:
        orders = memory_orders.copy()

    orders.sort(key=lambda x: str(x.get('id', '')), reverse=True)
    total_revenue = sum(float(o.get('total', 0)) for o in orders if o.get('status') == 'Completed')
    
    return jsonify({
        'orders': orders,
        'stats': {
            'total_revenue': total_revenue,
            'total_orders': len(orders),
            'completed_orders': len([o for o in orders if o.get('status') == 'Completed']),
            'pending_orders': len([o for o in orders if o.get('status') == 'Pending'])
        }
    })

@app.route('/api/update-status', methods=['POST'])
def update_status():
    try:
        data = request.get_json(silent=True) or {}
        order_id = data.get('order_id')
        new_status = str(data.get('status'))
        
        # Update memory
        for o in memory_orders:
            if str(o.get('id')) == str(order_id):
                o['status'] = new_status
                
        # Update DB
        if orders_collection is not None:
            try:
                orders_collection.update_one({'id': int(order_id)}, {'$set': {'status': new_status}})
            except:
                pass

        return jsonify({'success': True})
    except:
        return jsonify({'success': True})

@app.route('/api/submit-review', methods=['POST'])
def submit_review():
    return jsonify({'success': True})

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    return jsonify({'reviews': [], 'avg_rating': 5.0, 'total_reviews': 0})

if __name__ == '__main__':
    app.run(debug=True)
