import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "pipeline.py"
spec = importlib.util.spec_from_file_location("medallion_pipeline", MODULE_PATH)
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


class TransformOrdersTests(unittest.TestCase):
    def setUp(self):
        self.customers = {"C1": {"customer_id": "C1", "customer_name": "Customer 1", "city": "Buin"}}
        self.products = {"P1": {"product_id": "P1", "product_name": "Product 1", "category": "Test"}}
        self.valid = {"order_id": "O1", "customer_id": "C1", "product_id": "P1",
                      "order_date": "2025-01-10", "quantity": "2", "unit_price": "10.00",
                      "total_amount": "20.00", "channel": "web"}

    def transform(self, row):
        return pipeline.transform_orders([row], self.customers, self.products)

    def test_accepts_valid_order(self):
        accepted, rejected = self.transform(self.valid)
        self.assertEqual(len(accepted), 1)
        self.assertEqual(rejected, [])
        self.assertEqual(accepted[0]["order_year_month"], "2025-01")

    def test_rejects_unknown_customer(self):
        row = {**self.valid, "customer_id": "MISSING"}
        _, rejected = self.transform(row)
        self.assertEqual(rejected[0]["reason"], "unknown_customer")

    def test_rejects_unknown_product(self):
        row = {**self.valid, "product_id": "MISSING"}
        _, rejected = self.transform(row)
        self.assertEqual(rejected[0]["reason"], "unknown_product")

    def test_rejects_duplicate_order_id(self):
        accepted, rejected = pipeline.transform_orders(
            [self.valid, self.valid], self.customers, self.products)
        self.assertEqual(len(accepted), 1)
        self.assertEqual(rejected[0]["reason"], "duplicate_order_id")

    def test_rejects_non_positive_quantity(self):
        _, rejected = self.transform({**self.valid, "quantity": "0", "total_amount": "0"})
        self.assertEqual(rejected[0]["reason"], "non_positive_quantity_or_price")

    def test_rejects_inconsistent_amount(self):
        _, rejected = self.transform({**self.valid, "total_amount": "19.99"})
        self.assertEqual(rejected[0]["reason"], "amount_mismatch")

    def test_rejects_invalid_date(self):
        _, rejected = self.transform({**self.valid, "order_date": "not-a-date"})
        self.assertEqual(rejected[0]["reason"], "invalid_numeric_or_date")

    def test_rejects_infinite_amount(self):
        _, rejected = self.transform({**self.valid, "total_amount": "Infinity"})
        self.assertEqual(rejected[0]["reason"], "invalid_numeric_or_date")

    def test_empty_output_still_has_headers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "empty.csv"
            pipeline.write_csv(target, [], ["order_id", "reason"])
            with target.open(encoding="utf-8", newline="") as handle:
                self.assertEqual(next(csv.reader(handle)), ["order_id", "reason"])


if __name__ == "__main__":
    unittest.main()
