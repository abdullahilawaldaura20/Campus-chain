-- CampusChain — Sample seed data (Postgres)
-- Matches the mock data used in the Phase 2 UI prototype.
-- Every seeded account uses the password "password123" — the hash
-- below is a real Werkzeug scrypt hash, so you can actually log in
-- with these accounts against /api/login for testing.

-- ============================================================
-- USERS  (id 1-5; id 5 is an admin)
-- ============================================================
INSERT INTO users (id, name, school_email, student_id, password_hash, role, phone, status) VALUES
(1, 'Amina Yusuf',  'amina.yusuf@school.edu.ng',  'CS/21/1043',  'scrypt:32768:8:1$9TDa7ECpBxsBPfTa$e8c501b6cc5170eaa481153df735d9f9cd543f8af09377f930765f0e22290be49310db1d733937e67ad8646b621c88038eba31272445b2888b9ec9ba4bedd76b', 'student', '080-000-0001', 'active'),
(2, 'Tunde B.',      'tunde.b@school.edu.ng',      'EEE/20/0871', 'scrypt:32768:8:1$9TDa7ECpBxsBPfTa$e8c501b6cc5170eaa481153df735d9f9cd543f8af09377f930765f0e22290be49310db1d733937e67ad8646b621c88038eba31272445b2888b9ec9ba4bedd76b', 'student', '080-000-0002', 'active'),
(3, 'Chidi O.',      'chidi.o@school.edu.ng',      'MCB/22/0342', 'scrypt:32768:8:1$9TDa7ECpBxsBPfTa$e8c501b6cc5170eaa481153df735d9f9cd543f8af09377f930765f0e22290be49310db1d733937e67ad8646b621c88038eba31272445b2888b9ec9ba4bedd76b', 'student', '080-000-0003', 'active'),
(4, 'Fatima A.',     'fatima.a@school.edu.ng',     'BCH/21/0559', 'scrypt:32768:8:1$9TDa7ECpBxsBPfTa$e8c501b6cc5170eaa481153df735d9f9cd543f8af09377f930765f0e22290be49310db1d733937e67ad8646b621c88038eba31272445b2888b9ec9ba4bedd76b', 'student', '080-000-0004', 'active'),
(5, 'Admin User',    'admin@school.edu.ng',        'ADMIN/0001',  'scrypt:32768:8:1$9TDa7ECpBxsBPfTa$e8c501b6cc5170eaa481153df735d9f9cd543f8af09377f930765f0e22290be49310db1d733937e67ad8646b621c88038eba31272445b2888b9ec9ba4bedd76b', 'admin',   NULL,           'active');

-- ============================================================
-- PRODUCTS  (matches Phase 2 marketplace mock cards)
-- ============================================================
INSERT INTO products (id, seller_id, title, description, price, category, condition, status) VALUES
(1, 2, 'Digital Electronics Textbook (4th Ed.)', 'Barely used, no highlights or torn pages. Covers everything in the 200-level syllabus.', 4500.00, 'Books', 'Like new', 'sold'),
(2, 4, 'Bluetooth Speaker — JBL Clip',            'Works perfectly, includes charging cable.',                                              6000.00, 'Electronics', 'Used - good', 'sold'),
(3, 3, 'Study Desk (wood, foldable)',             'Sturdy foldable desk, great for hostel rooms. Minor scratch on one corner.',             12000.00, 'Furniture', 'Used - fair', 'sold'),
(4, 1, 'HP Laptop Charger (65W)',                 'Original HP charger, tested working. Compatible with most HP Pavilion models.',            3500.00, 'Electronics', 'Used - good', 'available'),
(5, 2, 'Denim Jacket (Size M)',                   'Worn a handful of times, no stains or tears.',                                            5000.00, 'Fashion', 'Like new', 'available'),
(6, 1, 'Reading Lamp (LED, adjustable)',          'Three brightness settings, USB powered.',                                                 2500.00, 'Furniture', 'Like new', 'sold');

-- ============================================================
-- BLOCKCHAIN BLOCKS  (genesis + 3 completed trades)
-- Hashes below were computed with the exact algorithm in blockchain.py,
-- so validate_chain() will report this seed data as valid out of the box.
-- ============================================================
INSERT INTO blockchain_blocks (id, transaction_id, seller_id, buyer_id, product_id, timestamp, previous_hash, current_hash) VALUES
(1, 0, 0, 0, 0, '2026-07-20 09:00:00',
    '0000000000000000000000000000000000000000000000000000000000000000',
    '84c778621993b306a634a0e00e6435748d647bdd4bb1c3391e936a4091d078e6'),
(2, 1, 4, 1, 2, '2026-07-21 14:30:00',
    '84c778621993b306a634a0e00e6435748d647bdd4bb1c3391e936a4091d078e6',
    'fe5bce913a804d50fb4bd1fd30bd9382148e55460857177c91762b46fe8df85a'),
(3, 2, 3, 1, 3, '2026-07-23 11:15:00',
    'fe5bce913a804d50fb4bd1fd30bd9382148e55460857177c91762b46fe8df85a',
    '9478e5831d41c801f67ff36f864e5302f0c1766fdb35edb8f2d146ca5e2dfc69'),
(4, 3, 1, 5, 6, '2026-07-25 16:45:00',
    '9478e5831d41c801f67ff36f864e5302f0c1766fdb35edb8f2d146ca5e2dfc69',
    '14eb7047fb03fc28c3ff283bba7de05ef1d8e0b15c37e8352f1a37b6fcd8e5c6');

-- ============================================================
-- TRANSACTIONS
-- ============================================================
INSERT INTO transactions (id, product_id, seller_id, buyer_id, amount, status, block_id, created_at) VALUES
(1, 2, 4, 1, 6000.00,  'completed', 2, '2026-07-21 14:30:00'),
(2, 3, 3, 1, 12000.00, 'completed', 3, '2026-07-23 11:15:00'),
(3, 6, 1, 5, 2500.00,  'completed', 4, '2026-07-25 16:45:00');

-- ============================================================
-- REVIEWS
-- ============================================================
INSERT INTO reviews (transaction_id, reviewer_id, seller_id, rating, comment) VALUES
(1, 1, 4, 5, 'Fast handoff, item exactly as described.'),
(2, 1, 3, 4, 'Good communication, desk had a small scratch not mentioned.'),
(3, 5, 1, 5, 'Great seller, would buy from again.');

-- ============================================================
-- MESSAGES
-- ============================================================
INSERT INTO messages (sender_id, receiver_id, product_id, content, read_flag) VALUES
(1, 4, 2, 'Hi, is the speaker still available?', TRUE),
(4, 1, 2, 'Yes! Still have it, we can meet at the library.', TRUE),
(3, 1, 3, 'Sent you a buy request for the desk.', FALSE);

-- ============================================================
-- Reset auto-increment sequences to continue after the explicit IDs
-- inserted above — without this, the next INSERT from the app (e.g. a
-- new user registering) would collide with id=1.
-- ============================================================
SELECT setval(pg_get_serial_sequence('users', 'id'), (SELECT MAX(id) FROM users));
SELECT setval(pg_get_serial_sequence('products', 'id'), (SELECT MAX(id) FROM products));
SELECT setval(pg_get_serial_sequence('blockchain_blocks', 'id'), (SELECT MAX(id) FROM blockchain_blocks));
SELECT setval(pg_get_serial_sequence('transactions', 'id'), (SELECT MAX(id) FROM transactions));
