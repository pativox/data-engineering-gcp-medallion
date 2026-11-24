from pathlib import Path
import csv, json
from datetime import datetime
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

def read_csv(name):
    with (RAW / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def run():
    customers = {r["customer_id"]: r for r in read_csv("customers.csv")}
    products = {r["product_id"]: r for r in read_csv("products.csv")}
    source_orders = read_csv("orders.csv")
    seen, accepted, rejected = set(), [], []
    for row in source_orders:
        reason = None
        oid = row["order_id"]
        if oid in seen:
            reason = "duplicate_order_id"
        else:
            seen.add(oid)
        if not reason and row["customer_id"] not in customers:
            reason = "unknown_customer"
        if not reason and row["product_id"] not in products:
            reason = "unknown_product"
        try:
            qty, price = int(row["quantity"]), float(row["unit_price"])
            total = float(row["total_amount"])
            datetime.strptime(row["order_date"], "%Y-%m-%d")
            if qty <= 0 or price <= 0:
                reason = reason or "non_positive_quantity_or_price"
            if round(qty * price, 2) != round(total, 2):
                reason = reason or "amount_mismatch"
        except (ValueError, TypeError):
            reason = reason or "invalid_numeric_or_date"
        if reason:
            rejected.append({"order_id": oid, "reason": reason})
            continue
        enriched = dict(row)
        enriched["customer_city"] = customers[row["customer_id"]]["city"]
        enriched["product_name"] = products[row["product_id"]]["product_name"]
        enriched["category"] = products[row["product_id"]]["category"]
        enriched["order_year_month"] = row["order_date"][:7]
        accepted.append(enriched)

    OUT.mkdir(parents=True, exist_ok=True)
    fields = list(accepted[0].keys()) if accepted else []
    write_csv(OUT / "silver_orders.csv", accepted, fields)

    # Gold fact table and monthly aggregate
    fact = [{k:r[k] for k in ["order_id","customer_id","product_id","order_date","quantity","unit_price","total_amount","channel"]} for r in accepted]
    write_csv(OUT / "gold_fact_sales.csv", fact, list(fact[0].keys()) if fact else [])
    agg = defaultdict(lambda: {"orders":0, "revenue":0.0, "units":0})
    for r in accepted:
        a=agg[r["order_year_month"]]
        a["orders"] += 1
        a["revenue"] += float(r["total_amount"])
        a["units"] += int(r["quantity"])
    monthly=[{"year_month":k,"orders":v["orders"],"revenue":round(v["revenue"],2),"units":v["units"]} for k,v in sorted(agg.items())]
    write_csv(OUT / "gold_monthly_sales.csv", monthly, ["year_month","orders","revenue","units"])

    report = {
        "source_rows": len(source_orders),
        "accepted_rows": len(accepted),
        "rejected_rows": len(rejected),
        "rejection_reasons": {},
        "status": "PASS" if not rejected else "PASS_WITH_REJECTS",
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds")
    }
    for r in rejected:
        report["rejection_reasons"][r["reason"]] = report["rejection_reasons"].get(r["reason"],0)+1
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS/"quality_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    write_csv(OUT/"rejected_orders.csv", rejected, ["order_id","reason"])
    print(json.dumps(report,indent=2))

if __name__ == "__main__":
    run()
