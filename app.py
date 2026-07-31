from flask import Flask, render_template, request, jsonify
import datetime

app = Flask(__name__)

orders = []
order_counter = 1

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

# API: नवीन ऑर्डर सबमिट करण्यासाठी (तारीख YYYY-MM-DD फॉरमॅटमध्ये साठवली जाईल)
@app.route('/api/order', methods=['POST'])
def place_order():
    global order_counter
    data = request.json
    if not data or 'customer_name' not in data or 'table_no' not in data or 'items' not in data:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400

    order_id = f"{order_counter}"
    order_counter += 1
    
    # वेळ आणि तारीख स्वतंत्रपणे साठवणे
    now_obj = datetime.datetime.now()
    date_str = now_obj.strftime("%Y-%m-%d")  # उदा. 2026-07-31
    time_str = now_obj.strftime("%I:%M %p")   # उदा. 08:30 PM

    new_order = {
        'id': order_id,
        'customer_name': data['customer_name'],
        'table_no': data['table_no'],
        'phone': data.get('phone', 'N/A'),
        'items': data['items'],
        'total': float(data['total']),
        'date': date_str,
        'time': time_str,
        'status': 'Pending ⏳'
    }

    orders.insert(0, new_order)
    return jsonify({'success': True, 'order_id': order_id, 'order': new_order})

@app.route('/api/admin/orders', methods=['GET'])
def get_admin_orders():
    return jsonify({'success': True, 'orders': orders})

@app.route('/api/admin/complete_order', methods=['POST'])
def complete_order():
    data = request.json
    order_id = str(data.get('order_id'))
    for ord in orders:
        if str(ord['id']) == order_id:
            ord['status'] = 'Completed ✅'
            return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Order not found'}), 404

# 🎯 Date-wise Analytics API (निवडलेल्या तारखेनुसार डेटा फिल्टर करणे)
@app.route('/api/admin/analytics_data', methods=['GET'])
def get_analytics():
    selected_date = request.args.get('date')  # URL मधून तारीख घेणे
    
    # जर तारीख पाठवली असेल तर त्या तारखेच्या ऑर्डर्स फिल्टर करा
    if selected_date:
        filtered_orders = [ord for ord in orders if ord.get('date') == selected_date]
    else:
        filtered_orders = orders

    total_orders = len(filtered_orders)
    total_revenue = sum(ord['total'] for ord in filtered_orders)
    pending_orders = sum(1 for ord in filtered_orders if 'Pending' in ord['status'])
    completed_orders = sum(1 for ord in filtered_orders if 'Completed' in ord['status'])

    return jsonify({
        'success': True,
        'selected_date': selected_date,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'orders': filtered_orders
    })

if __name__ == '__main__':
    app.run(debug=True)
