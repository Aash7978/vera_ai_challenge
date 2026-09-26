import json
from pathlib import Path


class DataLoader:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)

    def load_json(self, path: Path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_categories(self):
        categories = {}

        directory = self.data_dir / "categories"

        for file in directory.glob("*.json"):
            data = self.load_json(file)
            categories[data["slug"]] = data

        return categories

    def load_merchants(self):
        merchants = {}

        directory = self.data_dir / "merchants"

        for file in directory.glob("*.json"):
            data = self.load_json(file)
            merchants[data["merchant_id"]] = data

        return merchants

    def load_customers(self):
        customers = {}

        directory = self.data_dir / "customers"

        for file in directory.glob("*.json"):
            data = self.load_json(file)
            customers[data["customer_id"]] = data

        return customers

    def load_triggers(self):
        triggers = {}

        directory = self.data_dir / "triggers"

        for file in directory.glob("*.json"):
            data = self.load_json(file)
            triggers[data["id"]] = data

        return triggers

    def load_all(self):
        return {
            "categories": self.load_categories(),
            "merchants": self.load_merchants(),
            "customers": self.load_customers(),
            "triggers": self.load_triggers(),
        }