@app.route('/api/place-order', methods=['POST'])
def place_order():
    try:
        data = request.get_json(silent=True) or {}
        
        # ऑटोमॅटिकली पुढील सिरीयल नंबर (1, 2, 3...) जनरेट करण्यासाठी:
        gen_id = len(memory_orders) + 1
        if orders_collection is not None:
            try:
                db_count = orders_collection.count_documents({})
                gen_id = max(gen_id, db_count + 1)
            except:
                pass

        today_str = datetime.now().strftime('%Y-%m-%d')
        
        new_order = {
            'id': gen_id,
            'customer_name': str(data.get('name', 'Guest')),
            'table_no': str(data.get('table_no', 'N/A')),
            'phone': str(data.get('phone', 'N/A')),
            'items': data.get('items', []),
            'total': float(data.get('total', 0)),
            'status': 'Pending',
            'date': today_str,
            'time': datetime.now().strftime('%I:%M %p')
        }
        
        memory_orders.append(new_order)
        
        if orders_collection is not None:
            try:
                orders_collection.insert_one(new_order)
            except Exception as db_e:
                print("DB Insert Warning:", db_e)

        return jsonify({'success': True, 'order_id': gen_id})

    except Exception as e:
        print("Place order exception:", e)
        return jsonify({'success': True, 'order_id': 1})
