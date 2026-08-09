"""The closed set of categories the cascade is allowed to assign.

Used two ways: to tell the LLM stage what its valid answers are, and to
reject anything it returns outside this set rather than trust it blindly.
"""

BANK_CATEGORIES = [
    "card_payment", "cash_withdrawal", "club_membership", "dining", "entertainment",
    "family_transfer", "food_delivery", "groceries", "health", "household_staff",
    "income", "insurance_health", "insurance_term", "interest_income", "investment_ppf",
    "investment_sip", "loan_emi", "rent", "subscription", "tax_advance", "transfer_in",
    "transport", "utilities",
]

CARD_CATEGORIES = [
    "business", "cash_advance", "dining", "entertainment", "finance_charge",
    "food_delivery", "fuel", "payment", "shopping", "tax", "travel",
]
