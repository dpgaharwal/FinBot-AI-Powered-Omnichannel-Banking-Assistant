-- Customers
INSERT INTO customers VALUES
('c1', 'Happy Gaharwal', 'happy@finbot.com', '9876543210', 'verified', NOW()),
('c2', 'Priya Sharma', 'priya@finbot.com', '9876543211', 'verified', NOW()),
('c3', 'Rahul Verma', 'rahul@finbot.com', '9876543212', 'pending', NOW());

-- Accounts
INSERT INTO accounts VALUES
('a1', 'c1', 'ACC001234567890', 'savings', 45230.50, 'active', NOW()),
('a2', 'c1', 'ACC001234567891', 'current', 125000.00, 'active', NOW()),
('a3', 'c2', 'ACC001234567892', 'savings', 89000.00, 'active', NOW()),
('a4', 'c3', 'ACC001234567893', 'salary', 12000.00, 'active', NOW());

-- Transactions
INSERT INTO transactions VALUES
('t1', 'a1', 'credit', 5000.00, 'Salary credit', 'success', NOW()),
('t2', 'a1', 'debit', 1200.00, 'Amazon purchase', 'success', NOW()),
('t3', 'a1', 'debit', 500.00, 'Electricity bill', 'success', NOW()),
('t4', 'a1', 'credit', 2000.00, 'Freelance payment', 'success', NOW()),
('t5', 'a2', 'debit', 15000.00, 'Rent payment', 'success', NOW()),
('t6', 'a2', 'credit', 50000.00, 'Client payment', 'success', NOW()),
('t7', 'a3', 'debit', 3000.00, 'Zomato order', 'failed', NOW()),
('t8', 'a3', 'credit', 10000.00, 'FD maturity', 'success', NOW());

-- Loans
INSERT INTO loans VALUES
('l1', 'c1', 'personal', 200000.00, 5500.00, 24, 'active', DATE_ADD(NOW(), INTERVAL 30 DAY), NOW()),
('l2', 'c2', 'home', 5000000.00, 42000.00, 180, 'active', DATE_ADD(NOW(), INTERVAL 15 DAY), NOW()),
('l3', 'c3', 'car', 800000.00, 15000.00, 36, 'active', DATE_ADD(NOW(), INTERVAL 7 DAY), NOW());