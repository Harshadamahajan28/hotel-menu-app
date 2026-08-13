import os
import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import psycopg2

app = Flask(__name__)
app.secret_key = "royal_spice_secret_key"

DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://neondb_owner:npg_tp1sR2xCcloF@ep-solitary-water-ayecuz6l.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require'
)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS menu_items (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                category VARCHAR(50) NOT NULL,
                price_half NUMERIC(10, 2),
                price_full NUMERIC(10, 2) NOT NULL,
                image_url TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                customer_name VARCHAR(100) NOT NULL,
                table_no INT NOT NULL,
                items JSONB NOT NULL,
                total NUMERIC(10, 2) NOT NULL,
                order_date DATE DEFAULT CURRENT_DATE,
                order_time VARCHAR(20) NOT NULL,
                status VARCHAR(20) DEFAULT 'Pending'
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Database Initialized Successfully!")
    except Exception as e:
        print("Database Connection Error:", e)

init_db()

@app.route('/')
def menu_page():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM menu_items ORDER BY id ASC')
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        
        menu_by_category = {}
        for item in items:
            cat = item[2]
            if cat not in menu_by_category:
                menu_by_category[cat] = []
            menu_by_category[cat].append({
                'id': item[0],
                'name': item[1],
                'category': item[2],
                'price_half': item[3],
                'price_full': item[4],
                'image_url': item[5]
            })
            
        return render_template('menu.html', menu=menu_by_category)
    except Exception as e:
        return f"Error loading menu: {e}"

@app.route('/api/order', methods=['POST'])
def place_order():
    try:
        data = request.json
        c_name = data.get('customer_name')
        t_no = data.get('table_no')
        items = data.get('items')
        total = data.get('total')

        utc_now = datetime.datetime.now(datetime.timezone.utc)
        ist_now = utc_now + datetime.timedelta(hours=5, minutes=30)
        
        order_date = ist_now.strftime("%Y-%m-%d")
        order_time = ist_now.strftime("%I:%M %p")

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO orders (customer_name, table_no, items, total, order_date, order_time)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        ''', (c_name, t_no, psycopg2.extras.Json(items), total, order_date, order_time))
        
        order_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'order_id': order_id,
            'order_date': order_date,
            'order_time': order_time
        })
    except Exception as e:
        print("Order Error:", e)
        return jsonify({'success': False, 'error': str(e)}), 500

# ⏱️ १० मिनिटांचे नियम जोडून अपडेट केलेले Delete/Cancel API
@app.route('/api/order/cancel/<int:order_id>', methods=['DELETE'])
def cancel_order(order_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # आधी ऑर्डर कधी तयार झाली ते तपासा
        cursor.execute('SELECT order_date, order_time FROM orders WHERE id = %s', (order_id,))
        order = cursor.fetchone()
        
        if not order:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Order not found!'}), 404

        order_date_str, order_time_str = str(order[0]), str(order[1])
        
        # ऑर्डर दिलेली वेळ आणि आत्ताची वेळ यातील फरक काढा
        order_datetime_str = f"{order_date_str} {order_time_str}"
        order_datetime = datetime.datetime.strptime(order_datetime_str, "%Y-%m-%d %I:%M %p")
        
        # आत्ताची वेळ (IST)
        utc_now = datetime.datetime.now(datetime.timezone.utc)
        ist_now = (utc_now + datetime.timedelta(hours=5, minutes=30)).replace(tzinfo=None)

        time_diff_minutes = (ist_now - order_datetime).total_seconds() / 60

        # १० मिनिटांपेक्षा जास्त वेळ झाला असल्यास Delete न करता एरर द्या
        if time_diff_minutes > 10:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False, 
                'error': 'ऑर्डर देऊन १० मिनिटांपेक्षा जास्त वेळ झाला आहे. आता ऑर्डर रद्द करता येणार नाही!'
            }), 400

        # १० मिनिटांच्या आत असल्यास डिलीट करा
        cursor.execute('DELETE FROM orders WHERE id = %s', (order_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Order deleted successfully'})
        
    except Exception as e:
        print("Delete Order Error:", e)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == "royal123":
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="गलत पासवर्ड!")
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM orders ORDER BY id DESC')
        orders = cursor.fetchall()
        
        cursor.execute('SELECT * FROM menu_items ORDER BY id ASC')
        menu_items = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('admin.html', orders=orders, menu_items=menu_items)
    except Exception as e:
        return f"Error loading admin: {e}"

if __name__ == '__main__':
    app.run(debug=True)
