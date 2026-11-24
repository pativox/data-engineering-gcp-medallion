from pathlib import Path
from datetime import datetime
from collections import defaultdict
import csv, json

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data/raw", ROOT / "data/processed"

def read_csv(name):
    with (RAW / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))

def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def run():
    customers = {r["customer_id"]: r for r in read_csv("customers.csv")}
    products = {r["product_id"]: r for r in read_csv("products.csv")}
    orders, seen, accepted, rejected = read_csv("orders.csv"), set(), [], []
    for row in orders:
        reason = None
        if row["order_id"] in seen:
            reason = "duplicate_order_id"
        seen.add(row["order_id"])
        if not reason and row["customer_id"] not in customers: reason = "unknown_customer"
        if not reason and row["product_id"] not in products: reason = "unknown_product"
        try:
            qty, price, total = int(row["quantity"]), float(row["unit_price"]), float(row["total_amount"])
            datetime.strptime(row["order_date"], "%Y-%m-%d")
            if qty <= 0 or price <= 0: reason = reason or "non_positive_quantity_or_price"
            if round(qty * price, 2) != round(total, 2): reason = reason or "amount_mismatch"
        except (ValueError, TypeError):
            reason = reason or "invalid_numeric_or_date"
        if reason:
            rejected.append({"order_id": row["order_id"], "reason": reason})
            continue
        enriched = dict(row, customer_city=customers[row["customer_id"]]["city"],
                        product_name=products[row["product_id"]]["product_name"],
                        category=products[row["product_id"]]["category"],
                        order_year_month=row["order_date"][:7])
        accepted.append(enriched)
    write_csv(OUT / "silver_orders.csv", accepted, list(accepted[0]))
    fact_fields = ["order_id","customer_id","product_id","order_date","quantity","unit_price","total_amount","channel"]
    fact = [{k: r[k] for k in fact_fields} for r in accepted]
    write_csv(OUT / "gold_fact_sales.csv", fact, fact_fields)
    monthly = defaultdict(lambda: {"orders": 0, "revenue": 0.0, "units": 0})
    for row in accepted:
        item = monthly[row["order_year_month"]]
        item["orders"] += 1; item["revenue"] += float(row["total_amount"]); item["units"] += int(row["quantity"])
    aggregates = [{"year_month": k, **v, "revenue": round(v["revenue"], 2)} for k, v in sorted(monthly.items())]
    write_csv(OUT / "gold_monthly_sales.csv", aggregates, ["year_month","orders","revenue","units"])
    write_csv(OUT / "rejected_orders.csv", rejected, ["order_id","reason"])
    report = {"source_rows": len(orders), "accepted_rows": len(accepted), "rejected_rows": len(rejected),
              "status": "PASS" if not rejected else "PASS_WITH_REJECTS"}
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports/quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    run()
