from flask import Flask, render_template, request, jsonify
import sqlite3
import datetime
import pytz  # Timezone अचूक करण्यासाठी

app = Flask(__name__)

# भारतीय वेळ (IST) मिळवण्यासाठी Function
def get_indian_time():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.datetime.now(ist)
    date_str = now.strftime("%Y-%m-%d")    # YYYY-MM-DD
    time_str = now.strftime("%I:%M %p")    # 12-Hour format (उदा. 04:00 PM)
    return date_str, time_str

# SQLite Database तयार करणे
def init_db():
    conn = sqlite3.connect('hotel.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            table_no TEXT,
            phone TEXT,
            items TEXT,
            total REAL,
            order_date TEXT,
            order_time TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

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

# API: नवीन ऑर्डर (Perfect IST Time सह सेव्ह करणे)
@app.route('/api/order', methods=['POST'])
def place_order():
    data = request.json
    if not data or 'customer_name' not in data or 'table_no' not in data or 'items' not in data:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400

    # ⏰ अचूक भारतीय तारीख आणि वेळ
    date_str, time_str = get_indian_time()

    items_summary = ", ".join([f"{item['name']} (x{item['qty']})" for item in data['items']])

    conn = sqlite3.connect('hotel.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (customer_name, table_no, phone, items, total, order_date, order_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data['customer_name'], data['table_no'], data.get('phone', 'N/A'), items_summary, float(data['total']), date_str, time_str, 'Pending ⏳'))
    
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'order_id': order_id, 'date': date_str, 'time': time_str})

# API: Admin साठी ऑर्डर्स
@app.route('/api/admin/orders', methods=['GET'])
def get_admin_orders():
    conn = sqlite3.connect('hotel.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, customer_name, table_no, phone, items, total, order_date, order_time, status FROM orders ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()

    orders_list = []
    for row in rows:
        orders_list.append({
            'id': row[0],
            'customer_name': row[1],
            'table_no': row[2],
            'phone': row[3],
            'items_str': row[4],
            'total': row[5],
            'date': row[6],
            'time': row[7],
            'status': row[8]
        })

    return jsonify({'success': True, 'orders': orders_list})

# API: Complete Order
@app.route('/api/admin/complete_order', methods=['POST'])
def complete_order():
    data = request.json
    order_id = data.get('order_id')
    
    conn = sqlite3.connect('hotel.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET status = ? WHERE id = ?', ('Completed ✅', order_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# API: Date-wise Analytics
@app.route('/api/admin/analytics_data', methods=['GET'])
def get_analytics():
    selected_date = request.args.get('date')
    
    conn = sqlite3.connect('hotel.db')
    cursor = conn.cursor()

    if selected_date:
        cursor.execute('SELECT id, customer_name, table_no, items, total, order_date, order_time, status FROM orders WHERE order_date = ? ORDER BY id DESC', (selected_date,))
    else:
        cursor.execute('SELECT id, customer_name, table_no, items, total, order_date, order_time, status FROM orders ORDER BY id DESC')

    rows = cursor.fetchall()
    conn.close()

    orders_list = []
    total_revenue = 0
    pending_count = 0
    completed_count = 0

    for row in rows:
        total_revenue += row[4]
        if 'Pending' in row[7]:
            pending_count += 1
        elif 'Completed' in row[7]:
            completed_count += 1

        orders_list.append({
            'id': row[0],
            'customer_name': row[1],
            'table_no': row[2],
            'items': row[3],
            'total': row[4],
            'date': row[5],
            'time': row[6],
            'status': row[7]
        })

    return jsonify({
        'success': True,
        'selected_date': selected_date,
        'total_orders': len(orders_list),
        'total_revenue': total_revenue,
        'pending_orders': pending_count,
        'completed_orders': completed_count,
        'orders': orders_list
    })

if __name__ == '__main__':
    app.run(debug=True)
