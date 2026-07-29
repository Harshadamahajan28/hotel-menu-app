from flask import Flask, render_template, request, jsonify
from datetime import date

app = Flask(__name__)

# ऑर्डर्स साठवण्यासाठी लिस्ट
orders_db = []

# १. होम पेज (ग्राहक स्क्रीन)
@app.route('/')
def home():
    return render_template('index.html')

# २. मेन्यू पेज
@app.route('/menu')
def menu():
    return render_template('menu.html')

# ३. लॉगिन पेज
@app.route('/login')
def login():
    return render_template('login.html')

# ४. रजिस्ट्रेशन पेज
@app.route('/register')
def register():
    return render_template('register.html')

# ५. ग्राहकाची ऑर्डर स्वीकारणारा API Route
@app.route('/api/place-order', methods=['POST'])
def place_order():
    data = request.get_json()
    
    order_id = len(orders_db) + 1
    
    new_order = {
        'id': order_id,
        'customer_name': data.get('name', 'GUEST'),
        'phone': data.get('phone', ''),
        'table_no': data.get('table_no', 'Table 1'),
        'items': data.get('items', []),
        'total': data.get('total', 0),
        'status': 'Pending ⏳'
    }
    
    orders_db.append(new_order)
    return jsonify({'success': True, 'order_id': order_id})

# ६. ॲडमिन पॅनेल मुख्य पान
@app.route('/admin')
def admin():
    return render_template('admin.html')

# ७. ऑर्डर्सचा डेटा मिळवण्यासाठी JSON API
@app.route('/api/orders')
def get_orders():
    return jsonify(orders_db)

# ८. किचन/मॅनेजरसाठी स्टेटस बदलणारा API
@app.route('/api/update-status/<int:order_id>', methods=['POST'])
def update_status(order_id):
    data = request.get_json()
    new_status = data.get('status')
    
    for order in orders_db:
        if order['id'] == order_id:
            order['status'] = new_status
            return jsonify({'success': True})
            
    return jsonify({'success': False, 'error': 'Order not found'})

# ९. Daily Order Analytics Route (main च्या वर)
@app.route('/analytics')
def analytics():
    today = date.today().strftime("%Y-%m-%d")
    total_sales = 4500
    total_orders = 18
    popular_item = "Paneer Butter Masala"
    
    return render_template('analytics.html', 
                           sales=total_sales, 
                           orders=total_orders, 
                           top_item=popular_item)

# सर्व रूट्स संपल्यानंतर शेवटी हेच राहील
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
