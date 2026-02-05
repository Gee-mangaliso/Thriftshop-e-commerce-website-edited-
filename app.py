from flask_mail import Mail, Message
from flask import request, jsonify
from flask_bcrypt import Bcrypt
import mysql.connector
import json
import uuid
import os
import secrets
from datetime import datetime, timedelta
import jwt 
import random
from flask import request
from werkzeug.utils import secure_filename
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask import render_template
from werkzeug.middleware.proxy_fix import ProxyFix

# Initialize Flask app
app = Flask(__name__)

app.config['DEBUG'] = True

app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_proto=1,
    x_host=1
)

#Secure session and JWT configuratuion
app.config.update(
    SECRET_KEY='your-super-secret-key', # Replace with a secure key
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_TYPE='filesystem',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24)
)

#JWT token generator
def generate_token(user_id, email):
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token

#Homepage route
@app.route('/')
def home():
    return render_template("index.html")

CORS(app,supports_credentials=True)

# File upload configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm'}

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'noreply@mzansithrift.co.za'
app.config['MAIL_PASSWORD'] = 'your-email-password'
mail = Mail(app)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '@Khizo14251',
    'database': 'thriftshop_sa',
#    'auth_plugin': 'mysql_native_password'
}

# Setup logging
def configure_log():
    if not os.path.exists('logs'):
        os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/mzansi_thrift.log', maxBytes=1_000_000, backupCount=5,delay=True)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s in %(pathname)s: %(lineno)s"
))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Mzansi Thrift Store startup')
    
configure_log()

def get_db_connection():
    try:
        return mysql.connector.connect(**db_config)
           # auth_plugin='mysql_native_password'
    except mysql.connector.Error as err:
        print("DB ERROR:", err)
        app.logger.error(f"Database connection error: {err}")
        return None
    
# Bcrypt for password hashing
bcrypt = Bcrypt(app)

# Utility functions
def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_order_number():
    return f"TS{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"

def generate_token():
    return secrets.token_urlsafe(32)

def calculate_shipping(province, weight=1):
    """Calculate shipping costs based on province and weight"""
    base_costs = {
        'Gauteng': 65.00,
        'Western Cape': 85.00,
        'KwaZulu-Natal': 95.00,
        'Eastern Cape': 105.00,
        'Free State': 90.00,
        'Limpopo': 110.00,
        'Mpumalanga': 100.00,
        'North West': 95.00,
        'Northern Cape': 120.00
    }
    return base_costs.get(province, 85.00) + (weight * 2.5)

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session and 'seller_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def seller_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'seller_id' not in session:
            return jsonify({'error': 'Seller authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def buyer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Buyer authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Create upload directories
def create_upload_dirs():
    directories = ['images', 'videos', 'profiles']
    for directory in directories:
        path = os.path.join(app.config['UPLOAD_FOLDER'], directory)
        if not os.path.exists(path):
            os.makedirs(path)

create_upload_dirs()


# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    app.logger.info("🔥 /api/register HIT")
    data = request.get_json()
    app.logger.info(f"📥 Incoming data: {request.get_json()}")
    
    if not data:
        return jsonify({'error': 'Invalid or missing JSON body'}), 400
    
    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')

    if not all([full_name, email, password, phone]):
        return jsonify({'error': 'All fields are required'}), 400
    
    # Hash password and create user
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        
        # Check if user is already registered
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({'error': 'Email already registered'}), 409

        cursor.execute("""
            INSERT INTO users (email, password_hash, full_name, phone)
            VALUES (%s, %s, %s, %s)
        """, (email, password_hash, full_name, phone))
        
        conn.commit()
        user_id = cursor.lastrowid
        
        # Create session for current user
        session['user_id'] = user_id
        session['user_name'] = full_name
        session.permanent = True
        
         # Log user activity
        cursor.execute("""
            INSERT INTO activity_logs (user_id, action, ip_address)
            VALUES (%s, %s, %s)
        """, (user_id, 'user_registered', request.remote_addr))
        conn.commit()
        
        app.logger.info(f'New user registered: {email}')
        
        # Return success response with current user's name
        return jsonify({
            "message": "Registration successful",
            "current_user": full_name,
            "user": {
                "id": user_id,
                "full_name": full_name,
                "email": email,
                "phone": phone
            }
        }), 201

    except mysql.connector.Error as err:
        #conn.rollback()
        app.logger.error(f'Registration error: {err}')
        return jsonify({'error': 'Database error occurred'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
@app.route('/api/login', methods=['POST'])
def login():
    app.logger.info("🔥 /api/login HIT")
    data = request.get_json()
    app.logger.info(f"📥 Incoming data: {request.get_json()}")
    
    email = data.get('email')
    password = data.get('password')
   # user_type = data.get('user_type', 'buyer')

    if not email or not password:
        return jsonify({'error': 'Missing email or password'}), 400

    conn = get_db_connection()
    
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        "SELECT id, full_name, email, password_hash, phone FROM users WHERE email = %s",
        (email,)
    )
    user = cursor.fetchone()
     
    cursor.close()
    conn.close()


     # VERIFY USER EXISTS IN DATABASE
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401

     # VERIFY PASSWORD
    if not bcrypt.check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid email or password'}), 401
        
        
     #Create session
    session.clear() 
    session['user_id'] = user['id']
    session['user_name'] = user['full_name']
    session.permanent = True
     
    return jsonify({
        "success": True,
        "user": {
            "id": user['id'],
            "full_name": user['full_name'],
            "email": user['email'],
            "phone": user['phone']
        }
    }), 200

@app.route('/api/logout', methods=['POST'])
def logout():
    user_id = session.get('user_id') or session.get('seller_id')
    if user_id:
        # Log logout activity
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                               INSERT INTO activity_logs (user_id, action, ip_address)
                               VALUES (%s, %s, %s)
                               """, (user_id, 'user_logout', request.remote_addr))
                conn.commit()
                cursor.close()
            except Exception as e:
                app.logger.error(f'Error logging logout activity: {e}')
            finally:
                conn.close()

    session.clear()
    app.logger.info('User logged out')
    return jsonify({'message': 'Logout successful'})

@app.route('/api/user')
@login_required
def get_current_user():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        if 'seller_id' in session:
            cursor.execute("""
                           SELECT id, email, business_name, status, phone, rating, total_sales
                           FROM sellers WHERE id = %s
                           """, (session['seller_id'],))
            user = cursor.fetchone()
            user_type = 'seller'
        else:
            cursor.execute("""
                           SELECT id, email, full_name, phone, address_line1, city, province
                           FROM users WHERE id = %s
                           """, (session['user_id'],))
            user = cursor.fetchone()
            user_type = 'buyer'

        return jsonify({'user': user, 'user_type': user_type})

    except Exception as e:
        app.logger.error(f'Error getting user: {e}')
        return jsonify({'error': 'Failed to get user data'}), 500
    finally:
        cursor.close()
        conn.close()

# Seller Registration
@app.route('/api/seller/register', methods=['POST'])
def seller_register():
    app.logger.info("🔥 /api/seller/register HIT")
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid or missing JSON body'}), 400
    
    business_name = data.get('business_name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    business_type = data.get('business_type', 'individual')

    if not all([business_name, email, password, phone]):
        return jsonify({'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    # Hash password and create user
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)

        # Check if seller exists
        cursor.execute("SELECT id FROM sellers WHERE email = %s OR business_name = %s",
                       (email, business_name))
        if cursor.fetchone():
            return jsonify({'error': 'Seller already exists with this email or business name'}), 400

        cursor.execute("""
                       INSERT INTO sellers (email, password_hash, business_name, business_type, phone, status)
                       VALUES (%s, %s, %s, %s, %s, 'pending')
        """, (email, password_hash, business_name, business_type, phone))
          

        
        conn.commit()
        seller_id = cursor.lastrowid
        
        # Create session for current seller
        session['seller_id'] = seller_id
        session['business_name'] = business_name
        session.permanent = True
        
        # Initialize seller stats
        cursor.execute("""
                       INSERT INTO seller_stats (seller_id, total_revenue, total_orders, total_products, pending_orders)
                       VALUES (%s, 0, 0, 0, 0)
        """, (seller_id,))
        
        app.logger.info(f'New seller registered: {business_name}')

# Return success response with current user's name
        return jsonify({
            "message": "Registration successful",
            "current_seller": business_name,
            "current seller": {
                "id": seller_id,
                "full_name": business_name,
                "email": email,
                "phone": phone
            }
        }), 201

    except mysql.connector.Error as err:
        conn.rollback()
        app.logger.error(f'Seller registration error: {err}')
        return jsonify({'error': 'Database error occurred'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
# Buyer Login
@app.route('/api/seller/login', methods=['POST'])
def seller_login():
    app.logger.info("🔥 /api/Seller/login HIT")
    data = request.get_json()
    app.logger.info(f"📥 Incoming data: {request.get_json()}")
    
    email = data.get('email')
    password = data.get('password')
   # user_type = data.get('user_type', 'buyer')

    if not email or not password:
        return jsonify({'error': 'Missing email or password'}), 400

    conn = get_db_connection()
    
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        "SELECT id, business_name, email, password_hash, phone FROM sellers WHERE email = %s",
        (email,)
    )
    currentSeller = cursor.fetchone()
     
    cursor.close()
    conn.close()


     # VERIFY USER EXISTS IN DATABASE
    if not currentSeller:
        return jsonify({'error': 'Invalid email or password'}), 401

     # VERIFY PASSWORD
    if not bcrypt.check_password_hash(currentSeller['password_hash'], password):
        return jsonify({'error': 'Invalid email or password'}), 401
        
        
     #Create session
    session.clear() 
    session['seller_id'] = currentSeller['id']
    session['business_name'] = currentSeller['business_name']
    session.permanent = True
     
    return jsonify({
        "success": True,
        "currentSeller": {
            "id": currentSeller['id'],
            "business_name": currentSeller['business_name'],
            "email": currentSeller['email'],
            "phone": currentSeller['phone']
        }
    }), 200

        
def serialize_product(product):
    return { "id": product.id,
             "name":product.name,
             "price": product.price,
             "description": product.description,
             "seller_name": product.seller.business_name if product.seller else None,
             "images": product.images if product.images else ["/static/uploads/images/no-image.png"],
             "videos": product.videos if product.videos else [] }        

# Product Routes
@app.route('/api/products')
def get_products():
    category_id = request.args.get('category_id')
    seller_id = request.args.get('seller_id')
    search = request.args.get('search')
    featured = request.args.get('featured')
    limit = request.args.get('limit')

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)

        query = """
                SELECT p.*, c.name as category_name, s.business_name as seller_name,
                       s.rating as seller_rating
                FROM products p
                         LEFT JOIN categories c ON p.category_id = c.id
                         LEFT JOIN sellers s ON p.seller_id = s.id
                WHERE p.is_active = TRUE AND s.status = 'approved' \
                """
        params = []

        if category_id:
            query += " AND p.category_id = %s"
            params.append(category_id)

        if seller_id:
            query += " AND p.seller_id = %s"
            params.append(seller_id)

        if search:
            query += " AND (p.name LIKE %s OR p.description LIKE %s OR p.brand LIKE %s)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])

        if featured and featured.lower() in ["1", "true", "yes"]:
            query += " AND p.featured = 1"
            query += " ORDER BY p.view_count DESC, p.created_at DESC"
        else:
            query += " ORDER BY p.created_at DESC"
            if limit:
                query += " LIMIT %s"
                params.append(int(limit))

        cursor.execute(query, params)
        products = cursor.fetchall()

        # Convert JSON images to Python list
        # Convert JSON images/videos safely
        for product in products:
            images = product.get('images')
            videos = product.get('videos')

            # Handle images
            if images:
                filenames = json.loads(images) # ✅ parse JSON string into list
                product['images'] = []
                try:
                    for fname in filenames: # ✅ loop through each filename
                        if fname.startswith("/static/"): # Already a full path → use directly
                            product['images'].append(fname)
                        else: # Just a filename → prepend the static path
                            product['images'].append(f"/static/uploads/images/{fname}")
                except Exception:
                    product['images'] = ["/static/uploads/images/no-image.png"]
            else:
                product['images'] = ["/static/uploads/images/no-image.png"]
            app.logger.info(f"Product {product['id']} raw images: {images}")

            # Handle videos
            if videos:
                try:
                    filenames = json.loads(videos)
                    product['videos'] = [f"/static/uploads/videos/{fname}" for fname in filenames]
                except Exception:
                    product['videos'] = []
            else:
                product['videos'] = []
        return jsonify({'products': products})
    
    except Exception as e:
        app.logger.error(f'Error getting products: {e}')
        return jsonify({'error': 'Failed to fetch products'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/products/<int:product_id>')
def get_product(product_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        # Update view count
        cursor.execute("UPDATE products SET view_count = view_count + 1 WHERE id = %s", (product_id,))

        cursor.execute("""
                       SELECT p.*, c.name as category_name, s.business_name as seller_name,
                              s.rating as seller_rating, s.total_sales as seller_sales
                       FROM products p
                                LEFT JOIN categories c ON p.category_id = c.id
                                LEFT JOIN sellers s ON p.seller_id = s.id
                       WHERE p.id = %s AND p.is_active = TRUE
                       """, (product_id,))

        product = cursor.fetchone()
        conn.commit()

        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Safely handle images
        images = product.get('images')
        if images:
            try:
                filenames = json.loads(images)
                product['images'] = [
                    fname if fname.startswith("/static/") else f"/static/uploads/images/{fname}"
                    for fname in filenames
               ]
            except Exception:
                product['images'] = ["/static/uploads/images/no-image.png"]
        else:
            product['images'] = ["/static/uploads/images/no-image.png"]

        # Safely handle videos
        videos = product.get('videos')
        if videos:
            try:
                filenames = json.loads(videos)
                product['videos'] = [f"/static/uploads/videos/{fname}" for fname in filenames]
            except Exception:
                product['videos'] = []
        else:
            product['videos'] = []

    except Exception as e:
        app.logger.error(f'Error getting product {product_id}: {e}')
        return jsonify({'error': 'Failed to fetch product'}), 500
    finally:
        cursor.close()
        conn.close()


# Cart Routes
@app.route('/api/cart', methods=['GET', 'POST', 'DELETE'])
@buyer_required
def manage_cart():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        if request.method == 'GET':
            cursor.execute("""
                           SELECT c.*, p.name, p.price, p.images, p.stock_quantity,
                                  s.business_name as seller_name, s.id as seller_id
                           FROM cart c
                                    JOIN products p ON c.product_id = p.id
                                    JOIN sellers s ON p.seller_id = s.id
                           WHERE c.user_id = %s
                           """, (user_id,))

            cart_items = cursor.fetchall()

            for item in cart_items:
                if item['images']:
                    item['images'] = json.loads(item['images'])
                else:
                    item['images'] = []

            return jsonify({'cart_items': cart_items})

        elif request.method == 'POST':
            data = request.json
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)

            # Check if product exists and has stock
            cursor.execute("SELECT stock_quantity FROM products WHERE id = %s AND is_active = TRUE", (product_id,))
            product = cursor.fetchone()

            if not product:
                return jsonify({'error': 'Product not found'}), 404

            if product['stock_quantity'] < quantity:
                return jsonify({'error': 'Insufficient stock'}), 400

            # Check if item already in cart
            cursor.execute("SELECT id, quantity FROM cart WHERE user_id = %s AND product_id = %s", (user_id, product_id))
            existing_item = cursor.fetchone()

            if existing_item:
                new_quantity = existing_item['quantity'] + quantity
                if new_quantity > product['stock_quantity']:
                    return jsonify({'error': 'Cannot add more than available stock'}), 400

                cursor.execute("UPDATE cart SET quantity = %s WHERE user_id = %s AND product_id = %s",
                               (new_quantity, user_id, product_id))
            else:
                cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)",
                               (user_id, product_id, quantity))

            conn.commit()
            return jsonify({'message': 'Item added to cart'})

        elif request.method == 'DELETE':
            product_id = request.args.get('product_id')

            if product_id:
                cursor.execute("DELETE FROM cart WHERE user_id = %s AND product_id = %s", (user_id, product_id))
            else:
                cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))

            conn.commit()
            return jsonify({'message': 'Cart item removed'})

    except Exception as e:
        conn.rollback()
        app.logger.error(f'Cart operation error: {e}')
        return jsonify({'error': 'Cart operation failed'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/cart/<int:product_id>', methods=['PUT'])
@buyer_required
def update_cart_item(product_id):
   user_id = session.get('user_id')
   if not user_id:
       return jsonify({'error': 'Unauthorized'}), 401
    
   data = request.json
   quantity = data.get('quantity')
   
   if quantity <= 0:
        return jsonify({'error': 'Quantity must be positive'}), 400
    
   conn = get_db_connection()
   if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

   try:
       cursor = conn.cursor(dictionary=True)
       # Check product stock
       cursor.execute("SELECT stock_quantity FROM products WHERE id = %s", (product_id,))
       product = cursor.fetchone()

       if not product:
            return jsonify({'error': 'Product not found'}), 404

       if product['stock_quantity'] < quantity:
            return jsonify({'error': 'Insufficient stock'}), 400

       cursor.execute("UPDATE cart SET quantity = %s WHERE user_id = %s AND product_id = %s",
                       (quantity, user_id, product_id))

       if cursor.rowcount == 0:
           return jsonify({'error': 'Cart item not found'}), 404

       conn.commit()
       return jsonify({'message': 'Cart updated successfully'})
                      
   except Exception as e:
       conn.rollback()
       app.logger.error(f'Cart update error: {e}')
       return jsonify({'error': 'Failed to update cart'}), 500
   finally:
       cursor.close()
       conn.close()

# Order Routes
@app.route('/api/orders', methods=['GET', 'POST'])
@login_required
def manage_orders():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        if request.method == 'GET':
            if 'seller_id' in session:
                # Get seller's orders
                seller_id = session.get('seller_id')
                if not user_id:
                    return jsonify({'error': 'Unauthorized'}), 401

                cursor.execute("""
                               SELECT o.*, oi.product_id, oi.quantity, oi.unit_price, oi.status as item_status,
                                      p.name as product_name, u.full_name as customer_name, u.phone as customer_phone
                               FROM orders o
                                        JOIN order_items oi ON o.id = oi.order_id
                                        JOIN products p ON oi.product_id = p.id
                                        JOIN users u ON o.user_id = u.id
                               WHERE oi.seller_id = %s
                               ORDER BY o.created_at DESC
                               """, (seller_id,))
            else:
                # Get buyer's orders
                user_id = session['user_id']
                cursor.execute("""
                               SELECT o.*,
                                      (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as item_count
                               FROM orders o
                               WHERE o.user_id = %s
                               ORDER BY o.created_at DESC
                               """, (user_id,))

            orders = cursor.fetchall()
            return jsonify({'orders': orders})

        elif request.method == 'POST':
            if 'user_id' not in session:
                return jsonify({'error': 'Buyer authentication required'}), 401

            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Unauthorized'}), 401
            data = request.json
            shipping_address = data.get('shipping_address')
            payment_method = data.get('payment_method', 'credit_card')

            if not shipping_address:
                return jsonify({'error': 'Shipping address required'}), 400

            # Get cart items
            cursor.execute("""
                           SELECT c.product_id, c.quantity, p.price, p.seller_id, p.name, p.stock_quantity
                           FROM cart c
                                    JOIN products p ON c.product_id = p.id
                           WHERE c.user_id = %s
                           """, (user_id,))

            cart_items = cursor.fetchall()

            if not cart_items:
                return jsonify({'error': 'Cart is empty'}), 400

            # Validate stock and calculate total
            total_amount = 0
            order_items = []

            for item in cart_items:
                if item['stock_quantity'] < item['quantity']:
                    return jsonify({'error': f'Insufficient stock for {item["name"]}'}), 400

                item_total = item['price'] * item['quantity']
                total_amount += item_total

                order_items.append({
                    'product_id': item['product_id'],
                    'seller_id': item['seller_id'],
                    'quantity': item['quantity'],
                    'unit_price': item['price'],
                    'total_price': item_total
                })

            shipping_fee = calculate_shipping(shipping_address.get('province', 'Gauteng'))
            total_amount += shipping_fee

            # Create order
            order_number = generate_order_number()
            cursor.execute("""
                           INSERT INTO orders (order_number, user_id, total_amount, shipping_fee,
                                               shipping_address, payment_method)
                           VALUES (%s, %s, %s, %s, %s, %s)
                           """, (order_number, user_id, total_amount, shipping_fee,
                                 json.dumps(shipping_address), payment_method))

            order_id = cursor.lastrowid

            # Create order items and update product stock
            for item in order_items:
                cursor.execute("""
                               INSERT INTO order_items (order_id, product_id, seller_id, quantity, unit_price, total_price)
                               VALUES (%s, %s, %s, %s, %s, %s)
                               """, (order_id, item['product_id'], item['seller_id'], item['quantity'],
                                     item['unit_price'], item['total_price']))

                # Update product stock
                cursor.execute("""
                               UPDATE products SET stock_quantity = stock_quantity - %s
                               WHERE id = %s
                               """, (item['quantity'], item['product_id']))

            # Clear cart
            cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))

            # Log order creation
            cursor.execute("""
                           INSERT INTO activity_logs (user_id, action, ip_address)
                           VALUES (%s, %s, %s)
                           """, (user_id, 'order_created', request.remote_addr))

            conn.commit()

            app.logger.info(f'Order created: {order_number} by user {user_id}')

            return jsonify({
                'message': 'Order created successfully',
                'order_id': order_id,
                'order_number': order_number,
                'total_amount': total_amount
            }), 201

    except Exception as e:
        conn.rollback()
        app.logger.error(f'Order operation error: {e}')
        return jsonify({'error': 'Order operation failed'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/orders/<int:order_id>/cancel', methods=['POST'])
@buyer_required
def cancel_order(order_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        # Verify order belongs to user and can be cancelled
        cursor.execute("""
                       SELECT id, status FROM orders
                       WHERE id = %s AND user_id = %s AND status IN ('pending', 'confirmed')
                       """, (order_id, user_id))

        order = cursor.fetchone()
        if not order:
            return jsonify({'error': 'Order not found or cannot be cancelled'}), 404

        # Get order items to restore stock
        cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
        order_items = cursor.fetchall()

        # Restore product stock
        for item in order_items:
            cursor.execute("""
                           UPDATE products SET stock_quantity = stock_quantity + %s
                           WHERE id = %s
                           """, (item['quantity'], item['product_id']))

        # Cancel order
        cursor.execute("UPDATE orders SET status = 'cancelled' WHERE id = %s", (order_id,))
        cursor.execute("UPDATE order_items SET status = 'cancelled' WHERE order_id = %s", (order_id,))

        # Log cancellation
        cursor.execute("""
                       INSERT INTO activity_logs (user_id, action, ip_address)
                       VALUES (%s, %s, %s)
                       """, (user_id, 'order_cancelled', request.remote_addr))

        conn.commit()

        app.logger.info(f'Order cancelled: {order_id} by user {user_id}')

        return jsonify({'message': 'Order cancelled successfully'})

    except Exception as e:
        conn.rollback()
        app.logger.error(f'Order cancellation error: {e}')
        return jsonify({'error': 'Failed to cancel order'}), 500
    finally:
        cursor.close()
        conn.close()

# Payment Routes
@app.route('/api/payments/process', methods=['POST'])
@buyer_required
def process_payment():
    data = request.json
    order_id = data.get('order_id')
    payment_method = data.get('payment_method')
    amount = data.get('amount')

    if not all([order_id, payment_method, amount]):
        return jsonify({'error': 'Missing payment information'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        # Verify order exists and belongs to user
        cursor.execute("SELECT id, user_id, total_amount FROM orders WHERE id = %s", (order_id,))
        order = cursor.fetchone()

        if not order or order['user_id'] != session['user_id']:
            return jsonify({'error': 'Order not found'}), 404

        if abs(order['total_amount'] - float(amount)) > 0.01:  # Allow small floating point differences
            return jsonify({'error': 'Amount mismatch'}), 400

        # Simulate payment processing with random success/failure
        success = random.random() > 0.2  # 80% success rate
        transaction_id = str(uuid.uuid4())

        if success:
            # Update order status
            cursor.execute("UPDATE orders SET payment_status = 'completed', status = 'confirmed' WHERE id = %s", (order_id,))
            cursor.execute("UPDATE order_items SET status = 'confirmed' WHERE order_id = %s", (order_id,))

            # Update seller stats
            cursor.execute("""
                           UPDATE seller_stats ss
                               JOIN order_items oi ON ss.seller_id = oi.seller_id
                               SET ss.total_orders = ss.total_orders + 1,
                                   ss.total_revenue = ss.total_revenue + oi.total_price,
                                   ss.pending_orders = ss.pending_orders + 1
                           WHERE oi.order_id = %s
                           """, (order_id,))

            status = 'success'
            message = 'Payment processed successfully'
        else:
            cursor.execute("UPDATE orders SET payment_status = 'failed' WHERE id = %s", (order_id,))
            status = 'failed'
            message = 'Payment failed. Please try again.'

        # Record payment transaction
        cursor.execute("""
                       INSERT INTO payment_transactions (order_id, transaction_id, amount, payment_method, status)
                       VALUES (%s, %s, %s, %s, %s)
                       """, (order_id, transaction_id, amount, payment_method, status))

        # Log payment activity
        cursor.execute("""
                       INSERT INTO activity_logs (user_id, action, ip_address)
                       VALUES (%s, %s, %s)
                       """, (session['user_id'], f'payment_{status}', request.remote_addr))

        conn.commit()

        app.logger.info(f'Payment {status} for order {order_id}')

        return jsonify({
            'success': success,
            'message': message,
            'transaction_id': transaction_id
        })

    except Exception as e:
        conn.rollback()
        app.logger.error(f'Payment processing error: {e}')
        return jsonify({'error': 'Payment processing failed'}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/products/<int:product_id>/media', methods=['GET', 'POST'])
@seller_required
def manage_product_media(product_id):
    seller_id = session['seller_id']

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        # Verify product belongs to seller
        cursor.execute("SELECT id FROM products WHERE id = %s AND seller_id = %s", (product_id, seller_id))
        if not cursor.fetchone():
            return jsonify({'error': 'Product not found'}), 404

        if request.method == 'GET':
            cursor.execute("""
                           SELECT * FROM product_media
                           WHERE product_id = %s
                           ORDER BY sort_order, created_at
                           """, (product_id,))

            media_items = cursor.fetchall()
            return jsonify({'media': media_items})

        elif request.method == 'POST':
            if 'media' not in request.files:
                return jsonify({'error': 'No files provided'}), 400

            files = request.files.getlist('media')
            uploaded_media = []

            for file in files:
                if file.filename == '':
                    continue

                filename = secure_filename(file.filename)
                file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

                # Determine media type
                if file_ext in ALLOWED_IMAGE_EXTENSIONS:
                    media_type = 'image'
                    upload_dir = 'images'
                    mime_type = f'image/{file_ext}'
                elif file_ext in ALLOWED_VIDEO_EXTENSIONS:
                    media_type = 'video'
                    upload_dir = 'videos'
                    mime_type = f'video/{file_ext}'
                else:
                    continue  # Skip invalid files

                # Generate unique filename
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], upload_dir, unique_filename)
                file.save(filepath)

                # Get file size
                file_size = os.path.getsize(filepath)

                # Insert into database
                cursor.execute("""
                               INSERT INTO product_media (product_id, media_type, file_url, file_name, file_size, mime_type, uploader_id, uploader_type)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, 'seller')
                               """, (product_id, media_type, f'/static/uploads/{upload_dir}/{unique_filename}',
                                     filename, file_size, mime_type, seller_id))

                media_id = cursor.lastrowid

                uploaded_media.append({
                    'id': media_id,
                    'media_type': media_type,
                    'file_url': f'/static/uploads/{upload_dir}/{unique_filename}',
                    'file_name': filename,
                    'file_size': file_size,
                    'mime_type': mime_type
                })

            conn.commit()

            app.logger.info(f'Media uploaded for product {product_id}: {len(uploaded_media)} items')

            return jsonify({
                'message': 'Media uploaded successfully',
                'media': uploaded_media
            }), 201

    except Exception as e:
        conn.rollback()
        app.logger.error(f'Product media error: {e}')
        return jsonify({'error': 'Media operation failed'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/products/<int:product_id>/media/<int:media_id>', methods=['PUT', 'DELETE'])
@seller_required
def manage_single_product_media(product_id, media_id):
    seller_id = session['seller_id']

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        # Verify media belongs to seller's product
        cursor.execute("""
                       SELECT pm.* FROM product_media pm
                                            JOIN products p ON pm.product_id = p.id
                       WHERE pm.id = %s AND p.id = %s AND p.seller_id = %s
                       """, (media_id, product_id, seller_id))

        media_item = cursor.fetchone()
        if not media_item:
            return jsonify({'error': 'Media item not found'}), 404

        if request.method == 'PUT':
            data = request.json

            update_fields = []
            params = []

            if 'alt_text' in data:
                update_fields.append("alt_text = %s")
                params.append(data['alt_text'])

            if 'caption' in data:
                update_fields.append("caption = %s")
                params.append(data['caption'])

            if 'sort_order' in data:
                update_fields.append("sort_order = %s")
                params.append(data['sort_order'])

            if 'is_primary' in data:
                # If setting as primary, remove primary from other media
                if data['is_primary']:
                    cursor.execute("UPDATE product_media SET is_primary = FALSE WHERE product_id = %s", (product_id,))

                update_fields.append("is_primary = %s")
                params.append(data['is_primary'])

            if update_fields:
                params.extend([media_id, product_id, seller_id])
                query = f"""
                    UPDATE product_media pm
                    JOIN products p ON pm.product_id = p.id
                    SET {', '.join(update_fields)}
                    WHERE pm.id = %s AND p.id = %s AND p.seller_id = %s
                """

                cursor.execute(query, params)
                conn.commit()

                return jsonify({'message': 'Media updated successfully'})
            else:
                return jsonify({'error': 'No fields to update'}), 400

        elif request.method == 'DELETE':
            # Delete physical file
            file_path = media_item['file_url'].replace('/static/uploads/', '')
            full_path = os.path.join(app.config['UPLOAD_FOLDER'], file_path)

            if os.path.exists(full_path):
                os.remove(full_path)

            # Delete from database
            cursor.execute("DELETE FROM product_media WHERE id = %s", (media_id,))
            conn.commit()

            app.logger.info(f'Media deleted: {media_id} from product {product_id}')

            return jsonify({'message': 'Media deleted successfully'})

    except Exception as e:
        conn.rollback()
        app.logger.error(f'Single media operation error: {e}')
        return jsonify({'error': 'Media operation failed'}), 500
    finally:
        cursor.close()
        conn.close()

# Enhanced product creation with media
@app.route('/api/products-with-media', methods=['POST'])
@seller_required
def create_product_with_media():
    seller_id = session['seller_id']

    # This endpoint expects form data with both product info and files
    try:
        # Get product data
        product_data = {
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'price': request.form.get('price'),
            'category_id': request.form.get('category_id'),
            'conditions': request.form.get('conditions', 'good'),
            'stock_quantity': request.form.get('stock_quantity', 1)
        }

        # Validate required fields
        required_fields = ['name', 'description', 'price', 'category_id']
        for field in required_fields:
            if not product_data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = conn.cursor(dictionary=True)

        # Create product
        cursor.execute("""
                       INSERT INTO products (seller_id, category_id, name, description, price, conditions, stock_quantity)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                       """, (seller_id, product_data['category_id'], product_data['name'],
                             product_data['description'], product_data['price'],
                             product_data['conditions'], product_data['stock_quantity']))

        product_id = cursor.lastrowid

        # Handle media uploads
        if 'media' in request.files:
            files = request.files.getlist('media')
            primary_set = False

            for i, file in enumerate(files):
                if file.filename == '':
                    continue

                filename = secure_filename(file.filename)
                file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

                # Determine media type
                if file_ext in ALLOWED_IMAGE_EXTENSIONS:
                    media_type = 'image'
                    upload_dir = 'images'
                    mime_type = f'image/{file_ext}'
                elif file_ext in ALLOWED_VIDEO_EXTENSIONS:
                    media_type = 'video'
                    upload_dir = 'videos'
                    mime_type = f'video/{file_ext}'
                else:
                    continue  # Skip invalid files

                # Generate unique filename
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], upload_dir, unique_filename)
                file.save(filepath)

                # Get file size
                file_size = os.path.getsize(filepath)

                # Set first image as primary
                is_primary = not primary_set and media_type == 'image'
                if is_primary:
                    primary_set = True

                # Insert into database
                cursor.execute("""
                               INSERT INTO product_media (product_id, media_type, file_url, file_name, file_size,
                                                          mime_type, sort_order, is_primary, uploader_id, uploader_type)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'seller')
                               """, (product_id, media_type, f'/static/uploads/{upload_dir}/{unique_filename}',
                                     filename, file_size, mime_type, i, is_primary, seller_id))

        # Update seller stats
        cursor.execute("""
                       UPDATE seller_stats
                       SET total_products = total_products + 1
                       WHERE seller_id = %s
                       """, (seller_id,))

        conn.commit()

        app.logger.info(f'Product created with media: {product_id} by seller {seller_id}')

        return jsonify({
            'message': 'Product created successfully with media',
            'product_id': product_id
        }), 201

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        app.logger.error(f'Product with media creation error: {e}')
        return jsonify({'error': 'Product creation failed'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()



# Seller Dashboard Routes
@app.route('/api/seller/dashboard')
@seller_required
def seller_dashboard():
     seller_id = session.get('seller_id')
     if not seller_id:
         return jsonify({'error': 'Unauthorized'}), 401

     conn = get_db_connection()
     if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
     try:
         cursor = conn.cursor(dictionary=True)

        # Get seller stats
         cursor.execute("""
             SELECT total_revenue, total_orders, total_products, pending_orders
             FROM seller_stats
             WHERE seller_id = %s
         """, (seller_id,))
         
         stats = cursor.fetchone() or {
             'total_revenue': 0,
             'total_orders': 0,
             'total_products': 0,
             'pending_orders': 0
         }
         
         # Confirm seller exists
        # cursor.execute("SELECT id FROM sellers WHERE id = %s", (seller_id,))
        # if not cursor.fetchone():
         #    return jsonify({'error': 'Seller not found'}), 404

         
        # Get recent orders
         cursor.execute("""
              SELECT o.*, oi.product_id, oi.quantity, oi.status as item_status,
              p.name as product_name, u.full_name as customer_name
                       FROM orders o
              JOIN order_items oi ON o.id = oi.order_id
              JOIN products p ON oi.product_id = p.id
              JOIN users u ON o.user_id = u.id
              WHERE oi.seller_id = %s
              ORDER BY o.created_at DESC
              LIMIT 5
         """, (seller_id,))
         recent_orders = cursor.fetchall()
         
        # app.logger.info(f'Seller {seller_id} accessed dashboard')

         return jsonify({
             'stats': stats,
             'recent_orders': recent_orders
         })

     except Exception as e:
        app.logger.error(f'Seller dashboard error: {e}')
        return jsonify({'error': 'Failed to load dashboard'}), 500
     finally:
         cursor.close()
         conn.close()

@app.route('/api/seller/products', methods=['GET', 'POST'])
@seller_required
def manage_seller_products():
    seller_id = session.get('seller_id')
    if not seller_id:
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        if request.method == 'GET':
            cursor.execute("""
                           SELECT p.*, c.name as category_name
                           FROM products p
                                    LEFT JOIN categories c ON p.category_id = c.id
                           WHERE p.seller_id = %s
                           ORDER BY p.created_at DESC
                           """, (seller_id,))

            products = cursor.fetchall()

            for product in products:
                if product['images']:
                    product['images'] = json.loads(product['images'])
                else:
                    product['images'] = []

                if product['videos']:
                    product['videos'] = json.loads(product['videos'])
                else:
                    product['videos'] = []

            return jsonify({'products': products})

        elif request.method == 'POST':
            data = request.json

            required_fields = ['name', 'description', 'price', 'category_id']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'error': f'Missing required field: {field}'}), 400

            images = json.dumps(data.get('images', []))
            videos = json.dumps(data.get('videos', []))

            cursor.execute("""
                           INSERT INTO products (seller_id, category_id, name, description, price, original_price,
                                                 conditions, size, color, brand, material, images, videos, stock_quantity)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                           """, (seller_id, data.get('category_id'), data.get('name'), data.get('description'),
                                 data.get('price'), data.get('original_price'), data.get('conditions', 'good'),
                                 data.get('size'), data.get('color'), data.get('brand'), data.get('material'),
                                 images, videos, data.get('stock_quantity', 1)))

            # Update seller product count
            cursor.execute("""
                           UPDATE seller_stats
                           SET total_products = total_products + 1
                           WHERE seller_id = %s
                           """, (seller_id,))

            conn.commit()

            app.logger.info(f'New product added by seller {seller_id}')

            return jsonify({'message': 'Product added successfully'}), 201

    except Exception as e:
        conn.rollback()
        app.logger.error(f'Seller products error: {e}')
        return jsonify({'error': 'Product operation failed'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/seller/products/<int:product_id>', methods=['PUT', 'DELETE'])
@seller_required
def manage_seller_product(product_id):
    seller_id = session.get('seller_id')
    if not seller_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        # Verify product belongs to seller
        cursor.execute("SELECT id FROM products WHERE id = %s AND seller_id = %s", (product_id, seller_id))
        if not cursor.fetchone():
            return jsonify({'error': 'Product not found'}), 404

        if request.method == 'PUT':
            data = request.json

            update_fields = []
            params = []

            allowed_fields = ['name', 'description', 'price', 'original_price', 'category_id',
                              'conditions', 'size', 'color', 'brand', 'material', 'stock_quantity',
                              'images', 'videos', 'is_active']

            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = %s")
                    if field in ['images', 'videos']:
                        params.append(json.dumps(data[field]))
                    else:
                        params.append(data[field])

            if not update_fields:
                return jsonify({'error': 'No fields to update'}), 400

            params.extend([product_id, seller_id])
            query = f"UPDATE products SET {', '.join(update_fields)} WHERE id = %s AND seller_id = %s"

            cursor.execute(query, params)
            conn.commit()

            return jsonify({'message': 'Product updated successfully'})

        elif request.method == 'DELETE':
            cursor.execute("DELETE FROM products WHERE id = %s AND seller_id = %s", (product_id, seller_id))

            # Update seller product count
            cursor.execute("""
                           UPDATE seller_stats
                           SET total_products = GREATEST(0, total_products - 1)
                           WHERE seller_id = %s
                           """, (seller_id,))

            conn.commit()

            app.logger.info(f'Product {product_id} deleted by seller {seller_id}')

            return jsonify({'message': 'Product deleted successfully'})

    except Exception as e:
        conn.rollback()
        app.logger.error(f'Seller product operation error: {e}')
        return jsonify({'error': 'Product operation failed'}), 500
    finally:
        cursor.close()
        conn.close()

# File Upload Route
@app.route('/api/upload-media', methods=['POST'])
@login_required
def upload_media():
    if 'media' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('media')
    uploaded_files = {'images': [], 'videos': []}

    for file in files:
        if file.filename == '':
            continue

        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

        try:
            if file_ext in ALLOWED_IMAGE_EXTENSIONS:
                # Save image
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'images', unique_filename)
                file.save(filepath)
                uploaded_files['images'].append(f'/static/uploads/images/{unique_filename}')

            elif file_ext in ALLOWED_VIDEO_EXTENSIONS:
                # Save video
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'videos', unique_filename)
                file.save(filepath)
                uploaded_files['videos'].append(f'/static/uploads/videos/{unique_filename}')

            else:
                return jsonify({'error': f'Invalid file type: {file_ext}'}), 400

        except Exception as e:
            app.logger.error(f'File upload error: {e}')
            return jsonify({'error': 'Failed to upload files'}), 500

    app.logger.info(f'Media uploaded: {len(uploaded_files["images"])} images, {len(uploaded_files["videos"])} videos')
    return jsonify(uploaded_files)

# Static file serving
@app.route('/static/uploads/<path:filename>')
def serve_uploaded_files(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Categories Route
@app.route('/api/categories')
def get_categories():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM categories WHERE is_active = TRUE ORDER BY name")
        categories = cursor.fetchall()

        return jsonify({'categories': categories})

    except Exception as e:
        app.logger.error(f'Categories error: {e}')
        return jsonify({'error': 'Failed to fetch categories'}), 500
    finally:
        cursor.close()
        conn.close()

# Contact Route
@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    subject = data.get('subject')
    message = data.get('message')

    if not all([name, email, subject, message]):
        return jsonify({'error': 'All fields are required'}), 400

    try:
        # In a real application, you would send an email here
        # For now, we'll just log it
        app.logger.info(f'Contact form submitted: {subject} from {name} ({email})')

        # Store message in database if needed
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                           INSERT INTO messages (sender_name, sender_email, subject, message)
                           VALUES (%s, %s, %s, %s)
                           """, (name, email, subject, message))
            conn.commit()
            cursor.close()
            conn.close()

        return jsonify({'message': 'Thank you for your message. We will get back to you soon.'})

    except Exception as e:
        app.logger.error(f'Contact form error: {e}')
        return jsonify({'error': 'Failed to send message'}), 500

# Health check route
@app.route('/api/health')
def health_check():
    # Check database connection
    conn = get_db_connection()
    db_status = 'healthy' if conn else 'unhealthy'
    if conn:
        conn.close()

    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'timestamp': datetime.now().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Internal server error: {error}')
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'error': 'File too large'}), 413



if __name__ == '__main__':
    # Create upload directories
    create_upload_dirs()

    # Configure logging only once
    if not app.logger.handlers:
        import os, logging
        from logging.handlers import RotatingFileHandler

        os.makedirs("logs", exist_ok=True)
        handler = RotatingFileHandler(
            "logs/mzansi_thrift.log",
            maxBytes=1_000_000,
            backupCount=5,
            delay=True  # helps avoid Windows file locks
        )
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s in %(module)s: %(message)s"
        )
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)

    # Start the Flask application
    app.logger.info('Starting Mzansi Thrift Store API server...')
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
