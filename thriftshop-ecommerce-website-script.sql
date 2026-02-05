USE THRIFTSHOP_SA;
SELECT * FROM PRODUCTS;
ALTER TABLE products ADD COLUMN featured TINYINT(1) DEFAULT 0;
UPDATE products SET featured = 1 WHERE id = 7;
SELECT FEATURED FROM PRODUCTS;
SELECT id, featured, is_active, seller_id 
FROM products 
WHERE id = 7;
SELECT id, status FROM sellers WHERE id = 6;
UPDATE sellers SET status = 'approved' WHERE id = 6;
UPDATE products SET featured = 1 WHERE id IN (1,2,3,4,5,6);
SELECT id, name, images
FROM products
WHERE images LIKE '%.webf%';




