import os
import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, jsonify

app = Flask(__name__) 

# 🔗 Database Connection (Ensure DATABASE_URL is set in environment variables)
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set!")
    return psycopg2.connect(DATABASE_URL)

# Full 75 Menu Items List
DEFAULT_FULL_MENU = [
    # --- Starters (15 Items) ---
    ('Paneer Tikka', 130.0, 240.0, 'Starters'),
    ('Paneer Chilli', 135.0, 250.0, 'Starters'),
    ('Hara Bhara Kabab', 100.0, 190.0, 'Starters'),
    ('Veg Crispy', 110.0, 200.0, 'Starters'),
    ('Veg Manchurian Dry', 110.0, 200.0, 'Starters'),
    ('Mushroom Tikka', 140.0, 260.0, 'Starters'),
    ('Cheese Corn Balls', 130.0, 240.0, 'Starters'),
    ('Chicken Tikka', 160.0, 300.0, 'Starters'),
    ('Chicken Tandoori', 220.0, 420.0, 'Starters'),
    ('Chicken Chilli', 150.0, 280.0, 'Starters'),
    ('Chicken Lollipop', 140.0, 260.0, 'Starters'),
    ('Chicken Seekh Kebab', 170.0, 320.0, 'Starters'),
    ('Chicken Malai Tikka', 180.0, 330.0, 'Starters'),
    ('Fish Fry', 190.0, 360.0, 'Starters'),
    ('Prawns Koliwada', 210.0, 390.0, 'Starters'),

    # --- Main Course (15 Items) ---
    ('Paneer Butter Masala', 140.0, 260.0, 'Main Course'),
    ('Paneer Kadhai', 140.0, 260.0, 'Main Course'),
    ('Paneer Bhurji', 150.0, 270.0, 'Main Course'),
    ('Veg Kolhapuri', 120.0, 220.0, 'Main Course'),
    ('Veg Maratha', 130.0, 240.0, 'Main Course'),
    ('Dal Tadka', 90.0, 160.0, 'Main Course'),
    ('Dal Makhani', 110.0, 200.0, 'Main Course'),
    ('Kaju Curry', 160.0, 290.0, 'Main Course'),
    ('Butter Chicken', 170.0, 320.0, 'Main Course'),
    ('Chicken Masala', 150.0, 280.0, 'Main Course'),
    ('Chicken Handi', 180.0, 340.0, 'Main Course'),
    ('Chicken Kolhapuri', 160.0, 300.0, 'Main Course'),
    ('Chicken Curry', 140.0, 260.0, 'Main Course'),
    ('Mutton Curry', 200.0, 380.0, 'Main Course'),
    ('Mutton Rogan Josh', 220.0, 410.0, 'Main Course'),

    # --- Roti & Breads (15 Items) ---
    ('Tandoori Roti', 0.0, 20.0, 'Roti & Breads'),
    ('Butter Roti', 0.0, 25.0, 'Roti & Breads'),
    ('Plain Naan', 0.0, 35.0, 'Roti & Breads'),
    ('Butter Naan', 0.0, 45.0, 'Roti & Breads'),
    ('Garlic Naan', 0.0, 55.0, 'Roti & Breads'),
    ('Cheese Garlic Naan', 0.0, 80.0, 'Roti & Breads'),
    ('Missi Roti', 0.0, 35.0, 'Roti & Breads'),
    ('Plain Paratha', 0.0, 40.0, 'Roti & Breads'),
    ('Butter Paratha', 0.0, 50.0, 'Roti & Breads'),
    ('Aloo Paratha', 0.0, 70.0, 'Roti & Breads'),
    ('Paneer Paratha', 0.0, 90.0, 'Roti & Breads'),
    ('Kulcha Plain', 0.0, 40.0, 'Roti & Breads'),
    ('Onion Kulcha', 0.0, 60.0, 'Roti & Breads'),
    ('Chapati / Phulka', 0.0, 15.0, 'Roti & Breads'),
    ('Butter Chapati', 0.0, 20.0, 'Roti & Breads'),

    # --- Rice & Biryani (15 Items) ---
    ('Steam Rice', 50.0, 90.0, 'Rice & Biryani'),
    ('Jeera Rice', 70.0, 130.0, 'Rice & Biryani'),
    ('Dal Khichdi', 95.0, 170.0, 'Rice & Biryani'),
    ('Palak Khichdi', 100.0, 180.0, 'Rice & Biryani'),
    ('Veg Dum Biryani', 110.0, 200.0, 'Rice & Biryani'),
    ('Paneer Biryani', 130.0, 240.0, 'Rice & Biryani'),
    ('Veg Pulao', 100.0, 180.0, 'Rice & Biryani'),
    ('Kashmiri Pulao', 120.0, 220.0, 'Rice & Biryani'),
    ('Chicken Dum Biryani', 140.0, 260.0, 'Rice & Biryani'),
    ('Chicken Tikka Biryani', 160.0, 290.0, 'Rice & Biryani'),
    ('Chicken Hyderabadi Biryani', 150.0, 280.0, 'Rice & Biryani'),
    ('Egg Biryani', 110.0, 200.0, 'Rice & Biryani'),
    ('Mutton Biryani', 180.0, 340.0, 'Rice & Biryani'),
    ('Veg Fried Rice', 90.0, 170.0, 'Rice & Biryani'),
    ('Chicken Fried Rice', 120.0, 220.0, 'Rice & Biryani'),

    # --- Desserts & Drinks (15 Items) ---
    ('Masala Taak (Buttermilk)', 0.0, 25.0, 'Desserts & Drinks'),
    ('Sweet Lassi', 0.0, 50.0, 'Desserts & Drinks'),
    ('Mango Lassi', 0.0, 65.0, 'Desserts & Drinks'),
    ('Cold Drink (Soft Drink)', 0.0, 30.0, 'Desserts & Drinks'),
    ('Fresh Lime Soda', 0.0, 45.0, 'Desserts & Drinks'),
    ('Fresh Lime Water', 0.0, 35.0, 'Desserts & Drinks'),
    ('Cold Coffee', 0.0, 70.0, 'Desserts & Drinks'),
    ('Gulab Jamun (2 Pcs)', 0.0, 50.0, 'Desserts & Drinks'),
    ('Rasgulla (2 Pcs)', 0.0, 50.0, 'Desserts & Drinks'),
    ('Vanilla Ice Cream', 0.0, 60.0, 'Desserts & Drinks'),
    ('Chocolate Ice Cream', 0.0, 70.0, 'Desserts & Drinks'),
    ('Butterscotch Ice Cream', 0.0, 70.0, 'Desserts & Drinks'),
    ('Matka Kulfi', 0.0, 60.0, 'Desserts & Drinks'),
    ('Gajar Halwa (Seasonal)', 0.0, 80.0, 'Desserts & Drinks'),
    ('Sizzling Brownie with Ice Cream', 0.0, 140.0, 'Desserts & Drinks')
]

# Database Tables Initialization
def init_db():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1. Orders Table
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
            
            # 2. Menu Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS menu_items (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    half_price REAL DEFAULT 0.0,
                    full_price REAL NOT NULL,
                    category TEXT
                )
            ''')
            
            # 3. Insert or Update Default Menu Data if table has fewer than 75 items
            cursor.execute("SELECT COUNT(*) FROM menu_items")
            count = cursor.fetchone()[0]
            
            if count < 75:
                cursor.execute("TRUNCATE TABLE menu_items RESTART IDENTITY")
                cursor.executemany(
                    'INSERT INTO menu_items (name, half_price, full_price, category) VALUES (%s, %s, %s, %s)', 
                    DEFAULT_FULL_MENU
                )
            
            conn.commit()
            print("Database Initialized Successfully with 75 Menu Items!")
    except Exception as e:
        print("Database Init Error:", e)
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# Run initialization at application start
init_db()

# IST Time (UTC + 5:30) Helper Function
def get_indian_time():
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
    return ist_now.strftime("%Y-%m-%d"), ist_now.strftime("%I:%M %p")

# --- Routes ---

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

# --- API Endpoints ---

@app.route('/api/menu', methods=['GET'])
def get_menu():
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute('SELECT id, name, half_price, full_price, category FROM menu_items ORDER BY id ASC')
            menu_list = cursor.fetchall()

        return jsonify({'success': True, 'menu': menu_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# --------------------------------------------------------------
# 🆕 नवीन Menu Item Add करण्यासाठी Endpoint
# Admin Dashboard वरील "Add New Menu Item" फॉर्म याच route ला
# data पाठवतो. Item database मध्ये save झाला की तो आपोआप
# /api/menu (म्हणजे customer च्या /menu page वर) पण दिसतो,
# कारण दोन्ही ठिकाणी एकाच menu_items table मधून data येतो.
# --------------------------------------------------------------
@app.route('/api/admin/add_item', methods=['POST'])
def add_menu_item():
    try:
        data = request.json or {}
        name = data.get('name')
        category = data.get('category')
        half_price = float(data.get('half_price', 0))
        full_price = float(data.get('full_price', 0))

        if not name or not full_price:
            return jsonify({'success': False, 'error': 'Name आणि Full Price आवश्यक आहे'}), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                'INSERT INTO menu_items (name, half_price, full_price, category) VALUES (%s, %s, %s, %s)',
                (name, half_price, full_price, category)
            )
            conn.commit()

        return jsonify({'success': True, 'message': 'Item added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@app.route('/api/admin/update_item', methods=['POST'])
def update_item():
    try:
        data = request.json or {}
        item_id = data.get('id')
        new_half_price = float(data.get('half_price', 0))
        new_full_price = float(data.get('full_price', 0))

        if not item_id:
            return jsonify({'success': False, 'error': 'Invalid parameters'}), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('UPDATE menu_items SET half_price = %s, full_price = %s WHERE id = %s', 
                           (new_half_price, new_full_price, item_id))
            conn.commit()

        return jsonify({'success': True, 'message': 'Price updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@app.route('/api/order', methods=['POST'])
def place_order():
    try:
        data = request.json or {}
        if not data or 'customer_name' not in data or 'table_no' not in data or 'items' not in data:
            return jsonify({'success': False, 'error': 'Invalid data'}), 400

        date_str, time_str = get_indian_time()
        items_summary = ", ".join([f"{item['name']} (x{item['qty']})" for item in data['items']])

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('''
                INSERT INTO orders (customer_name, table_no, phone, items, total, order_date, order_time, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''', (data['customer_name'], data['table_no'], data.get('phone', 'N/A'), 
                  items_summary, float(data.get('total', 0)), date_str, time_str, 'Pending ⏳'))
            
            order_id = cursor.fetchone()[0]
            conn.commit()

        return jsonify({'success': True, 'order_id': order_id, 'date': date_str, 'time': time_str})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@app.route('/api/order/cancel/<int:order_id>', methods=['DELETE'])
def cancel_order(order_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT order_date, order_time FROM orders WHERE id = %s', (order_id,))
            order = cursor.fetchone()
            
            if not order:
                return jsonify({'success': False, 'error': 'ऑर्डर सापडली नाही!'}), 404

            order_date_str, order_time_str = str(order[0]), str(order[1])
            order_datetime_str = f"{order_date_str} {order_time_str}"
            order_datetime = datetime.datetime.strptime(order_datetime_str, "%Y-%m-%d %I:%M %p")
            
            utc_now = datetime.datetime.now(datetime.timezone.utc)
            ist_now = (utc_now + datetime.timedelta(hours=5, minutes=30)).replace(tzinfo=None)

            time_diff_minutes = (ist_now - order_datetime).total_seconds() / 60

            if time_diff_minutes > 10:
                return jsonify({
                    'success': False, 
                    'error': 'ऑर्डर देऊन १० मिनिटांपेक्षा जास्त वेळ झाला आहे. किचनमध्ये स्वयंपाक सुरू असल्याने आता ऑर्डर डिलीट करता येणार नाही!'
                }), 400

            cursor.execute('DELETE FROM orders WHERE id = %s', (order_id,))
            conn.commit()
            
        return jsonify({'success': True, 'message': 'Order deleted successfully'})
        
    except Exception as e:
        print("Delete Order Error:", e)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# --------------------------------------------------------------
# 🆕 कस्टमरच्या स्क्रीनवरून दर काही सेकंदांनी ऑर्डरचा स्टेटस आणि
# "अजून किती वेळ Cancel करता येईल" हे तपासण्यासाठी नवीन Endpoint.
# (हे DELETE /api/order/cancel/<id> ला रिप्लेस करत नाही -- तो
#  आधीचा 10-मिनिटांचा लॉक तसाच वापरला जातो. हे फक्त customer च्या
#  स्क्रीनवर Cancel बटण वेळेआधीच लपवण्यासाठी आहे.)
# --------------------------------------------------------------
@app.route('/api/order/status/<int:order_id>', methods=['GET'])
def order_status(order_id):
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute('SELECT id, status, order_date, order_time FROM orders WHERE id = %s', (order_id,))
            order = cursor.fetchone()

        if not order:
            return jsonify({'success': True, 'status': 'not_found', 'can_cancel': False, 'seconds_left': 0})

        order_datetime_str = f"{order['order_date']} {order['order_time']}"
        order_datetime = datetime.datetime.strptime(order_datetime_str, "%Y-%m-%d %I:%M %p")

        utc_now = datetime.datetime.now(datetime.timezone.utc)
        ist_now = (utc_now + datetime.timedelta(hours=5, minutes=30)).replace(tzinfo=None)
        elapsed_minutes = (ist_now - order_datetime).total_seconds() / 60

        is_pending = bool(order['status']) and 'Pending' in order['status']
        can_cancel = is_pending and elapsed_minutes <= 10
        seconds_left = max(0, int((10 - elapsed_minutes) * 60)) if can_cancel else 0

        return jsonify({
            'success': True,
            'status': order['status'],
            'can_cancel': can_cancel,
            'seconds_left': seconds_left
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@app.route('/api/admin/orders', methods=['GET'])
def get_admin_orders():
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute('SELECT id, customer_name, table_no, phone, items AS items_str, total, order_date AS date, order_time AS time, status FROM orders ORDER BY id DESC')
            orders_list = cursor.fetchall()

        return jsonify({'success': True, 'orders': orders_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@app.route('/api/admin/complete_order', methods=['POST'])
def complete_order():
    try:
        data = request.json or {}
        order_id = data.get('order_id')
        
        if not order_id:
            return jsonify({'success': False, 'error': 'Order ID required'}), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('UPDATE orders SET status = %s WHERE id = %s', ('Completed ✅', order_id))
            conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@app.route('/api/admin/analytics_data', methods=['GET'])
def get_analytics():
    try:
        selected_date = request.args.get('date')
        
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if selected_date:
                cursor.execute('SELECT id, customer_name, table_no, items, total, order_date AS date, order_time AS time, status FROM orders WHERE order_date = %s ORDER BY id DESC', (selected_date,))
            else:
                cursor.execute('SELECT id, customer_name, table_no, items, total, order_date AS date, order_time AS time, status FROM orders ORDER BY id DESC')

            orders_list = cursor.fetchall()

        total_revenue = sum([float(o['total']) for o in orders_list if o['total']])
        pending_count = sum([1 for o in orders_list if o['status'] and 'Pending' in o['status']])
        completed_count = sum([1 for o in orders_list if o['status'] and 'Completed' in o['status']])

        return jsonify({
            'success': True, 
            'selected_date': selected_date,
            'total_orders': len(orders_list), 
            'total_revenue': total_revenue,
            'pending_orders': pending_count, 
            'completed_orders': completed_count,
            'orders': orders_list
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)
