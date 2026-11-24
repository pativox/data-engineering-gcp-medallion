"""Local Medallion batch pipeline. Raw CSV files are the Bronze source of truth."""
from pathlib import Path
import csv
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

ORDER_COLUMNS = {"order_id", "customer_id", "product_id", "order_date", "quantity", "unit_price", "total_amount", "channel"}
CUSTOMER_COLUMNS = {"customer_id", "customer_name", "city", "created_at"}
PRODUCT_COLUMNS = {"product_id", "product_name", "category", "unit_price"}


def read_csv(name, required_columns):
    path = RAW / name
    if not path.is_file():
        raise FileNotFoundError(f"Required source file not found: {path}")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or [])
        missing = required_columns - headers
        if missing:
            raise ValueError(f"{name}: missing columns: {', '.join(sorted(missing))}")
        return list(reader)


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _decimal(value):
    result = Decimal(str(value).strip())
    if not result.is_finite():
        raise InvalidOperation("non-finite numeric value")
    return result


def transform_orders(source_orders, customers, products):
    seen, accepted, rejected = set(), [], []
    for row_number, row in enumerate(source_orders, start=2):
        order_id = (row.get("order_id") or "").strip()
        customer_id = (row.get("customer_id") or "").strip()
        product_id = (row.get("product_id") or "").strip()
        reason = None

        if not order_id or not customer_id or not product_id:
            reason = "missing_required_key"
        elif order_id in seen:
            reason = "duplicate_order_id"
        else:
            seen.add(order_id)

        try:
            quantity = int((row.get("quantity") or "").strip())
            unit_price = _decimal(row.get("unit_price", ""))
            total_amount = _decimal(row.get("total_amount", ""))
            order_date = datetime.strptime((row.get("order_date") or "").strip(), "%Y-%m-%d").date()
            if quantity <= 0 or unit_price <= 0:
                reason = reason or "non_positive_quantity_or_price"
            if (unit_price * quantity).quantize(Decimal("0.01")) != total_amount.quantize(Decimal("0.01")):
                reason = reason or "amount_mismatch"
        except (ValueError, TypeError, InvalidOperation):
            reason = reason or "invalid_numeric_or_date"

        if not reason and customer_id not in customers:
            reason = "unknown_customer"
        if not reason and product_id not in products:
            reason = "unknown_product"
        if not reason and not (row.get("channel") or "").strip():
            reason = "empty_channel"

        if reason:
            rejected.append({"row_number": row_number, "order_id": order_id, "reason": reason})
            continue

        enriched = dict(row)
        enriched.update({
            "order_id": order_id,
            "customer_id": customer_id,
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": str(unit_price.quantize(Decimal("0.01"))),
            "total_amount": str(total_amount.quantize(Decimal("0.01"))),
            "order_date": order_date.isoformat(),
            "customer_name": customers[customer_id]["customer_name"],
            "customer_city": customers[customer_id]["city"],
            "product_name": products[product_id]["product_name"],
            "category": products[product_id]["category"],
            "order_year_month": order_date.strftime("%Y-%m"),
        })
        accepted.append(enriched)
    return accepted, rejected


def run():
    customer_rows = read_csv("customers.csv", CUSTOMER_COLUMNS)
    product_rows = read_csv("products.csv", PRODUCT_COLUMNS)
    source_orders = read_csv("orders.csv", ORDER_COLUMNS)

    customers = {}
    for row in customer_rows:
        key = (row.get("customer_id") or "").strip()
        if not key or key in customers:
            raise ValueError("customers.csv contains an empty or duplicate customer_id")
        customers[key] = row

    products = {}
    for row in product_rows:
        key = (row.get("product_id") or "").strip()
        if not key or key in products:
            raise ValueError("products.csv contains an empty or duplicate product_id")
        products[key] = row

    accepted, rejected = transform_orders(source_orders, customers, products)
    silver_fields = ["order_id", "customer_id", "product_id", "order_date", "quantity", "unit_price",
                     "total_amount", "channel", "customer_name", "customer_city", "product_name",
                     "category", "order_year_month"]
    write_csv(OUT / "silver_orders.csv", accepted, silver_fields)

    fact_fields = ["order_id", "customer_id", "product_id", "order_date", "quantity",
                   "unit_price", "total_amount", "channel"]
    fact = [{key: row[key] for key in fact_fields} for row in accepted]
    write_csv(OUT / "gold_fact_sales.csv", fact, fact_fields)

    dim_customers = [{"customer_id": key, "customer_name": row["customer_name"],
                      "city": row["city"], "created_at": row["created_at"]}
                     for key, row in sorted(customers.items())]
    dim_products = [{"product_id": key, "product_name": row["product_name"],
                     "category": row["category"], "unit_price": row["unit_price"]}
                    for key, row in sorted(products.items())]
    write_csv(OUT / "gold_dim_customer.csv", dim_customers,
              ["customer_id", "customer_name", "city", "created_at"])
    write_csv(OUT / "gold_dim_product.csv", dim_products,
              ["product_id", "product_name", "category", "unit_price"])

    monthly = defaultdict(lambda: {"orders": 0, "revenue": Decimal("0.00"), "units": 0})
    for row in accepted:
        bucket = monthly[row["order_year_month"]]
        bucket["orders"] += 1
        bucket["revenue"] += Decimal(row["total_amount"])
        bucket["units"] += int(row["quantity"])
    monthly_rows = [{"year_month": key, "orders": value["orders"],
                     "revenue": str(value["revenue"].quantize(Decimal("0.01"))),
                     "units": value["units"]} for key, value in sorted(monthly.items())]
    write_csv(OUT / "gold_monthly_sales.csv", monthly_rows,
              ["year_month", "orders", "revenue", "units"])

    reasons = {}
    for row in rejected:
        reasons[row["reason"]] = reasons.get(row["reason"], 0) + 1
    report = {
        "source_rows": len(source_orders),
        "accepted_rows": len(accepted),
        "rejected_rows": len(rejected),
        "rejection_reasons": reasons,
        "status": "PASS" if not rejected else "PASS_WITH_REJECTS",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_csv(OUT / "rejected_orders.csv", rejected, ["row_number", "order_id", "reason"])
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    run()
