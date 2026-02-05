-- ======================================================
--  Mzansi Thrift Store - DDL, DML, and Indexes
-- ======================================================

-- Drop Procedures and Triggers before dropping tables
DROP PROCEDURE IF EXISTS UpdateProductViewCount;
DROP PROCEDURE IF EXISTS CalculateSellerStats;

DROP TRIGGER IF EXISTS after_order_item_insert;
DROP TRIGGER IF EXISTS after_review_insert;

-- Drop Views
DROP VIEW IF EXISTS product_details;
DROP VIEW IF EXISTS seller_performance;

-- Drop Tables in reverse dependency order (to clean up everything)
DROP TABLE IF EXISTS coupon_usage;
DROP TABLE IF EXISTS coupons;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS activity_logs;
DROP TABLE IF EXISTS seller_stats;
DROP TABLE IF EXISTS shipping;
DROP TABLE IF EXISTS payment_transactions;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS review_helpful;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS wishlist;
DROP TABLE IF EXISTS cart;
DROP TABLE IF EXISTS product_variants;
DROP TABLE IF EXISTS product_media;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS sellers;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS site_settings;


-- ============================
-- USERS (Buyers)
-- ============================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    province ENUM('Eastern Cape', 'Free State', 'Gauteng', 'KwaZulu-Natal', 'Limpopo', 'Mpumalanga', 'North West', 'Northern Cape', 'Western Cape'),
    postal_code VARCHAR(10),
    id_number VARCHAR(13),
    profile_picture VARCHAR(500),
    email_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(100),
    reset_token VARCHAR(100),
    reset_token_expiry TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    INDEX idx_users_email (email),
    INDEX idx_users_phone (phone)
);

-- ============================
-- SELLERS
-- ============================
CREATE TABLE sellers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    business_name VARCHAR(255) NOT NULL,
    business_type ENUM('individual', 'registered_business', 'non_profit') DEFAULT 'individual',
    business_description TEXT,
    business_logo VARCHAR(500),
    cover_image VARCHAR(500),
    tax_number VARCHAR(100),
    phone VARCHAR(20),
    id_number VARCHAR(13),
    bank_name VARCHAR(100),
    account_number VARCHAR(50),
    branch_code VARCHAR(10),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    province ENUM('Eastern Cape', 'Free State', 'Gauteng', 'KwaZulu-Natal', 'Limpopo', 'Mpumalanga', 'North West', 'Northern Cape', 'Western Cape'),
    postal_code VARCHAR(10),
    status ENUM('pending', 'approved', 'rejected', 'suspended') DEFAULT 'pending',
    rating DECIMAL(3,2) DEFAULT 0.00,
    total_sales INT DEFAULT 0,
    response_time INT DEFAULT 0, -- in hours
    verification_documents JSON, -- Store document URLs
    email_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(100),
    last_login TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_sellers_email (email),
    INDEX idx_sellers_status (status),
    INDEX idx_sellers_business_name (business_name)
);

-- ============================
-- CATEGORIES
-- ============================
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    image_url VARCHAR(500),
    icon VARCHAR(100),
    parent_id INT NULL,
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL,
    INDEX idx_categories_parent (parent_id),
    INDEX idx_categories_active (is_active)
);

-- ============================
-- PRODUCTS
-- ============================
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seller_id INT NOT NULL,
    category_id INT,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    short_description VARCHAR(500),
    price DECIMAL(10,2) NOT NULL CHECK (price > 0),
    original_price DECIMAL(10,2) CHECK (original_price > 0),
    conditions ENUM('excellent', 'good', 'fair', 'poor') NOT NULL DEFAULT 'good',
    size VARCHAR(50),
    color VARCHAR(50),
    brand VARCHAR(100),
    material VARCHAR(100),
    sku VARCHAR(100) UNIQUE,
    stock_quantity INT DEFAULT 1,
    min_order_quantity INT DEFAULT 1,
    max_order_quantity INT DEFAULT 10,
    weight DECIMAL(8,2) DEFAULT 0.5, -- in kg
    dimensions VARCHAR(100), -- "LxWxH" in cm
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    is_approved BOOLEAN DEFAULT TRUE, -- For admin approval
    view_count INT DEFAULT 0,
    purchase_count INT DEFAULT 0,
    wishlist_count INT DEFAULT 0,
    seo_title VARCHAR(255),
    seo_description TEXT,
    seo_keywords VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES sellers(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    INDEX idx_products_seller (seller_id),
    INDEX idx_products_category (category_id),
    INDEX idx_products_active (is_active),
    INDEX idx_products_featured (is_featured),
    INDEX idx_products_price (price),
    INDEX idx_products_created (created_at)
);

-- ============================
-- PRODUCT MEDIA
-- ============================
CREATE TABLE product_media (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    media_type ENUM('image', 'video') NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size INT, -- in bytes
    mime_type VARCHAR(100),
    alt_text VARCHAR(255),
    caption VARCHAR(500),
    sort_order INT DEFAULT 0,
    is_primary BOOLEAN DEFAULT FALSE,
    is_approved BOOLEAN DEFAULT TRUE,
    uploader_id INT, -- user/seller who uploaded
    uploader_type ENUM('seller', 'admin') DEFAULT 'seller',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    INDEX idx_media_product (product_id),
    INDEX idx_media_type (media_type),
    INDEX idx_media_primary (is_primary),
    INDEX idx_media_sort (sort_order)
);

-- ============================
-- PRODUCT VARIANTS
-- ============================
CREATE TABLE product_variants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    variant_name VARCHAR(255) NOT NULL, -- e.g., "Color", "Size"
    variant_value VARCHAR(255) NOT NULL, -- e.g., "Red", "Large"
    price_adjustment DECIMAL(10,2) DEFAULT 0,
    stock_quantity INT DEFAULT 0,
    sku_suffix VARCHAR(50), -- to be appended to main SKU
    image_url VARCHAR(500), -- variant-specific image
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE KEY unique_variant (product_id, variant_name, variant_value),
    INDEX idx_variants_product (product_id)
);

-- ============================
-- CART
-- ============================
CREATE TABLE cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    variant_id INT NULL,
    quantity INT DEFAULT 1 CHECK (quantity > 0),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (variant_id) REFERENCES product_variants(id) ON DELETE SET NULL,
    UNIQUE KEY unique_cart_item (user_id, product_id, variant_id),
    INDEX idx_cart_user (user_id),
    INDEX idx_cart_product (product_id)
);

-- ============================
-- WISHLIST
-- ============================
CREATE TABLE wishlist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE KEY unique_wishlist_item (user_id, product_id),
    INDEX idx_wishlist_user (user_id)
);

-- ============================
-- ORDERS
-- ============================
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_number VARCHAR(100) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    shipping_fee DECIMAL(10,2) DEFAULT 0,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    final_amount DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded') DEFAULT 'pending',
    shipping_address JSON NOT NULL,
    billing_address JSON,
    payment_method ENUM('credit_card', 'debit_card', 'eft', 'cash_on_delivery', 'paypal') DEFAULT 'credit_card',
    payment_status ENUM('pending', 'completed', 'failed', 'refunded', 'cancelled') DEFAULT 'pending',
    tracking_number VARCHAR(100),
    customer_notes TEXT,
    admin_notes TEXT,
    estimated_delivery DATE,
    delivered_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_orders_user (user_id),
    INDEX idx_orders_status (status),
    INDEX idx_orders_payment_status (payment_status),
    INDEX idx_orders_created (created_at),
    INDEX idx_orders_number (order_number)
);

-- ============================
-- ORDER ITEMS
-- ============================
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    seller_id INT NOT NULL,
    variant_id INT NULL,
    product_name VARCHAR(255) NOT NULL, -- snapshot of product name at time of order
    product_price DECIMAL(10,2) NOT NULL, -- snapshot of price at time of order
    variant_details JSON, -- snapshot of variant details
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'confirmed', 'shipped', 'delivered', 'cancelled', 'refunded') DEFAULT 'pending',
    tracking_number VARCHAR(100),
    shipped_at TIMESTAMP NULL,
    delivered_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (seller_id) REFERENCES sellers(id) ON DELETE CASCADE,
    FOREIGN KEY (variant_id) REFERENCES product_variants(id) ON DELETE SET NULL,
    INDEX idx_order_items_order (order_id),
    INDEX idx_order_items_seller (seller_id),
    INDEX idx_order_items_status (status)
);

-- ============================
-- REVIEWS
-- ============================
CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    user_id INT NOT NULL,
    order_item_id INT NOT NULL, -- ensure review is from actual purchase
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title VARCHAR(255),
    comment TEXT,
    media_urls JSON, -- URLs to review media (images/videos)
    is_approved BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    helpful_count INT DEFAULT 0,
    reported_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (order_item_id) REFERENCES order_items(id) ON DELETE CASCADE,
    UNIQUE KEY unique_review (order_item_id), -- One review per order item
    INDEX idx_reviews_product (product_id),
    INDEX idx_reviews_user (user_id),
    INDEX idx_reviews_rating (rating),
    INDEX idx_reviews_approved (is_approved)
);

-- ============================
-- REVIEW_HELPFUL
-- ============================
CREATE TABLE review_helpful (
    id INT AUTO_INCREMENT PRIMARY KEY,
    review_id INT NOT NULL,
    user_id INT NOT NULL,
    is_helpful BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_helpful (review_id, user_id),
    INDEX idx_helpful_review (review_id)
);

-- ============================
-- MESSAGES
-- ============================
CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    sender_type ENUM('user', 'seller') NOT NULL,
    receiver_type ENUM('user', 'seller') NOT NULL,
    subject VARCHAR(255),
    message TEXT NOT NULL,
    message_type ENUM('text', 'image', 'video', 'file') DEFAULT 'text',
    media_url VARCHAR(500),
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP NULL,
    parent_message_id INT NULL, -- for message threads
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES sellers(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_message_id) REFERENCES messages(id) ON DELETE SET NULL,
    INDEX idx_messages_sender (sender_id, sender_type),
    INDEX idx_messages_receiver (receiver_id, receiver_type),
    INDEX idx_messages_thread (parent_message_id),
    INDEX idx_messages_created (created_at)
);

-- ============================
-- PAYMENT TRANSACTIONS
-- ============================
CREATE TABLE payment_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    transaction_id VARCHAR(255) UNIQUE,
    payment_gateway ENUM('payfast', 'paystack', 'stripe', 'paypal') DEFAULT 'payfast',
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'ZAR',
    payment_method VARCHAR(50),
    status ENUM('pending', 'success', 'failed', 'cancelled', 'refunded') DEFAULT 'pending',
    gateway_response JSON, -- Raw response from payment gateway
    refund_amount DECIMAL(10,2) DEFAULT 0,
    refund_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_payments_order (order_id),
    INDEX idx_payments_status (status),
    INDEX idx_payments_created (created_at)
);

-- ============================
-- SHIPPING
-- ============================
CREATE TABLE shipping (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    carrier ENUM('post_office', 'courier_guy', 'ram', 'dsv', 'other') DEFAULT 'courier_guy',
    tracking_number VARCHAR(100),
    shipping_method VARCHAR(100),
    shipping_cost DECIMAL(10,2),
    insurance_cost DECIMAL(10,2) DEFAULT 0,
    package_weight DECIMAL(8,2),
    package_dimensions VARCHAR(100),
    estimated_delivery DATE,
    actual_delivery DATE,
    status ENUM('pending', 'label_created', 'in_transit', 'out_for_delivery', 'delivered', 'delayed', 'returned') DEFAULT 'pending',
    tracking_events JSON, -- Array of tracking events with timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_shipping_order (order_id),
    INDEX idx_shipping_status (status),
    INDEX idx_shipping_tracking (tracking_number)
);

-- ============================
-- SELLER STATS
-- ============================
CREATE TABLE seller_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seller_id INT NOT NULL,
    total_revenue DECIMAL(12,2) DEFAULT 0,
    total_orders INT DEFAULT 0,
    total_products INT DEFAULT 0,
    pending_orders INT DEFAULT 0,
    total_customers INT DEFAULT 0,
    average_rating DECIMAL(3,2) DEFAULT 0.00,
    response_rate DECIMAL(5,2) DEFAULT 0.00, -- percentage
    cancellation_rate DECIMAL(5,2) DEFAULT 0.00, -- percentage
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES sellers(id) ON DELETE CASCADE,
    UNIQUE KEY unique_seller_stats (seller_id),
    INDEX idx_stats_seller (seller_id)
);

-- ============================
-- ACTIVITY LOGS
-- ============================
CREATE TABLE activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    user_type ENUM('user', 'seller', 'admin') DEFAULT 'user',
    action VARCHAR(255) NOT NULL,
    description TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    resource_type VARCHAR(100), -- e.g., 'product', 'order'
    resource_id INT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_activity_user (user_id, user_type),
    INDEX idx_activity_action (action),
    INDEX idx_activity_created (created_at)
);

-- ============================
-- NOTIFICATIONS
-- ============================
CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    user_type ENUM('user', 'seller') NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type ENUM('order', 'message', 'system', 'promotion') DEFAULT 'system',
    related_id INT, -- ID of related resource (order_id, message_id, etc.)
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP NULL,
    action_url VARCHAR(500), -- URL for notification action
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_notifications_user (user_id, user_type),
    INDEX idx_notifications_read (is_read),
    INDEX idx_notifications_type (notification_type),
    INDEX idx_notifications_created (created_at)
);

-- ============================
-- COUPONS
-- ============================
CREATE TABLE coupons (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    discount_type ENUM('percentage', 'fixed') DEFAULT 'percentage',
    discount_value DECIMAL(10,2) NOT NULL,
    min_order_amount DECIMAL(10,2) DEFAULT 0,
    max_discount_amount DECIMAL(10,2),
    usage_limit INT DEFAULT 1,
    used_count INT DEFAULT 0,
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    applicable_categories JSON, -- Specific categories this coupon applies to
    excluded_products JSON, -- Products excluded from coupon
    created_by INT, -- Admin who created the coupon
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_coupons_code (code),
    INDEX idx_coupons_active (is_active),
    INDEX idx_coupons_validity (valid_from, valid_until)
);

-- ============================
-- COUPON_USAGE
-- ============================
CREATE TABLE coupon_usage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    coupon_id INT NOT NULL,
    user_id INT NOT NULL,
    order_id INT NOT NULL,
    discount_amount DECIMAL(10,2) NOT NULL,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (coupon_id) REFERENCES coupons(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    UNIQUE KEY unique_coupon_order (coupon_id, order_id),
    INDEX idx_coupon_usage_user (user_id),
    INDEX idx_coupon_usage_coupon (coupon_id)
);

-- ============================
-- SITE_SETTINGS
-- ============================
CREATE TABLE site_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setting_key VARCHAR(255) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type ENUM('string', 'number', 'boolean', 'json') DEFAULT 'string',
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    updated_by INT, -- Admin who updated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_settings_key (setting_key)
);

-- ======================================================
-- SAMPLE DATA
-- ======================================================

-- Insert Categories
INSERT IGNORE INTO categories (id, name, description, image_url, icon, sort_order) VALUES
(1, 'Clothing & Shoes', 'Pre-loved clothing, shoes and accessories with South African style', '/static/categories/clothing.jpg', 'tshirt', 1),
(2, 'Furniture & Home', 'Second-hand furniture and home decor items', '/static/categories/furniture.jpg', 'couch', 2),
(3, 'Electronics', 'Used electronics, gadgets and accessories', '/static/categories/electronics.jpg', 'laptop', 3),
(4, 'Books & Media', 'Books, CDs, DVDs and educational materials', '/static/categories/books.jpg', 'book', 4),
(5, 'Sports & Outdoor', 'Sports equipment and outdoor gear', '/static/categories/sports.jpg', 'basketball-ball', 5),
(6, 'Toys & Games', 'Toys, games and children''s items', '/static/categories/toys.jpg', 'gamepad', 6),
(7, 'Art & Collectibles', 'Local art, crafts and collectible items', '/static/categories/art.jpg', 'palette', 7),
(8, 'Jewelry & Watches', 'Pre-owned jewelry and timepieces', '/static/categories/jewelry.jpg', 'gem', 8);

-- Insert Sample Sellers
INSERT IGNORE INTO sellers (id, email, password_hash, business_name, business_type, phone, status, province, rating, total_sales) VALUES
(1, 'mzansi_thrift@example.com', '$2b$12$hashedpassword1', 'Mzansi Thrift Finds', 'individual', '+27-11-555-1234', 'approved', 'Gauteng', 4.8, 67),
(2, 'cape_vintage@example.com', '$2b$12$hashedpassword2', 'Cape Vintage Collective', 'registered_business', '+27-21-555-5678', 'approved', 'Western Cape', 4.6, 45),
(3, 'joburg_retro@example.com', '$2b$12$hashedpassword3', 'Joburg Retro Hub', 'individual', '+27-11-555-9012', 'approved', 'Gauteng', 4.9, 89),
(4, 'durban_treasures@example.com', '$2b$12$hashedpassword4', 'Durban Treasures', 'registered_business', '+27-31-555-3456', 'approved', 'KwaZulu-Natal', 4.7, 34);

-- Insert Sample Products
INSERT IGNORE INTO products (id, seller_id, category_id, name, description, short_description, price, original_price, conditions, size, color, brand, material, stock_quantity, weight, is_featured) VALUES
(1, 1, 1, 'Traditional Shweshwe Dress', 'Beautiful traditional Shweshwe fabric dress, perfect for special occasions. Authentic South African design with intricate patterns. Excellent condition with no stains or tears.', 'Authentic Shweshwe dress in excellent condition', 450.00, 650.00, 'excellent', 'M', 'Blue/White', 'Da Gama Textiles', 'Cotton', 1, 0.8, TRUE),
(2, 1, 1, 'Vintage Springbok Jersey', 'Classic green Springbok rugby jersey from 1990s. Great condition with minimal wear. Perfect for rugby enthusiasts and collectors.', 'Vintage Springbok rugby jersey from 1990s', 350.00, 500.00, 'good', 'L', 'Green', 'Springbok', 'Polyester', 1, 0.5, TRUE),
(3, 2, 7, 'Handcrafted Wire Art Car', 'Beautiful handcrafted wire art car made by local artisan. Unique South African craftsmanship. Each piece is individually made with attention to detail.', 'Local artisan handcrafted wire art car', 280.00, 350.00, 'excellent', '30cm', 'Silver', 'Local Art', 'Wire', 3, 0.3, TRUE),
(4, 2, 3, 'Samsung Galaxy Tablet', 'Used Samsung tablet in good working condition. Includes charger and protective case. Screen has minor scratches but fully functional.', 'Samsung tablet in good working condition', 1200.00, 1800.00, 'good', '10 inch', 'Black', 'Samsung', 'Metal/Glass', 1, 0.6, FALSE),
(5, 3, 4, 'Nelson Mandela Biography Set', 'Collection of Nelson Mandela biographies and autobiographies. Historical collection perfect for history enthusiasts. Some wear on covers but pages intact.', 'Mandela biography collection', 320.00, 450.00, 'fair', 'N/A', 'Mixed', 'Various', 'Paper', 2, 2.5, FALSE),
(6, 3, 5, 'Soccer Boots - Bafana Bafana', 'Professional soccer boots, barely used. Perfect for serious players. Excellent grip and comfort with minimal wear.', 'Professional soccer boots in excellent condition', 420.00, 600.00, 'excellent', '42', 'Yellow/Green', 'Adidas', 'Synthetic', 1, 0.7, TRUE);

-- Insert Product Media
INSERT IGNORE INTO product_media (product_id, media_type, file_url, file_name, file_size, mime_type, alt_text, is_primary, sort_order) VALUES
(1, 'image', '/static/uploads/images/shweshwe_dress_1.jpg', 'shweshwe_dress_1.jpg', 2048576, 'image/jpeg', 'Traditional Shweshwe Dress front view', TRUE, 1),
(1, 'image', '/static/uploads/images/shweshwe_dress_2.jpg', 'shweshwe_dress_2.jpg', 1987432, 'image/jpeg', 'Traditional Shweshwe Dress back view', FALSE, 2),
(2, 'image', '/static/uploads/images/springbok_jersey_1.jpg', 'springbok_jersey_1.jpg', 1876543, 'image/jpeg', 'Vintage Springbok Jersey front', TRUE, 1),
(3, 'image', '/static/uploads/images/wire_car_1.jpg', 'wire_car_1.jpg', 2234567, 'image/jpeg', 'Handcrafted Wire Art Car front view', TRUE, 1),
(4, 'image', '/static/uploads/images/tablet_1.jpg', 'tablet_1.jpg', 1987654, 'image/jpeg', 'Samsung Galaxy Tablet front', TRUE, 1),
(5, 'image', '/static/uploads/images/books_1.jpg', 'books_1.jpg', 1654321, 'image/jpeg', 'Nelson Mandela Biography Set collection', TRUE, 1),
(6, 'image', '/static/uploads/images/boots_1.jpg', 'boots_1.jpg', 1876543, 'image/jpeg', 'Soccer Boots front view', TRUE, 1);


-- Insert Seller Stats
INSERT IGNORE INTO seller_stats (seller_id, total_revenue, total_orders, total_products, pending_orders, total_customers, average_rating, response_rate) VALUES 
(1, 12500.00, 67, 23, 3, 45, 4.8, 95.5),
(2, 8900.00, 45, 18, 2, 32, 4.6, 92.3),
(3, 15600.00, 89, 34, 5, 67, 4.9, 97.8),
(4, 5400.00, 28, 15, 1, 22, 4.7, 90.1);

-- Insert Site Settings
INSERT IGNORE INTO site_settings (setting_key, setting_value, setting_type, description, is_public) VALUES
('site_name', 'Mzansi Thrift Store', 'string', 'The name of the e-commerce site', TRUE),
('site_description', 'South Africa''s premier online thrift store', 'string', 'Site description for SEO', TRUE),
('currency', 'ZAR', 'string', 'Default currency', TRUE),
('shipping_enabled', 'true', 'boolean', 'Enable/disable shipping', TRUE),
('max_upload_size', '52428800', 'number', 'Maximum file upload size in bytes', FALSE),
('allowed_image_types', '["jpg", "jpeg", "png", "gif", "webp"]', 'json', 'Allowed image file types', FALSE),
('allowed_video_types', '["mp4", "mov", "avi", "webm"]', 'json', 'Allowed video file types', FALSE),
('auto_approve_products', 'true', 'boolean', 'Automatically approve new products', FALSE),
('commission_rate', '10', 'number', 'Platform commission rate percentage', FALSE);

-- Insert Sample Coupons
INSERT IGNORE INTO coupons (code, description, discount_type, discount_value, min_order_amount, max_discount_amount, usage_limit, valid_until) VALUES
('WELCOME10', 'Welcome discount for new customers', 'percentage', 10.00, 200.00, 100.00, 1, DATE_ADD(NOW(), INTERVAL 30 DAY)),
('SAVE20', 'Save 20% on your first order', 'percentage', 20.00, 500.00, 200.00, 1, DATE_ADD(NOW(), INTERVAL 60 DAY)),
('FREESHIP', 'Free shipping on orders over R300', 'fixed', 65.00, 300.00, 65.00, 100, DATE_ADD(NOW(), INTERVAL 90 DAY));

-- Create Views for common queries
CREATE OR REPLACE VIEW product_details AS
SELECT 
    p.*,
    c.name as category_name,
    s.business_name as seller_name,
    s.rating as seller_rating,
    s.province as seller_province,
    (SELECT COUNT(*) FROM reviews r WHERE r.product_id = p.id AND r.is_approved = TRUE) as review_count,
    (SELECT AVG(r.rating) FROM reviews r WHERE r.product_id = p.id AND r.is_approved = TRUE) as average_rating,
    (SELECT file_url FROM product_media pm WHERE pm.product_id = p.id AND pm.is_primary = TRUE LIMIT 1) as primary_image
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN sellers s ON p.seller_id = s.id
WHERE p.is_active = TRUE AND p.is_approved = TRUE;

CREATE OR REPLACE VIEW seller_performance AS
SELECT 
    s.*,
    ss.total_revenue,
    ss.total_orders,
    ss.total_products,
    ss.pending_orders,
    ss.average_rating,
    ss.response_rate,
    (SELECT COUNT(*) FROM products p WHERE p.seller_id = s.id AND p.is_active = TRUE) as active_products,
    (SELECT COUNT(*) FROM reviews r JOIN products p ON r.product_id = p.id WHERE p.seller_id = s.id) as total_reviews
FROM sellers s
LEFT JOIN seller_stats ss ON s.id = ss.seller_id
WHERE s.status = 'approved';

-- Create Indexes for better performance
CREATE INDEX idx_product_media_product ON product_media(product_id);
CREATE INDEX idx_product_media_primary ON product_media(is_primary);
CREATE INDEX idx_orders_dates ON orders(created_at, updated_at);
CREATE INDEX idx_sellers_rating ON sellers(rating);
CREATE INDEX idx_products_price_range ON products(price, is_active);
CREATE INDEX idx_order_items_dates ON order_items(created_at);
CREATE INDEX idx_reviews_dates ON reviews(created_at);