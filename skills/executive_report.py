# skills/executive_report.py - Executive report generation skill
import json
import os
import datetime

def generate_report():
    input_filename = "rfm_output.json"
    if not os.path.exists(input_filename):
        print(f"Error: Output file '{input_filename}' not found. Please run the RFM segmentation skill first.")
        return None
        
    with open(input_filename, "r", encoding="utf-8") as f:
        rfm_data = json.load(f)
        
    calculated_at = rfm_data["metadata"]["calculated_at"]
    total_customers = rfm_data["metadata"]["total_customers"]
    segments = rfm_data["segments_summary"]
    
    # Create the /reports/ directory if it doesn't exist
    os.makedirs("reports", exist_ok=True)
    
    report_date = datetime.datetime.now().strftime("%Y-%m-%d")
    report_path = f"reports/customer_retention_report_{report_date}.md"
    
    # Build the Markdown report content in English
    md_content = f"""# Executive Customer Segmentation & Retention Report
*Generated on: {calculated_at}*  
*Total Customers Analyzed: {total_customers} unique profiles*

---

## 1. RFM Customer Segmentation Summary

| Customer Segment | No. of Customers | Total Revenue | Average Spend per Customer |
| :--- | :---: | :---: | :---: |
"""
    
    for seg, data in segments.items():
        md_content += f"| **{seg}** | {data['count']} | ${data['total_spend']:,.2f} | ${data['avg_spend']:,.2f} |\n"
        
    md_content += """
---

## 2. Customer Segment Marketing & Retention Recommendations

Based on the distribution of Recency, Frequency, and Monetary (RFM) scores, we suggest the following targeted business strategies:

### 🏆 1. Champions
- **Diagnosis:** High recency, frequency, and spend. These are your most valuable advocates.
- **Key Actions:**
  - Build an exclusive VIP rewards program.
  - Provide early access to new product releases or beta features.
  - Ask for product testimonials and reviews to leverage word-of-mouth marketing.

### ❤️ 2. Loyal Customers
- **Diagnosis:** Regular purchasing pattern with stable spending.
- **Key Actions:**
  - Leverage cross-selling and up-selling recommendations based on historical purchases.
  - Send personalized promotions (e.g., birthday discounts).
  - Target with loyalty points and referral rewards.

### 🌱 3. New Customers
- **Diagnosis:** High recency but low frequency. Still in the onboarding stage.
- **Key Actions:**
  - Send an automated welcome email sequence introducing the brand values.
  - Offer a special discount coupon to incentivize their second purchase.
  - Provide helpful product guides or customer service contact info.

### ⚠️ 4. At Risk
- **Diagnosis:** Used to buy frequently and spend high amounts, but haven't purchased in months.
- **Key Actions:**
  - **Urgent Reactivation Campaign:** Send personalized "We miss you" email campaigns.
  - Offer time-limited, high-value discount codes.
  - Send feedback surveys to identify any customer service friction.

### 💤 5. Dormant Customers
- **Diagnosis:** Low recency and sporadic purchases.
- **Key Actions:**
  - Send friendly reminders of popular/trending items.
  - Engage with content marketing to rebuild interest before trying hard sales.

### ❌ 6. Lost Customers
- **Diagnosis:** Very low recency, frequency, and spend.
- **Key Actions:**
  - Run a single, low-cost automated email recovery campaign.
  - Do not invest significant advertising budget into retargeting this group if acquisition costs are high.

---

## 3. Recommended Next Steps

1. **CRM Synchronization:** Export lists of customers in the **At Risk** segment to trigger the reactivation email sequence.
2. **Impact Assessment:** Review metrics in 30 days to see if the churn rate in the "At Risk" category decreases and if retention KPIs improve.
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md_content)
        
    print(f"Customer retention report generated successfully at '{report_path}'.")
    return report_path

if __name__ == "__main__":
    generate_report()
