from flask import Flask, render_template, request, jsonify
import psycopg2
import datetime
import os

app = Flask(__name__)

# 🔗 Neon PostgreSQL Database Connection URL (Environment Variable or Default)
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    "postgresql://neondb_owner:npg_tp1sR2xCcloF@ep-solitary-water-ayecuz6l.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"
)

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Database Table ऑटोमॅटिक तयार करणे
def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
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
        cursor.close()
        conn.close()
    except Exception as e:
        print("Database Init Error:", e)

init_db()

# अचूक भारतीय वेळ (IST: UTC + 5:30)
def get_indian_time():
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
    return ist_now.strftime("%Y-%m-%d"), ist_now.strftime("%I:%M %p")

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

@app.route('/api/order', methods=['POST'])
def place_order():
    data = request.json
    if not data or 'customer_name' not in data or 'table_no' not in data or 'items' not in data:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400

    date_str, time_str = get_indian_time()
    items_summary = ", ".join([f"{item['name']} (x{item['qty']})" for item in data['items']])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (customer_name, table_no, phone, items, total, order_date, order_time, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
    ''', (data['customer_name'], data['table_no'], data.get('phone', 'N/A'), items_summary, float(data['total']), date_str, time_str, 'Pending ⏳'))
    
    order_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'success': True, 'order_id': order_id, 'date': date_str, 'time': time_str})

# 🗑️ १० मिनिटांचे Security Check असलेले Order Delete/Cancel API Route
@app.route('/api/order/cancel/<int:order_id>', methods=['DELETE'])
def cancel_order(order_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # १. ऑर्डरची तारीख व वेळ आधी शोधा
        cursor.execute('SELECT order_date, order_time FROM orders WHERE id = %s', (order_id,))
        order = cursor.fetchone()
        
        if not order:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'ऑर्डर सापडली नाही!'}), 404

        order_date_str, order_time_str = str(order[0]), str(order[1])
        
        # २. वेळेची तुलना करण्यासाठी वेळ ऑब्जेक्टमध्ये रूपांतर करा
        order_datetime_str = f"{order_date_str} {order_time_str}"
        order_datetime = datetime.datetime.strptime(order_datetime_str, "%Y-%m-%d %I:%M %p")
        
        # आत्ताची भारतीय वेळ
        utc_now = datetime.datetime.now(datetime.timezone.utc)
        ist_now = (utc_now + datetime.timedelta(hours=5, minutes=30)).replace(tzinfo=None)

        # वेळेतील फरक (मिनिटांमध्ये)
        time_diff_minutes = (ist_now - order_datetime).total_seconds() / 60

        # 🛑 १० मिनिटांपेक्षा जास्त वेळ झाला असल्यास Cancel करू देऊ नका
        if time_diff_minutes > 10:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False, 
                'error': 'ऑर्डर देऊन १० मिनिटांपेक्षा जास्त वेळ झाला आहे. किचनमध्ये स्वयंपाक सुरू असल्याने आता ऑर्डर डिलीट करता येणार नाही!'
            }), 400

        # ✅ १० मिनिटांच्या आत असल्यास डिलीट करा
        cursor.execute('DELETE FROM orders WHERE id = %s', (order_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Order deleted successfully'})
        
    except Exception as e:
        print("Delete Order Error:", e)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/orders', methods=['GET'])
def get_admin_orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, customer_name, table_no, phone, items, total, order_date, order_time, status FROM orders ORDER BY id DESC')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    orders_list = []
    for row in rows:
        orders_list.append({
            'id': row[0], 'customer_name': row[1], 'table_no': row[2], 'phone': row[3],
            'items_str': row[4], 'total': row[5], 'date': row[6], 'time': row[7], 'status': row[8]
        })

    return jsonify({'success': True, 'orders': orders_list})

@app.route('/api/admin/complete_order', methods=['POST'])
def complete_order():
    data = request.json
    order_id = data.get('order_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET status = %s WHERE id = %s', ('Completed ✅', order_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/admin/analytics_data', methods=['GET'])
def get_analytics():
    selected_date = request.args.get('date')
    
    conn = get_db_connection()
    cursor = conn.cursor()

    if selected_date:
        cursor.execute('SELECT id, customer_name, table_no, items, total, order_date, order_time, status FROM orders WHERE order_date = %s ORDER BY id DESC', (selected_date,))
    else:
        cursor.execute('SELECT id, customer_name, table_no, items, total, order_date, order_time, status FROM orders ORDER BY id DESC')

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    orders_list = []
    total_revenue, pending_count, completed_count = 0, 0, 0

    for row in rows:
        total_revenue += float(row[4]) if row[4] else 0.0
        status_val = str(row[7]) if row[7] else ''
        
        if 'Pending' in status_val: pending_count += 1
        elif 'Completed' in status_val: completed_count += 1

        orders_list.append({
            'id': row[0], 'customer_name': row[1], 'table_no': row[2], 'items': row[3],
            'total': row[4], 'date': row[5], 'time': row[6], 'status': row[7]
        })

    return jsonify({
        'success': True, 'selected_date': selected_date,
        'total_orders': len(orders_list), 'total_revenue': total_revenue,
        'pending_orders': pending_count, 'completed_orders': completed_count,
        'orders': orders_list
    })

if __name__ == '__main__':
    app.run(debug=True)
