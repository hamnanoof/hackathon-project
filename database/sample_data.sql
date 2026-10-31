-- Register a user through the application, then use that user's id below.
-- Replace :user_id with the registered user's integer id before running.
INSERT INTO products (user_id, name, description)
VALUES (:user_id, 'Acme Cloud', 'Cloud tools for growing teams');

INSERT INTO plans (product_id, name, price, billing_interval)
SELECT id, 'Starter', 19.00, 'month'
FROM products WHERE user_id = :user_id AND name = 'Acme Cloud';

INSERT INTO plans (product_id, name, price, billing_interval)
SELECT id, 'Business', 190.00, 'year'
FROM products WHERE user_id = :user_id AND name = 'Acme Cloud';
