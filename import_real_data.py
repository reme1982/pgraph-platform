# import_real_data.py - Imports real Olist Brazilian E-commerce dataset into SQLite
import pandas as pd
import sqlite3
import os
import shutil

def main():
    # 1. Hacer copia de seguridad de la base de datos simulada anterior
    mock_db_name = "ecommerce_mock.db"
    prod_db_name = "ecommerce.db"
    
    if os.path.exists(prod_db_name):
        print(f"Backing up existing simulated database to '{mock_db_name}'...")
        shutil.copyfile(prod_db_name, mock_db_name)
        
    print("Loading Olist datasets from CSV files...")
    # Rutas absolutas a los archivos CSV de Olist
    data_dir = r"C:\Users\hcard\OneDrive\Escritorio\📊 Ciencia de Datos & GIS\DataAnalyst2026\Customer Churn Analysis_Claude\Data"
    
    customers_path = os.path.join(data_dir, "olist_customers_dataset.csv")
    orders_path = os.path.join(data_dir, "olist_orders_dataset.csv")
    payments_path = os.path.join(data_dir, "olist_order_payments_dataset.csv")
    
    # 2. Cargar los CSV con pandas
    try:
        df_customers = pd.read_csv(customers_path, usecols=["customer_id", "customer_unique_id"])
        df_orders = pd.read_csv(orders_path, usecols=["order_id", "customer_id", "order_purchase_timestamp", "order_status"])
        df_payments = pd.read_csv(payments_path, usecols=["order_id", "payment_value"])
    except Exception as e:
        print(f"Error loading Olist CSV files: {e}")
        return
        
    print("Processing and merging datasets...")
    # Filtrar solo pedidos completados/entregados si es necesario (o todos los que tengan pago)
    # df_orders = df_orders[df_orders["order_status"] == "delivered"]
    
    # Unir pedidos con clientes (para obtener el customer_unique_id)
    df_merged = pd.merge(df_orders, df_customers, on="customer_id", how="inner")
    
    # Unir con pagos (para obtener el monto de la compra)
    df_final = pd.merge(df_merged, df_payments, on="order_id", how="inner")
    
    # Extraer y renombrar columnas necesarias
    # Para el análisis RFM, agrupamos por customer_unique_id (el ID del cliente real)
    df_purchases = pd.DataFrame()
    df_purchases["customer_id"] = df_final["customer_unique_id"]
    
    # Convertir el timestamp a formato de fecha YYYY-MM-DD
    df_purchases["purchase_date"] = pd.to_datetime(df_final["order_purchase_timestamp"]).dt.strftime("%Y-%m-%d")
    df_purchases["amount"] = df_final["payment_value"]
    
    # Eliminar valores nulos
    df_purchases = df_purchases.dropna()
    
    print(f"Total purchases joined: {len(df_purchases)}")
    print(f"Unique customers loaded: {df_purchases['customer_id'].nunique()}")
    
    # 3. Guardar en la base de datos SQLite
    print(f"Writing to new SQLite database '{prod_db_name}'...")
    conn = sqlite3.connect(prod_db_name)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS purchases")
    cursor.execute("""
        CREATE TABLE purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            purchase_date TEXT NOT NULL,
            amount REAL NOT NULL
        )
    """)
    conn.commit()
    
    # Escribir el dataframe en la tabla de compras
    df_purchases.to_sql("purchases", conn, if_exists="append", index=False)
    
    # Imprimir un resumen rápido de verificación
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT customer_id), SUM(amount) FROM purchases")
    total_rows, unique_custs, total_revenue = cursor.fetchone()
    print("Database verification:")
    print(f" - Saved purchases: {total_rows}")
    print(f" - Unique customers in DB: {unique_custs}")
    print(f" - Total revenue in DB: ${total_revenue:,.2f}")
    
    conn.close()
    print("Import complete! Your agent is now backed by real Brazilian E-commerce transactions.")

if __name__ == "__main__":
    main()
