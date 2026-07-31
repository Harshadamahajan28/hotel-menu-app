import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient
import datetime

app = Flask(__name__)
app.secret_key = "royal_spice_secret_key"

# Read MONGO_URI safely from Render Environment Variables
MONGO_URI = os.getenv("MONGO_URI")

use_mongodb = False
orders_collection = None
reviews_collection = None

if MONGO_URI:
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client['hotel_database']
        orders_collection = db['orders']
        reviews_collection = db['reviews']
        print("SUCCESS: Connected to MongoDB Database!")
        use_mongodb = True
    except Exception as e:
        print(f"ERROR: Could not connect to MongoDB: {e}")
        use_mongodb = False
else:
    print("WARNING: MONGO_URI Environment Variable is missing!")

# Fallback Memory (Only if DB Fails)
memory_orders = []
memory_reviews = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == '1234':
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error="Invalid Credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/analytics')
def analytics():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    return render_template('analytics.html')

# API: Place New Order
@app.route('/api/order', methods=['POST'])
def place_order():
    data = request.json
    now = datetime.datetime.now()
    
    order_data = {
        "id": int(now.timestamp()),
        "table_no": data.get('table_no', 'N/A'),
        "customer_name": data.get('customer_name', 'Guest'),
        "items": data.get('items', []),
        "total": data.get('total', 0),
        "status": "Pending",
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%I:%M %p")
    }

    if use_mongodb:
        orders_collection.insert_one(order_data)
        if '_id' in order_data:
            del order_data['_id']
    else:
        memory_orders.append(order_data)

    return jsonify({"success": True, "message": "Order placed successfully!", "order": order_data})

# API: Get All Orders & Analytics Stats
@app.route('/api/orders', methods=['GET'])
def get_orders():
    if use_mongodb:
        orders = list(orders_collection.find({}, {'_id': 0}).sort("id", -1))
    else:
        orders = sorted(memory_orders, key=lambda x: x['id'], reverse=True)

    total_revenue = sum(o.get('total', 0) for o in orders if o.get('status') == 'Completed')
    total_orders = len(orders)
    completed_orders = sum(1 for o in orders if o.get('status') == 'Completed')

    return jsonify({
        "orders": orders,
        "stats": {
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "completed_orders": completed_orders
        }
    })

# API: Update Order Status
@app.route('/api/update-status', methods=['POST'])
def update_status():
    data = request.json
    order_id = int(data.get('order_id'))
    new_status = data.get('status')

    if use_mongodb:
        orders_collection.update_one({"id": order_id}, {"$set": {"status": new_status}})
    else:
        for o in memory_orders:
            if o['id'] == order_id:
                o['status'] = new_status
                break

    return jsonify({"success": True})

# API: Submit Review
@app.route('/api/review', methods=['POST'])
def submit_review():
    data = request.json
    now = datetime.datetime.now()
    
    review_data = {
        "name": data.get('name', 'Anonymous'),
        "rating": int(data.get('rating', 5)),
        "comment": data.get('comment', ''),
        "date": now.strftime("%Y-%m-%d %I:%M %p")
    }

    if use_mongodb:
        reviews_collection.insert_one(review_data)
    else:
        memory_reviews.append(review_data)

    return jsonify({"success": True})

# API: Get Reviews
@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    if use_mongodb:
        reviews = list(reviews_collection.find({}, {'_id': 0}))
    else:
        reviews = memory_reviews

    avg_rating = 5.0
    if reviews:
        avg_rating = round(sum(r.get('rating', 5) for r in reviews) / len(reviews), 1)

    return jsonify({"reviews": reviews, "avg_rating": avg_rating})

if __name__ == '__main__':
    app.run(debug=True)
