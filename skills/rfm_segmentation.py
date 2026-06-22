# skills/rfm_segmentation.py - Optimized customer segmentation for large datasets
import sqlite3
import json
import datetime
import os

def run_rfm_segmentation():
    # 1. Connect to the database and retrieve transactions and max date
    conn = sqlite3.connect("ecommerce.db")
    cursor = conn.cursor()
    
    # Dynamically find the reference date (max purchase date in DB + 1 day)
    cursor.execute("SELECT MAX(purchase_date) FROM purchases")
    max_date_str = cursor.fetchone()[0]
    
    if not max_date_str:
        print("No transactions found in the database.")
        conn.close()
        return
        
    y, m, d = map(int, max_date_str.split("-"))
    max_date = datetime.date(y, m, d)
    reference_date = max_date + datetime.timedelta(days=1)
    print(f"Reference date dynamically set to: {reference_date} (Max purchase date: {max_date_str})")
    
    print("Fetching transaction history from database...")
    cursor.execute("SELECT customer_id, purchase_date, amount FROM purchases")
    transactions = cursor.fetchall()
    conn.close()
    
    print(f"Processing {len(transactions)} transactions...")
    
    # 2. Group transactions by customer (optimized date parsing)
    customer_data = {}
    for cust_id, date_str, amount in transactions:
        # Fast date parsing
        py, pm, pd = map(int, date_str.split("-"))
        purchase_date = datetime.date(py, pm, pd)
        recency_days = (reference_date - purchase_date).days
        
        if cust_id not in customer_data:
            customer_data[cust_id] = {
                "recency": recency_days,
                "frequency": 0,
                "monetary": 0.0
            }
        
        if recency_days < customer_data[cust_id]["recency"]:
            customer_data[cust_id]["recency"] = recency_days
            
        customer_data[cust_id]["frequency"] += 1
        customer_data[cust_id]["monetary"] += amount
        
    # 3. Calculate Quintiles (Scores from 1 to 5) - O(N) optimized ranking
    customers_list = list(customer_data.keys())
    n = len(customers_list)
    print(f"Calculating RFM scores for {n} unique customers...")
    
    # R_score: Recency (Lower days value is better -> higher score)
    sorted_by_r = sorted(customers_list, key=lambda x: customer_data[x]["recency"])
    # F_score: Frequency (Higher transaction count is better -> higher score)
    sorted_by_f = sorted(customers_list, key=lambda x: customer_data[x]["frequency"])
    # M_score: Monetary (Higher total spent is better -> higher score)
    sorted_by_m = sorted(customers_list, key=lambda x: customer_data[x]["monetary"])
    
    # Create O(1) rank maps to avoid O(N^2) list.index() lookups
    r_rank_map = {cust_id: rank for rank, cust_id in enumerate(sorted_by_r)}
    f_rank_map = {cust_id: rank for rank, cust_id in enumerate(sorted_by_f)}
    m_rank_map = {cust_id: rank for rank, cust_id in enumerate(sorted_by_m)}
    
    scores = {}
    for cust_id in customers_list:
        # Calculate scores in O(1) using the rank maps
        r_rank = r_rank_map[cust_id]
        r_score = 5 - int((r_rank / n) * 5)
        
        f_rank = f_rank_map[cust_id]
        f_score = int((f_rank / n) * 5) + 1
        
        m_rank = m_rank_map[cust_id]
        m_score = int((m_rank / n) * 5) + 1
        
        # Safeguard scores in range [1, 5]
        r_score = max(1, min(5, r_score))
        f_score = max(1, min(5, f_score))
        m_score = max(1, min(5, m_score))
        
        # Map to business segments
        segment = "Average"
        if r_score >= 4 and f_score >= 4 and m_score >= 4:
            segment = "Champions"
        elif r_score >= 3 and f_score >= 3 and m_score >= 3:
            segment = "Loyal Customers"
        elif r_score >= 4 and f_score <= 2:
            segment = "New Customers"
        elif r_score <= 2 and f_score >= 3:
            segment = "At Risk"
        elif r_score <= 2 and f_score <= 2:
            segment = "Lost Customers"
        elif r_score == 3 and f_score <= 2:
            segment = "Dormant Customers"
            
        scores[cust_id] = {
            "recency_days": customer_data[cust_id]["recency"],
            "frequency_count": customer_data[cust_id]["frequency"],
            "monetary_spent": round(customer_data[cust_id]["monetary"], 2),
            "r_score": r_score,
            "f_score": f_score,
            "m_score": m_score,
            "rfm_index": f"{r_score}{f_score}{m_score}",
            "segment": segment
        }
        
    # 4. Aggregate segment statistics
    segments_summary = {}
    for cust_id, info in scores.items():
        seg = info["segment"]
        if seg not in segments_summary:
            segments_summary[seg] = {
                "count": 0,
                "total_spend": 0.0,
                "avg_spend": 0.0
            }
        segments_summary[seg]["count"] += 1
        segments_summary[seg]["total_spend"] += info["monetary_spent"]
        
    # Calculate averages
    for seg, data in segments_summary.items():
        data["total_spend"] = round(data["total_spend"], 2)
        data["avg_spend"] = round(data["total_spend"] / data["count"], 2)
        
    output_data = {
        "metadata": {
            "calculated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_customers": n
        },
        "segments_summary": segments_summary,
        "customers": scores
    }
    
    # Save output to JSON file
    output_filename = "rfm_output.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    print(f"RFM Segmentation completed successfully. File '{output_filename}' generated.")
    print("Segment summary:")
    for seg, data in sorted(segments_summary.items(), key=lambda x: x[1]["count"], reverse=True):
        print(f" - {seg}: {data['count']} customers (Total spent: ${data['total_spend']:,.2f})")

if __name__ == "__main__":
    run_rfm_segmentation()
