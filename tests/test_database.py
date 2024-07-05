import unittest
import sqlite3
from app.database import create_tables, insert_sample_data, get_connection

class DatabaseTestCase(unittest.TestCase):
    """Unit Testing The Database Set Up"""
    def setUp(self):
        """Building the database and inserting sample data"""
        create_tables()
        insert_sample_data()

    def test_order_table(self):
        """Testing how many results we get on conditioning"""
        conn = get_connection()
        c = conn.cursor()
        c.execute('SELECT order_ID FROM orders where status="Processing"')
        results = c.fetchall()
        self.assertEqual(len(results), 1)
        conn.close()
    def test_order_table_actual(self):
        """Testing what result we get on conditioning"""
        conn = get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM orders where status="Delivered"')
        results = c.fetchall()
        self.assertEqual(results, [('54321', 'Delivered')])
        conn.close()

    def test_order_table_all(self):
        """Testing how many results we get from fetching all the files"""
        conn = get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM orders')
        results = c.fetchall()
        self.assertEqual(len(results), 3)
        conn.close()
    def test_order_table_all_actual(self):
        """Testing the results we get from fetching all the records"""
        conn = get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM orders')
        results = c.fetchall()
        self.assertEqual(results, [('12345', 'Shipped'), ('67890', 'Processing'), ('54321', 'Delivered') ])
        conn.close()



if __name__ == '__main__':
    unittest.main()
