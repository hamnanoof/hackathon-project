-- Active subscriptions and their plans for a given customer.
SELECT subscriptions.id, products.name AS product, plans.name AS plan,
       plans.price, plans.billing_interval, subscriptions.start_date
FROM subscriptions
JOIN plans ON plans.id = subscriptions.plan_id
JOIN products ON products.id = plans.product_id
WHERE subscriptions.user_id = :user_id AND subscriptions.status = 'active';

-- Outstanding invoices for a given customer.
SELECT invoice_number, amount, due_date
FROM invoices
WHERE user_id = :user_id AND status = 'pending'
ORDER BY due_date;

-- Total completed payments for a given customer.
SELECT COALESCE(SUM(amount), 0) AS total_collected
FROM payments
WHERE user_id = :user_id AND status = 'completed';
