from flask import Flask, render_template, request, jsonify
import datetime
import random

app = Flask(__name__)

# इन-मेमरी डेटाबेस (ऑर्डर आणि रिव्ह्यू साठवण्यासाठी)
orders = []
reviews = []

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

# API: नवीन ऑर्डर सबमिट करण्यासाठी
@app.route('/api/order', methods=['POST'])
def place_order():
    data = request.json
    if not data or 'customer_name' not in data or 'table_no' not in data or 'items' not in data:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400

    order_id = f"ORD-{random.randint(1000, 9999)}"
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

    orders.insert(0, new_order)  # नवीन ऑर्डर वर दिसेल
    return jsonify({'success': True, 'order_id': order_id, 'order': new_order})

# API: Admin साठी सर्व ऑर्डर्स मिळवण्यासाठी
@app.route('/api/admin/orders', methods=['GET'])
def get_admin_orders():
    return jsonify({'success': True, 'orders': orders})

# API: रिव्ह्यू सबमिट करण्यासाठी
@app.route('/api/review', methods=['POST'])
def submit_review():
    data = request.json
    reviews.append(data)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
