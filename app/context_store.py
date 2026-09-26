class ContextStore:

    def __init__(self, data):
        self.categories = data["categories"]
        self.merchants = data["merchants"]
        self.customers = data["customers"]
        self.triggers = data["triggers"]

    def get_trigger(self, trigger_id):
        return self.triggers.get(trigger_id)

    def get_merchant(self, merchant_id):
        return self.merchants.get(merchant_id)

    def get_customer(self, customer_id):
        if customer_id is None:
            return None

        return self.customers.get(customer_id)

    def get_category(self, category_slug):
        return self.categories.get(category_slug)

    def build_context(self, trigger_id):

        # 1. Find trigger
        trigger = self.get_trigger(trigger_id)

        if trigger is None:
            raise ValueError(
                f"Trigger not found: {trigger_id}"
            )

        # 2. Find merchant
        merchant_id = trigger["merchant_id"]

        merchant = self.get_merchant(merchant_id)

        if merchant is None:
            raise ValueError(
                f"Merchant not found: {merchant_id}"
            )

        # 3. Find category
        category_slug = merchant["category_slug"]

        category = self.get_category(category_slug)

        if category is None:
            raise ValueError(
                f"Category not found: {category_slug}"
            )

        # 4. Find customer, if present
        customer_id = trigger.get("customer_id")

        customer = self.get_customer(customer_id)

        # 5. Return unified context
        return {
            "trigger": trigger,
            "merchant": merchant,
            "customer": customer,
            "category": category,
        }
    