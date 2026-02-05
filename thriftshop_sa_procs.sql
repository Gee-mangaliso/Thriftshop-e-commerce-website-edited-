-- ======================================================
--  Stored Procedures
-- ======================================================
DROP PROCEDURE IF EXISTS UpdateProductViewCount;
DROP PROCEDURE IF EXISTS CalculateSellerStats;

-- Start custom delimiter
DELIMITER //

CREATE PROCEDURE UpdateProductViewCount(IN product_id INT)
BEGIN
    UPDATE products SET view_count = view_count + 1 WHERE id = product_id;
END//

CREATE PROCEDURE CalculateSellerStats(IN seller_id INT)
BEGIN
    DECLARE total_rev DECIMAL(12,2);
    DECLARE total_ord INT;
    DECLARE total_prod INT;
    DECLARE pending_ord INT;
    DECLARE avg_rating DECIMAL(3,2);
    
    -- Select aggregated data into declared variables
    SELECT 
        COALESCE(SUM(oi.total_price), 0),
        COUNT(DISTINCT o.id),
        COUNT(DISTINCT p.id),
        COUNT(DISTINCT CASE WHEN oi.status = 'pending' THEN oi.id END),
        COALESCE(AVG(r.rating), 0)
    INTO total_rev, total_ord, total_prod, pending_ord, avg_rating
    FROM sellers s
    LEFT JOIN products p ON s.id = p.seller_id
    LEFT JOIN order_items oi ON p.id = oi.product_id
    LEFT JOIN orders o ON oi.order_id = o.id
    LEFT JOIN reviews r ON p.id = r.product_id
    WHERE s.id = seller_id;
    
    -- Insert or Update seller_stats
    INSERT INTO seller_stats (seller_id, total_revenue, total_orders, total_products, pending_orders, average_rating)
    VALUES (seller_id, total_rev, total_ord, total_prod, pending_ord, avg_rating)
    ON DUPLICATE KEY UPDATE
        total_revenue = total_rev,
        total_orders = total_ord,
        total_products = total_prod,
        pending_orders = pending_ord,
        average_rating = avg_rating,
        last_updated = NOW();
END//

-- Reset delimiter
DELIMITER ;

-- ... all DROP PROCEDURE statements ...
-- Start custom delimiter
DELIMITER //

CREATE PROCEDURE UpdateProductViewCount(IN product_id INT)
BEGIN
    UPDATE products SET view_count = view_count + 1 WHERE id = product_id;
END//

CREATE PROCEDURE CalculateSellerStats(IN seller_id INT)
BEGIN
    -- ... SQL code ...
END//

-- Reset delimiter
DELIMITER ;