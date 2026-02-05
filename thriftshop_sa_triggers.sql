-- ======================================================
--  Triggers
-- ======================================================
DROP TRIGGER IF EXISTS after_order_item_insert;
DROP TRIGGER IF EXISTS after_review_insert;

-- Start custom delimiter
DELIMITER //

CREATE TRIGGER after_order_item_insert
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    -- Update product purchase count
    UPDATE products 
    SET purchase_count = purchase_count + NEW.quantity 
    WHERE id = NEW.product_id;
    
    -- Update seller stats (Calls the stored procedure created earlier)
    CALL CalculateSellerStats(NEW.seller_id);
END//



CREATE TRIGGER after_review_insert
AFTER INSERT ON reviews
FOR EACH ROW
BEGIN
    -- Update product average rating
    UPDATE products p
    SET p.rating = (
        SELECT AVG(r.rating) 
        FROM reviews r 
        WHERE r.product_id = NEW.product_id AND r.is_approved = TRUE
    )
    WHERE p.id = NEW.product_id;
    
    -- Update seller stats (Recalculate seller stats on new review)
    CALL CalculateSellerStats(
        (SELECT seller_id FROM products WHERE id = NEW.product_id LIMIT 1)
    );
END//

-- Reset delimiter
DELIMITER ;

-- ... all DROP TRIGGER statements ...
-- Start custom delimiter
DELIMITER //

CREATE TRIGGER after_order_item_insert
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    -- ... SQL code ...
END//

CREATE TRIGGER after_review_insert
AFTER INSERT ON reviews
FOR EACH ROW
BEGIN
    -- ... SQL code ...
END//

-- Reset delimiter
DELIMITER ;