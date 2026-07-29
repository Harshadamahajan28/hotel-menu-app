from flask import Flask, render_template, request, jsonify
from datetime import date, datetime, timedelta

app = Flask(__name__)

# ऑर्डर्स डेटाबेस (In-Memory DB with sample past data)
orders_db = [
    {
        'id': 1,
        'customer_name': 'Rahul Sharma',
        'phone': '9876543210',
        'table_no': 'Table 3',
        'items': [{'name': 'Paneer Butter Masala', 'qty': 2, 'taste': 'Medium'}, {'name': 'Roti', 'qty': 4, 'taste': 'Plain'}],
        'total': 480,
        'status': 'Completed ✅',
        'created_at': (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M")
    }
]

# १. होम पेज
@app.route('/')
def home():
    return render_template('index.html')

# २. मेन्यू पेज (Taste Options सह)
@app.route('/menu')
def menu():
    return render_template('menu.html')

# ३. लॉगिन व नोंदणी
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

# ४. नवीन ऑर्डर स्वीकारणारा API (Taste & Quantity सह)
@app.route('/api/place-order', methods=['POST'])
def place_order():
    data = request.get_json()
    
    order_id = len(orders_db) + 1
    new_order = {
        'id': order_id,
        'customer_name': data.get('name', 'GUEST'),
        'phone': data.get('phone', ''),
        'table_no': data.get('table_no', 'Table 1'),
        'items': data.get('items', []),  # [{'name': '...', 'qty': 1, 'taste': 'Spicy'}]
        'total': data.get('total', 0),
        'status': 'Pending ⏳',
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    orders_db.append(new_order)
    return jsonify({'success': True, 'order_id': order_id})

# ५. किचन डिस्प्ले स्क्रीन (Live Orders for Kitchen Staff)
@app.route('/kitchen')
def kitchen():
    return render_template('kitchen.html')

# ६. ॲडमिन पॅनेल मुख्य पान
@app.route('/admin')
def admin():
    return render_template('admin.html')

# ७. गेल्या १५ दिवसांच्या ऑर्डर्स मिळवणारा API
@app.route('/api/orders')
def get_orders():
    # गेल्या १५ दिवसांचा डेटा फिल्टर करणे
    fifteen_days_ago = datetime.now() - timedelta(days=15)
    
    filtered_orders = []
    for order in orders_db:
        order_date = datetime.strptime(order['created_at'], "%Y-%m-%d %H:%M")
        if order_date >= fifteen_days_ago:
            filtered_orders.append(order)
            
    return jsonify(filtered_orders)

# ८. ऑर्डर स्टेटस अपडेट API (Pending -> Cooking -> Ready)
@app.route('/api/update-status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    data = request.get_json()
    new_status = data.get('status')
    
    for order in orders_db:
        if order['id'] == order_id:
            order['status'] = new_status
            return jsonify({'success': True})
            
    return jsonify({'success': False, 'error': 'Order not found'})

# ९. १५ दिवसांचे Analytics पेज
@app.route('/analytics')
def analytics():
    total_sales = sum(order.get('total', 0) for order in orders_db)
    total_orders = len(orders_db)
    
    item_counts = {}
    for order in orders_db:
        for item in order.get('items', []):
            item_name = item.get('name', 'Dish')
            item_counts[item_name] = item_counts.get(item_name, 0) + item.get('qty', 1)
            
    popular_item = max(item_counts, key=item_counts.get) if item_counts else "No Sales Yet"
    
    return render_template('analytics.html', 
                           sales=total_sales, 
                           orders=total_orders, 
                           top_item=popular_item,
                           chart_data=[total_sales])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
