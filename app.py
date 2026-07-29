from flask import Flask, render_template, request, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)

DATA_FILE = 'orders.json'

# Helper function to load orders from file
def load_orders():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []

# Helper function to save orders to file
def save_orders(orders):
    with open(DATA_FILE, 'w') as f:
        json.dump(orders, f, indent=4)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/admin')
def admin():
    orders = load_orders()
    return render_template('admin.html', orders=orders)

@app.route('/analytics')
def analytics():
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
