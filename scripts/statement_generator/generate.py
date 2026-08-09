"""Generate synthetic bank and credit card statements for all personas.

Usage:
    python -m statement_generator.generate --out ../fixtures

For every persona this writes four files:

    <key>_bank_FY2025-26.pdf        the bank statement
    <key>_bank_FY2025-26.json       expected parser output (ground truth)
    <key>_card_FY2025-26.pdf        12 monthly credit card statements
    <key>_card_FY2025-26.json       expected parser output (ground truth)

The PDF and the JSON are rendered from the same in-memory objects, so the JSON
is exact ground truth by construction. That is the whole point: parser tests
compare against it, and any mismatch is a real parser bug.
"""

import argparse
import json
import os
from datetime import date

from . import render_bank, render_card
from .engine import generate_bank, generate_card
from .personas import ALL_PERSONAS

START = date(2025, 4, 1)
END = date(2026, 3, 31)
LABEL = "FY2025-26"


def bank_fixture(persona, txns, opening, closing):
    credits = sum(t["deposit"] for t in txns)
    debits = sum(t["withdrawal"] for t in txns)
    assert opening + credits - debits == closing, "reconciliation failed"
    return {
        "source": "synthetic",
        "document_type": "bank_statement",
        "bank": "HDFC BANK",
        "persona": persona.key,
        "account_number_masked": "XXXXXXXXXX" + persona.account_no[-4:],
        "ifsc": persona.ifsc,
        "period": {"from": START.isoformat(), "to": END.isoformat()},
        "opening_balance_paise": opening,
        "closing_balance_paise": closing,
        "total_credits_paise": credits,
        "total_debits_paise": debits,
        "transaction_count": len(txns),
        "transactions": [
            {
                "date": t["date"].isoformat(),
                "narration": t["narration"],
                "reference": t["ref"],
                "withdrawal_paise": t["withdrawal"],
                "deposit_paise": t["deposit"],
                "balance_paise": t["balance"],
                "expected_category": t["category"],
                "expected_merchant": t["merchant"],
            }
            for t in txns
        ],
    }


def card_fixture(persona, cycles):
    for cyc in cycles:
        expected = (cyc["opening"] - cyc["payments"] + cyc["purchases"]
                    + cyc["finance_charge"] + cyc["gst"])
        assert expected == cyc["closing"], "card cycle reconciliation failed"
    return {
        "source": "synthetic",
        "document_type": "credit_card_statement",
        "issuer": persona.card.issuer,
        "product": persona.card.product,
        "persona": persona.key,
        "card_number_masked": "XXXXXXXXXXXX" + persona.card.last4,
        "credit_limit_paise": persona.card.limit,
        "payment_style": persona.card.payment_style,
        "cycle_count": len(cycles),
        "total_finance_charges_paise": sum(c["finance_charge"] for c in cycles),
        "total_gst_paise": sum(c["gst"] for c in cycles),
        "closing_balance_paise": cycles[-1]["closing"] if cycles else 0,
        "cycles": [
            {
                "statement_date": c["statement_date"].isoformat(),
                "due_date": c["due_date"].isoformat(),
                "opening_paise": c["opening"],
                "payments_paise": c["payments"],
                "purchases_paise": c["purchases"],
                "finance_charge_paise": c["finance_charge"],
                "gst_paise": c["gst"],
                "closing_paise": c["closing"],
                "minimum_due_paise": c["minimum_due"],
                "transactions": [
                    {
                        "date": t["date"].isoformat(),
                        "description": t["description"],
                        "amount_paise": t["amount"],
                        "type": t["type"],
                        "expected_category": t["category"],
                    }
                    for t in c["transactions"]
                ],
            }
            for c in cycles
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="fixtures")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    summary = []
    for p in ALL_PERSONAS:
        cycles, payments = generate_card(p, START, END)
        txns, opening, closing = generate_bank(p, START, END, payments)

        base = os.path.join(args.out, f"{p.key}_{LABEL}")

        render_bank.render(f"{base}_bank.pdf", p, txns,
                           START.strftime("%d/%m/%Y"), END.strftime("%d/%m/%Y"))
        with open(f"{base}_bank.json", "w") as f:
            json.dump(bank_fixture(p, txns, opening, closing), f, indent=2)

        render_card.render(f"{base}_card.pdf", p, cycles)
        with open(f"{base}_card.json", "w") as f:
            json.dump(card_fixture(p, cycles), f, indent=2)

        income = sum(t["deposit"] for t in txns if t["category"] == "income")
        spend = sum(t["withdrawal"] for t in txns)
        summary.append({
            "persona": p.key,
            "name": p.name,
            "narrative": p.narrative,
            "bank_transactions": len(txns),
            "card_cycles": len(cycles),
            "annual_income_rs": income // 100,
            "annual_outflow_rs": spend // 100,
            "closing_balance_rs": closing // 100,
            "card_closing_rs": (cycles[-1]["closing"] if cycles else 0) // 100,
            "card_finance_charges_rs": sum(c["finance_charge"] for c in cycles) // 100,
        })
        print(f"{p.key:20s} bank={len(txns):4d} txns  "
              f"cycles={len(cycles):2d}  "
              f"card_interest=Rs {sum(c['finance_charge'] for c in cycles)//100:,}")

    with open(os.path.join(args.out, "personas_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
