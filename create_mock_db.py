import sqlite3
import random
import datetime

def generate_mock_data():
    conn = sqlite3.connect("ecommerce.db")
    cursor = conn.cursor()
    
    # Create the purchases table
    cursor.execute("DROP TABLE IF EXISTS purchases")
    cursor.execute("""
        CREATE TABLE purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            purchase_date TEXT NOT NULL,
            amount REAL NOT NULL
        )
    """)
    
    # Initialize seed for reproducibility
    random.seed(42)
    
    # Generate 100 customers with different behavior patterns
    customers = [f"CUST-{i:03d}" for i in range(1, 101)]
    
    # Today's date reference: 2026-06-20
    today = datetime.date(2026, 6, 20)
    
    purchases = []
    
    for customer in customers:
        # Define customer profile to simulate real RFM patterns
        cust_num = int(customer.split("-")[1])
        
        if cust_num <= 15:
            # Profile: Champions / Loyal (frequent purchases, high amounts, very recent)
            num_purchases = random.randint(8, 15)
            min_days_ago = 1
            max_days_ago = 30
            amount_range = (80.0, 250.0)
        elif cust_num <= 35:
            # Profile: New Customers (recent purchases, few transactions, varied amounts)
            num_purchases = random.randint(1, 2)
            min_days_ago = 2
            max_days_ago = 15
            amount_range = (20.0, 100.0)
        elif cust_num <= 60:
            # Profile: At Risk of Churn (frequent purchases before, but last transaction was long ago)
            num_purchases = random.randint(5, 10)
            min_days_ago = 90
            max_days_ago = 360
            amount_range = (40.0, 150.0)
        elif cust_num <= 80:
            # Profile: Sleeping / Lost Customers (few transactions, long ago, low amounts)
            num_purchases = random.randint(1, 3)
            min_days_ago = 180
            max_days_ago = 365
            amount_range = (15.0, 50.0)
        else:
            # Profile: Average (normal pattern)
            num_purchases = random.randint(2, 6)
            min_days_ago = 10
            max_days_ago = 120
            amount_range = (30.0, 120.0)
            
        # Generate individual transactions
        for _ in range(num_purchases):
            days_ago = random.randint(min_days_ago, max_days_ago)
            purchase_date = today - datetime.timedelta(days=days_ago)
            amount = round(random.uniform(*amount_range), 2)
            purchases.append((customer, purchase_date.strftime("%Y-%m-%d"), amount))
            
    # Insert records into database
    cursor.executemany(
        "INSERT INTO purchases (customer_id, purchase_date, amount) VALUES (?, ?, ?)",
        purchases
    )
    
    conn.commit()
    
    # Print summary
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT customer_id), SUM(amount) FROM purchases")
    total_purchases, distinct_customers, total_revenue = cursor.fetchone()
    print("Database 'ecommerce.db' generated successfully.")
    print(f"Total purchases generated: {total_purchases}")
    print(f"Unique customers: {distinct_customers}")
    print(f"Total simulated revenue: ${total_revenue:,.2f}")
    
    conn.close()

if __name__ == "__main__":
    generate_mock_data()
