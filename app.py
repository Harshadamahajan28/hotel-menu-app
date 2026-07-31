from flask import Flask, render_template, request, jsonify
import datetime

app = Flask(__name__)

# ऑर्डर्स साठवण्यासाठी मेमरी
orders = []
order_counter = 1  # Order ID 1 पासून सुरू होईल

@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

# API: नवीन ऑर्डर सबमिट करण्यासाठी (#1, #2, #3...)
@app.route('/api/order', methods=['POST'])
def place_order():
    global order_counter
    data = request.json
    if not data or 'customer_name' not in data or 'table_no' not in data or 'items' not in data:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400

    order_id = f"{order_counter}"
    order_counter += 1
    now = datetime.datetime.now().strftime("%I:%M %p, %d %b %Y")

    new_order = {
        'id': order_id,
        'customer_name': data['customer_name'],
        'table_no': data['table_no'],
        'phone': data.get('phone', 'N/A'),
        'items': data['items'],
        'total': data['total'],
        'time': now,
        'status': 'Pending ⏳'
    }

    orders.insert(0, new_order)
    return jsonify({'success': True, 'order_id': order_id, 'order': new_order})

# API: Admin साठी सर्व ऑर्डर्स मिळवण्यासाठी
@app.route('/api/admin/orders', methods=['GET'])
def get_admin_orders():
    return jsonify({'success': True, 'orders': orders})

# API: ऑर्डर स्टेटस बदलण्यासाठी (Pending -> Completed)
@app.route('/api/admin/complete_order', methods=['POST'])
def complete_order():
    data = request.json
    order_id = str(data.get('order_id'))
    
    for ord in orders:
        if str(ord['id']) == order_id:
            ord['status'] = 'Completed ✅'
            return jsonify({'success': True})
            
    return jsonify({'success': False, 'error': 'Order not found'}), 404

# API: Analytics साठी डेटा मिळवण्यासाठी
@app.route('/api/admin/analytics_data', methods=['GET'])
def get_analytics():
    total_orders = len(orders)
    total_revenue = sum(ord['total'] for ord in orders)
    pending_orders = sum(1 for ord in orders if 'Pending' in ord['status'])
    completed_orders = sum(1 for ord in orders if 'Completed' in ord['status'])

    return jsonify({
        'success': True,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders
    })

if __name__ == '__main__':
    app.run(debug=True)
