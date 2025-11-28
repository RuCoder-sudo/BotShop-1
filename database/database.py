import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Tuple
import config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(config.DATABASE_NAME, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            phone TEXT,
            role TEXT DEFAULT 'pending',
            balance REAL DEFAULT 0,
            blocked INTEGER DEFAULT 0,
            verification_status TEXT DEFAULT 'none',
            referrer_id INTEGER,
            referral_code TEXT UNIQUE,
            created_at TEXT,
            last_active TEXT,
            FOREIGN KEY(referrer_id) REFERENCES users(user_id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TEXT,
            created_by INTEGER,
            FOREIGN KEY(created_by) REFERENCES users(user_id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT,
            created_by INTEGER,
            FOREIGN KEY(country_id) REFERENCES countries(id) ON DELETE CASCADE,
            FOREIGN KEY(created_by) REFERENCES users(user_id),
            UNIQUE(country_id, name)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS districts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT,
            created_by INTEGER,
            FOREIGN KEY(city_id) REFERENCES cities(id) ON DELETE CASCADE,
            FOREIGN KEY(created_by) REFERENCES users(user_id),
            UNIQUE(city_id, name)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            parent_id INTEGER,
            created_at TEXT,
            created_by INTEGER,
            FOREIGN KEY(parent_id) REFERENCES categories(id) ON DELETE CASCADE,
            FOREIGN KEY(created_by) REFERENCES users(user_id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            category_id INTEGER,
            country_id INTEGER NOT NULL,
            city_id INTEGER NOT NULL,
            district_id INTEGER NOT NULL,
            image_path TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(seller_id) REFERENCES users(user_id),
            FOREIGN KEY(category_id) REFERENCES categories(id),
            FOREIGN KEY(country_id) REFERENCES countries(id),
            FOREIGN KEY(city_id) REFERENCES cities(id),
            FOREIGN KEY(district_id) REFERENCES districts(id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            buyer_id INTEGER NOT NULL,
            seller_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            payment_method TEXT,
            delivery_address TEXT,
            phone TEXT,
            created_at TEXT,
            completed_at TEXT,
            FOREIGN KEY(buyer_id) REFERENCES users(user_id),
            FOREIGN KEY(seller_id) REFERENCES users(user_id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            added_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(product_id) REFERENCES products(id),
            UNIQUE(user_id, product_id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            buyer_id INTEGER NOT NULL,
            seller_id INTEGER NOT NULL,
            product_id INTEGER,
            rating REAL NOT NULL,
            comment TEXT,
            created_at TEXT,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(buyer_id) REFERENCES users(user_id),
            FOREIGN KEY(seller_id) REFERENCES users(user_id),
            FOREIGN KEY(product_id) REFERENCES products(id),
            UNIQUE(order_id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            added_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(product_id) REFERENCES products(id),
            UNIQUE(user_id, product_id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS promo_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            discount_percent REAL,
            discount_amount REAL,
            usage_limit INTEGER,
            used_count INTEGER DEFAULT 0,
            valid_until TEXT,
            created_by INTEGER,
            created_at TEXT,
            FOREIGN KEY(created_by) REFERENCES users(user_id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS verification_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            requested_at TEXT,
            processed_at TEXT,
            processed_by INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(processed_by) REFERENCES users(user_id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT,
            message TEXT,
            status TEXT DEFAULT 'open',
            created_at TEXT,
            closed_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS balance_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            requested_at TEXT,
            confirmed_at TEXT,
            processed_at TEXT,
            processed_by INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(processed_by) REFERENCES users(user_id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscriber_id INTEGER NOT NULL,
            seller_id INTEGER NOT NULL,
            created_at TEXT,
            FOREIGN KEY(subscriber_id) REFERENCES users(user_id),
            FOREIGN KEY(seller_id) REFERENCES users(user_id),
            UNIQUE(subscriber_id, seller_id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complainant_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            product_id INTEGER,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            resolved_at TEXT,
            FOREIGN KEY(complainant_id) REFERENCES users(user_id),
            FOREIGN KEY(target_id) REFERENCES users(user_id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS delivery_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            price REAL NOT NULL DEFAULT 0,
            updated_at TEXT,
            updated_by INTEGER,
            FOREIGN KEY(updated_by) REFERENCES users(user_id)
        )''')
        
        cursor.execute('''INSERT OR IGNORE INTO delivery_settings (id, price, updated_at) 
                          VALUES (1, 0, ?)''', (datetime.now().isoformat(),))
        
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_products_location 
                          ON products(country_id, city_id, district_id)''')
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_products_seller 
                          ON products(seller_id)''')
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_orders_buyer 
                          ON orders(buyer_id)''')
        cursor.execute('''CREATE INDEX IF NOT EXISTS idx_orders_seller 
                          ON orders(seller_id)''')
        
        try:
            cursor.execute('ALTER TABLE orders ADD COLUMN delivery_cost REAL DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        self.conn.commit()

    def add_user(self, user_id: int, username: str, first_name: str, referral_code: str):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO users 
                     (user_id, username, first_name, referral_code, created_at, last_active)
                     VALUES (?, ?, ?, ?, ?, ?)
                     ON CONFLICT(user_id) DO UPDATE SET
                     username = excluded.username,
                     first_name = excluded.first_name,
                     last_active = excluded.last_active''',
                     (user_id, username, first_name, referral_code, 
                      datetime.now().isoformat(), datetime.now().isoformat()))
        self.conn.commit()

    def get_user(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

    def update_user_role(self, user_id: int, role: str):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET role = ? WHERE user_id = ?', (role, user_id))
        self.conn.commit()

    def create_verification_request(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO verification_requests 
                     (user_id, requested_at) VALUES (?, ?)''',
                     (user_id, datetime.now().isoformat()))
        self.conn.commit()

    def get_pending_verifications(self):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT vr.*, u.username, u.first_name 
                          FROM verification_requests vr
                          JOIN users u ON vr.user_id = u.user_id
                          WHERE vr.status = 'pending'
                          ORDER BY vr.requested_at DESC''')
        return cursor.fetchall()

    def approve_verification(self, request_id: int, admin_id: int):
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id FROM verification_requests WHERE id = ?', (request_id,))
        result = cursor.fetchone()
        if result:
            user_id = result['user_id']
            cursor.execute('''UPDATE verification_requests 
                         SET status = 'approved', processed_at = ?, processed_by = ?
                         WHERE id = ?''',
                         (datetime.now().isoformat(), admin_id, request_id))
            cursor.execute('''UPDATE users SET role = 'manager', verification_status = 'verified'
                         WHERE user_id = ?''', (user_id,))
            self.conn.commit()
            return user_id
        return None

    def reject_verification(self, request_id: int, admin_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''UPDATE verification_requests 
                     SET status = 'rejected', processed_at = ?, processed_by = ?
                     WHERE id = ?''',
                     (datetime.now().isoformat(), admin_id, request_id))
        self.conn.commit()

    def add_country(self, name: str, admin_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO countries (name, created_at, created_by)
                     VALUES (?, ?, ?)''',
                     (name, datetime.now().isoformat(), admin_id))
        self.conn.commit()
        return cursor.lastrowid

    def get_countries(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM countries ORDER BY name')
        return cursor.fetchall()

    def add_city(self, country_id: int, name: str, admin_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO cities (country_id, name, created_at, created_by)
                     VALUES (?, ?, ?, ?)''',
                     (country_id, name, datetime.now().isoformat(), admin_id))
        self.conn.commit()
        return cursor.lastrowid

    def get_cities(self, country_id: int):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM cities WHERE country_id = ? ORDER BY name', (country_id,))
        return cursor.fetchall()

    def add_district(self, city_id: int, name: str, admin_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO districts (city_id, name, created_at, created_by)
                     VALUES (?, ?, ?, ?)''',
                     (city_id, name, datetime.now().isoformat(), admin_id))
        self.conn.commit()
        return cursor.lastrowid

    def get_districts(self, city_id: int):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM districts WHERE city_id = ? ORDER BY name', (city_id,))
        return cursor.fetchall()

    def add_category(self, name: str, parent_id: Optional[int], admin_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO categories (name, parent_id, created_at, created_by)
                     VALUES (?, ?, ?, ?)''',
                     (name, parent_id, datetime.now().isoformat(), admin_id))
        self.conn.commit()
        return cursor.lastrowid

    def get_categories(self, parent_id: Optional[int] = None):
        cursor = self.conn.cursor()
        if parent_id is None:
            cursor.execute('SELECT * FROM categories WHERE parent_id IS NULL ORDER BY name')
        else:
            cursor.execute('SELECT * FROM categories WHERE parent_id = ? ORDER BY name', (parent_id,))
        return cursor.fetchall()
    
    def get_category_by_id(self, category_id: int):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM categories WHERE id = ?', (category_id,))
        return cursor.fetchone()
    
    def get_category_path(self, category_id: int):
        path = []
        current_id = category_id
        while current_id:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM categories WHERE id = ?', (current_id,))
            category = cursor.fetchone()
            if category:
                path.insert(0, category)
                current_id = category['parent_id']
            else:
                break
        return path

    def add_product(self, seller_id: int, name: str, description: str, price: float,
                   stock: int, category_id: int, country_id: int, city_id: int,
                   district_id: int, image_path: Optional[str] = None):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO products 
                     (seller_id, name, description, price, stock, category_id,
                      country_id, city_id, district_id, image_path, created_at, updated_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (seller_id, name, description, price, stock, category_id,
                      country_id, city_id, district_id, image_path,
                      datetime.now().isoformat(), datetime.now().isoformat()))
        self.conn.commit()
        product_id = cursor.lastrowid
        logger.info(f"Product created: ID={product_id}, seller={seller_id}, name='{name[:30]}...'")
        return product_id

    def get_products_by_location(self, country_id: int, city_id: int, district_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT p.*, u.username as seller_name, c.name as category_name
                          FROM products p
                          JOIN users u ON p.seller_id = u.user_id
                          LEFT JOIN categories c ON p.category_id = c.id
                          WHERE p.country_id = ? AND p.city_id = ? AND p.district_id = ?
                          AND p.status = 'active' AND p.stock > 0''',
                       (country_id, city_id, district_id))
        return cursor.fetchall()

    def get_sellers_by_location(self, country_id: int, city_id: int, district_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT DISTINCT u.user_id, u.username, u.first_name,
                          COUNT(p.id) as product_count,
                          AVG(r.rating) as avg_rating
                          FROM users u
                          JOIN products p ON u.user_id = p.seller_id
                          LEFT JOIN ratings r ON u.user_id = r.seller_id
                          WHERE p.country_id = ? AND p.city_id = ? AND p.district_id = ?
                          AND p.status = 'active' AND u.role = 'manager'
                          GROUP BY u.user_id''',
                       (country_id, city_id, district_id))
        return cursor.fetchall()

    def get_seller_products(self, seller_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT p.*, c.name as category_name,
                          co.name as country_name, ci.name as city_name, d.name as district_name
                          FROM products p
                          LEFT JOIN categories c ON p.category_id = c.id
                          LEFT JOIN countries co ON p.country_id = co.id
                          LEFT JOIN cities ci ON p.city_id = ci.id
                          LEFT JOIN districts d ON p.district_id = d.id
                          WHERE p.seller_id = ? AND p.status = 'active'
                          ORDER BY p.created_at DESC''',
                       (seller_id,))
        return cursor.fetchall()

    def search_products(self, query: str):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT p.*, u.username as seller_username, c.name as category_name,
                          co.name as country_name, ci.name as city_name, d.name as district_name
                          FROM products p
                          JOIN users u ON p.seller_id = u.user_id
                          LEFT JOIN categories c ON p.category_id = c.id
                          LEFT JOIN countries co ON p.country_id = co.id
                          LEFT JOIN cities ci ON p.city_id = ci.id
                          LEFT JOIN districts d ON p.district_id = d.id
                          WHERE (p.name LIKE ? OR p.description LIKE ?)
                          AND p.status = 'active' AND p.stock > 0''',
                       (f'%{query}%', f'%{query}%'))
        return cursor.fetchall()

    def get_product(self, product_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT p.*, u.username as seller_username, u.first_name as seller_first_name,
                          c.name as category_name, co.name as country_name, 
                          ci.name as city_name, d.name as district_name,
                          AVG(r.rating) as avg_rating, COUNT(r.id) as rating_count
                          FROM products p
                          JOIN users u ON p.seller_id = u.user_id
                          LEFT JOIN categories c ON p.category_id = c.id
                          LEFT JOIN countries co ON p.country_id = co.id
                          LEFT JOIN cities ci ON p.city_id = ci.id
                          LEFT JOIN districts d ON p.district_id = d.id
                          LEFT JOIN ratings r ON p.id = r.product_id
                          WHERE p.id = ?
                          GROUP BY p.id''',
                       (product_id,))
        return cursor.fetchone()

    def get_seller_rating(self, seller_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT AVG(rating) as avg_rating, COUNT(*) as rating_count
                          FROM ratings WHERE seller_id = ?''', (seller_id,))
        return cursor.fetchone()

    def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO cart (user_id, product_id, quantity, added_at)
                     VALUES (?, ?, ?, ?)
                     ON CONFLICT(user_id, product_id) DO UPDATE SET
                     quantity = quantity + excluded.quantity''',
                     (user_id, product_id, quantity, datetime.now().isoformat()))
        self.conn.commit()

    def get_cart(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT c.*, p.name, p.price, p.stock, p.seller_id,
                          u.username as seller_username, u.username as seller_name, u.first_name as seller_first_name
                          FROM cart c
                          JOIN products p ON c.product_id = p.id
                          JOIN users u ON p.seller_id = u.user_id
                          WHERE c.user_id = ?''', (user_id,))
        return cursor.fetchall()

    def clear_cart(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def create_order(self, buyer_id: int, seller_id: int,
                    product_id: int, quantity: int, total_price: float,
                    payment_method: str = 'balance', delivery_address: str = '',
                    phone: str = '', buyer_name: str = '', delivery_cost: float = 0):
        cursor = self.conn.cursor()
        
        import random
        import string
        order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        cursor.execute('SELECT COUNT(*) as count FROM orders WHERE order_number = ?', (order_number,))
        if cursor.fetchone()['count'] > 0:
            order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        cursor.execute('''INSERT INTO orders 
                     (order_number, buyer_id, seller_id, product_id, quantity,
                      total_price, payment_method, delivery_address, phone, delivery_cost, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (order_number, buyer_id, seller_id, product_id, quantity,
                      total_price, payment_method, delivery_address, phone, delivery_cost,
                      datetime.now().isoformat()))
        self.conn.commit()
        return cursor.lastrowid

    def get_user_orders(self, user_id: int, role: str = 'buyer'):
        cursor = self.conn.cursor()
        if role == 'buyer':
            cursor.execute('''SELECT o.*, p.name as product_name, u.username as seller_name
                              FROM orders o
                              JOIN products p ON o.product_id = p.id
                              JOIN users u ON o.seller_id = u.user_id
                              WHERE o.buyer_id = ?
                              ORDER BY o.created_at DESC''', (user_id,))
        else:
            cursor.execute('''SELECT o.*, p.name as product_name, u.username as buyer_name
                              FROM orders o
                              JOIN products p ON o.product_id = p.id
                              JOIN users u ON o.buyer_id = u.user_id
                              WHERE o.seller_id = ?
                              ORDER BY o.created_at DESC''', (user_id,))
        return cursor.fetchall()

    def add_rating(self, order_id: int, buyer_id: int, seller_id: int,
                  product_id: int, rating: float, comment: str = ''):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO ratings 
                     (order_id, buyer_id, seller_id, product_id, rating, comment, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (order_id, buyer_id, seller_id, product_id, rating, comment,
                      datetime.now().isoformat()))
        self.conn.commit()
    
    def check_order_has_rating(self, order_id: int):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM ratings WHERE order_id = ?', (order_id,))
        return cursor.fetchone()['count'] > 0

    def get_all_users(self, role: Optional[str] = None):
        cursor = self.conn.cursor()
        if role:
            cursor.execute('SELECT * FROM users WHERE role = ? ORDER BY created_at DESC', (role,))
        else:
            cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        return cursor.fetchall()

    def block_user(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET blocked = 1 WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def unblock_user(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET blocked = 0 WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def update_balance(self, user_id: int, amount: float, transaction_type: str, description: str = ''):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        cursor.execute('''INSERT INTO transactions (user_id, amount, type, description, created_at)
                     VALUES (?, ?, ?, ?, ?)''',
                     (user_id, amount, transaction_type, description, datetime.now().isoformat()))
        self.conn.commit()

    def get_statistics(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) as total_users FROM users')
        total_users = cursor.fetchone()['total_users']
        
        cursor.execute('SELECT COUNT(*) as total_orders FROM orders')
        total_orders = cursor.fetchone()['total_orders']
        
        cursor.execute('SELECT SUM(total_price) as total_revenue FROM orders WHERE status = "completed"')
        total_revenue = cursor.fetchone()['total_revenue'] or 0
        
        cursor.execute('SELECT COUNT(*) as total_products FROM products WHERE status = "active"')
        total_products = cursor.fetchone()['total_products']
        
        return {
            'total_users': total_users,
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'total_products': total_products
        }

    def update_country(self, country_id: int, new_name: str):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE countries SET name = ? WHERE id = ?', (new_name, country_id))
        self.conn.commit()

    def delete_country(self, country_id: int):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM countries WHERE id = ?', (country_id,))
        self.conn.commit()

    def get_country(self, country_id: int):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM countries WHERE id = ?', (country_id,))
        return cursor.fetchone()

    def update_city(self, city_id: int, new_name: str):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE cities SET name = ? WHERE id = ?', (new_name, city_id))
        self.conn.commit()

    def delete_city(self, city_id: int):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM cities WHERE id = ?', (city_id,))
        self.conn.commit()

    def get_city(self, city_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT c.*, co.name as country_name 
                          FROM cities c 
                          JOIN countries co ON c.country_id = co.id 
                          WHERE c.id = ?''', (city_id,))
        return cursor.fetchone()

    def update_district(self, district_id: int, new_name: str):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE districts SET name = ? WHERE id = ?', (new_name, district_id))
        self.conn.commit()

    def delete_district(self, district_id: int):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM districts WHERE id = ?', (district_id,))
        self.conn.commit()

    def get_district(self, district_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT d.*, c.name as city_name, co.name as country_name
                          FROM districts d 
                          JOIN cities c ON d.city_id = c.id
                          JOIN countries co ON c.country_id = co.id
                          WHERE d.id = ?''', (district_id,))
        return cursor.fetchone()

    def update_category(self, category_id: int, new_name: str):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE categories SET name = ? WHERE id = ?', (new_name, category_id))
        self.conn.commit()

    def count_all_subcategories(self, category_id: int, visited: set = None) -> int:
        if visited is None:
            visited = set()
        
        if category_id in visited:
            return 0
        
        visited.add(category_id)
        count = 0
        subcategories = self.get_categories(category_id)
        count += len(subcategories)
        for subcat in subcategories:
            count += self.count_all_subcategories(subcat['id'], visited)
        return count
    
    def get_all_category_ids(self, category_id: int, visited: set = None) -> list:
        if visited is None:
            visited = set()
        
        if category_id in visited:
            return []
        
        visited.add(category_id)
        result = [category_id]
        subcategories = self.get_categories(category_id)
        for subcat in subcategories:
            result.extend(self.get_all_category_ids(subcat['id'], visited))
        return result
    
    def delete_category(self, category_id: int) -> tuple:
        cursor = self.conn.cursor()
        
        all_category_ids = self.get_all_category_ids(category_id)
        
        affected_products = 0
        for cat_id in all_category_ids:
            cursor.execute('SELECT COUNT(*) as count FROM products WHERE category_id = ?', (cat_id,))
            affected_products += cursor.fetchone()['count']
            cursor.execute('UPDATE products SET category_id = NULL WHERE category_id = ?', (cat_id,))
        
        deleted_categories = len(all_category_ids) - 1
        
        for cat_id in reversed(all_category_ids):
            cursor.execute('DELETE FROM categories WHERE id = ?', (cat_id,))
        
        self.conn.commit()
        return (deleted_categories, affected_products)

    def get_category(self, category_id: int):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM categories WHERE id = ?', (category_id,))
        return cursor.fetchone()

    def get_order(self, order_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT o.*, p.name as product_name, 
                          u1.username as buyer_username, u2.username as seller_username
                          FROM orders o
                          JOIN products p ON o.product_id = p.id
                          JOIN users u1 ON o.buyer_id = u1.user_id
                          JOIN users u2 ON o.seller_id = u2.user_id
                          WHERE o.id = ?''', (order_id,))
        return cursor.fetchone()

    def get_complaints(self, status: str = None):
        cursor = self.conn.cursor()
        if status:
            cursor.execute('''SELECT c.*, 
                              u1.username as complainant_name, u1.first_name as complainant_fname,
                              u2.username as target_name, u2.first_name as target_fname,
                              p.name as product_name
                              FROM complaints c
                              JOIN users u1 ON c.complainant_id = u1.user_id
                              JOIN users u2 ON c.target_id = u2.user_id
                              LEFT JOIN products p ON c.product_id = p.id
                              WHERE c.status = ?
                              ORDER BY c.created_at DESC''', (status,))
        else:
            cursor.execute('''SELECT c.*,
                              u1.username as complainant_name, u1.first_name as complainant_fname,
                              u2.username as target_name, u2.first_name as target_fname,
                              p.name as product_name
                              FROM complaints c
                              JOIN users u1 ON c.complainant_id = u1.user_id
                              JOIN users u2 ON c.target_id = u2.user_id
                              LEFT JOIN products p ON c.product_id = p.id
                              ORDER BY c.created_at DESC''')
        return cursor.fetchall()

    def resolve_complaint(self, complaint_id: int, admin_id: int = None):
        cursor = self.conn.cursor()
        
        cursor.execute("PRAGMA table_info(complaints)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'resolved_by' in columns:
            cursor.execute('''UPDATE complaints 
                              SET status = 'resolved', resolved_at = ?, resolved_by = ? 
                              WHERE id = ?''',
                           (datetime.now().isoformat(), admin_id, complaint_id))
        else:
            cursor.execute('ALTER TABLE complaints ADD COLUMN resolved_by INTEGER')
            cursor.execute('''UPDATE complaints 
                              SET status = 'resolved', resolved_at = ?, resolved_by = ? 
                              WHERE id = ?''',
                           (datetime.now().isoformat(), admin_id, complaint_id))
        
        self.conn.commit()
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Complaint {complaint_id} resolved by admin {admin_id}")

    def adjust_user_balance(self, user_id: int, amount: float, 
                             transaction_type: str, description: str, admin_id: int = None):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        cursor = self.conn.cursor()
        
        user = self.get_user(user_id)
        if not user:
            raise ValueError("User not found")
        
        if transaction_type == 'debit' and user['balance'] < amount:
            raise ValueError("Insufficient funds")
        
        if transaction_type == 'credit':
            new_balance = user['balance'] + amount
        elif transaction_type == 'debit':
            new_balance = user['balance'] - amount
        else:
            raise ValueError("Invalid transaction type")
        
        cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', (new_balance, user_id))
        
        full_description = f"{description} | Admin ID: {admin_id}" if admin_id else description
        
        cursor.execute('''INSERT INTO transactions 
                          (user_id, amount, type, description, created_at)
                          VALUES (?, ?, ?, ?, ?)''',
                       (user_id, amount if transaction_type == 'credit' else -amount,
                        transaction_type, full_description, datetime.now().isoformat()))
        
        self.conn.commit()
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Balance adjusted for user {user_id}: {transaction_type} {amount} by admin {admin_id}")
        
        return new_balance

    def get_user_transactions(self, user_id: int, limit: int = 10):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT * FROM transactions 
                          WHERE user_id = ? 
                          ORDER BY created_at DESC 
                          LIMIT ?''', (user_id, limit))
        return cursor.fetchall()

    def get_blocked_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE blocked = 1 ORDER BY created_at DESC')
        return cursor.fetchall()

    def update_product(self, product_id: int, **kwargs):
        cursor = self.conn.cursor()
        
        allowed_fields = ['name', 'description', 'price', 'stock', 'category_id', 
                         'country_id', 'city_id', 'district_id', 'image_path', 'status']
        
        updates = []
        values = []
        
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                updates.append(f"{key} = ?")
                values.append(value)
        
        if not updates:
            return False
        
        updates.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(product_id)
        
        query = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        self.conn.commit()
        
        return cursor.rowcount > 0

    def delete_product(self, product_id: int):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_all_products(self, status: Optional[str] = None, limit: int = 100):
        cursor = self.conn.cursor()
        
        if status:
            cursor.execute('''SELECT p.*, u.username as seller_name, c.name as category_name,
                              co.name as country_name, ci.name as city_name, d.name as district_name
                              FROM products p
                              JOIN users u ON p.seller_id = u.user_id
                              LEFT JOIN categories c ON p.category_id = c.id
                              LEFT JOIN countries co ON p.country_id = co.id
                              LEFT JOIN cities ci ON p.city_id = ci.id
                              LEFT JOIN districts d ON p.district_id = d.id
                              WHERE p.status = ?
                              ORDER BY p.created_at DESC
                              LIMIT ?''', (status, limit))
        else:
            cursor.execute('''SELECT p.*, u.username as seller_name, c.name as category_name,
                              co.name as country_name, ci.name as city_name, d.name as district_name
                              FROM products p
                              JOIN users u ON p.seller_id = u.user_id
                              LEFT JOIN categories c ON p.category_id = c.id
                              LEFT JOIN countries co ON p.country_id = co.id
                              LEFT JOIN cities ci ON p.city_id = ci.id
                              LEFT JOIN districts d ON p.district_id = d.id
                              ORDER BY p.created_at DESC
                              LIMIT ?''', (limit,))
        
        return cursor.fetchall()

    def moderate_product(self, product_id: int, new_status: str, admin_id: int = None):
        cursor = self.conn.cursor()
        
        if new_status not in ['active', 'inactive', 'pending', 'rejected']:
            raise ValueError("Invalid status")
        
        cursor.execute('''UPDATE products SET status = ?, updated_at = ? WHERE id = ?''',
                      (new_status, datetime.now().isoformat(), product_id))
        self.conn.commit()
        
        logger.info(f"Product {product_id} moderated to {new_status} by admin {admin_id}")
        return cursor.rowcount > 0

    def search_products_advanced(self, query: str = '', category_id: Optional[int] = None,
                                 min_price: Optional[float] = None, max_price: Optional[float] = None,
                                 country_id: Optional[int] = None, city_id: Optional[int] = None,
                                 district_id: Optional[int] = None):
        cursor = self.conn.cursor()
        
        sql = '''SELECT p.*, u.username as seller_name, c.name as category_name,
                 co.name as country_name, ci.name as city_name, d.name as district_name
                 FROM products p
                 JOIN users u ON p.seller_id = u.user_id
                 LEFT JOIN categories c ON p.category_id = c.id
                 LEFT JOIN countries co ON p.country_id = co.id
                 LEFT JOIN cities ci ON p.city_id = ci.id
                 LEFT JOIN districts d ON p.district_id = d.id
                 WHERE p.status = 'active' AND p.stock > 0'''
        
        params = []
        
        if query:
            sql += ' AND (p.name LIKE ? OR p.description LIKE ?)'
            params.extend([f'%{query}%', f'%{query}%'])
        
        if category_id:
            sql += ' AND p.category_id = ?'
            params.append(category_id)
        
        if min_price is not None:
            sql += ' AND p.price >= ?'
            params.append(min_price)
        
        if max_price is not None:
            sql += ' AND p.price <= ?'
            params.append(max_price)
        
        if country_id:
            sql += ' AND p.country_id = ?'
            params.append(country_id)
        
        if city_id:
            sql += ' AND p.city_id = ?'
            params.append(city_id)
        
        if district_id:
            sql += ' AND p.district_id = ?'
            params.append(district_id)
        
        sql += ' ORDER BY p.created_at DESC LIMIT 50'
        
        cursor.execute(sql, params)
        return cursor.fetchall()

    def get_user_subscriptions(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT s.*, u.username, u.first_name
                          FROM subscriptions s
                          JOIN users u ON s.seller_id = u.user_id
                          WHERE s.subscriber_id = ?''', (user_id,))
        return cursor.fetchall()

    def get_seller_subscribers(self, seller_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT s.*, u.username, u.first_name
                          FROM subscriptions s
                          JOIN users u ON s.subscriber_id = u.user_id
                          WHERE s.seller_id = ?''', (seller_id,))
        return cursor.fetchall()

    def add_subscription(self, subscriber_id: int, seller_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO subscriptions (subscriber_id, seller_id, created_at)
                     VALUES (?, ?, ?)''',
                     (subscriber_id, seller_id, datetime.now().isoformat()))
        self.conn.commit()

    def remove_subscription(self, subscriber_id: int, seller_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''DELETE FROM subscriptions 
                     WHERE subscriber_id = ? AND seller_id = ?''',
                     (subscriber_id, seller_id))
        self.conn.commit()

    def create_balance_request(self, user_id: int, amount: float):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO balance_requests 
                     (user_id, amount, requested_at, status)
                     VALUES (?, ?, ?, 'waiting_confirmation')''',
                     (user_id, amount, datetime.now().isoformat()))
        self.conn.commit()
        return cursor.lastrowid

    def confirm_balance_request(self, request_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''UPDATE balance_requests 
                     SET status = 'pending', confirmed_at = ?
                     WHERE id = ? AND status = 'waiting_confirmation' ''',
                     (datetime.now().isoformat(), request_id))
        self.conn.commit()
        return cursor.rowcount > 0

    def cancel_balance_request(self, request_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''UPDATE balance_requests 
                     SET status = 'cancelled', processed_at = ?
                     WHERE id = ?''',
                     (datetime.now().isoformat(), request_id))
        self.conn.commit()

    def get_pending_balance_requests(self):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT br.*, u.username, u.first_name, u.balance
                          FROM balance_requests br
                          JOIN users u ON br.user_id = u.user_id
                          WHERE br.status = 'pending'
                          ORDER BY br.confirmed_at DESC''')
        return cursor.fetchall()

    def get_balance_request(self, request_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT br.*, u.username, u.first_name, u.balance
                          FROM balance_requests br
                          JOIN users u ON br.user_id = u.user_id
                          WHERE br.id = ?''', (request_id,))
        return cursor.fetchone()

    def approve_balance_request(self, request_id: int, admin_id: int):
        cursor = self.conn.cursor()
        request = self.get_balance_request(request_id)
        
        if not request or request['status'] != 'pending':
            return False
        
        try:
            self.adjust_user_balance(
                user_id=request['user_id'],
                amount=request['amount'],
                transaction_type='credit',
                description=f'Пополнение баланса (запрос #{request_id})',
                admin_id=admin_id
            )
            
            cursor.execute('''UPDATE balance_requests 
                         SET status = 'approved', processed_at = ?, processed_by = ?
                         WHERE id = ?''',
                         (datetime.now().isoformat(), admin_id, request_id))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error approving balance request {request_id}: {e}")
            return False

    def reject_balance_request(self, request_id: int, admin_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''UPDATE balance_requests 
                     SET status = 'rejected', processed_at = ?, processed_by = ?
                     WHERE id = ?''',
                     (datetime.now().isoformat(), admin_id, request_id))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_delivery_price(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT price FROM delivery_settings WHERE id = 1')
        result = cursor.fetchone()
        return result['price'] if result else 0

    def update_delivery_price(self, price: float, admin_id: int):
        cursor = self.conn.cursor()
        cursor.execute('''UPDATE delivery_settings 
                     SET price = ?, updated_at = ?, updated_by = ?
                     WHERE id = 1''',
                     (price, datetime.now().isoformat(), admin_id))
        self.conn.commit()

    def close(self):
        self.conn.close()
