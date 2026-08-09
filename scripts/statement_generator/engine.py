"""Transaction synthesis.

Produces bank and credit card transaction series for a persona over a date
range. Two invariants that the parser will later be tested against:

  1. Running balance is exact:  opening + credits - debits == closing
  2. The emitted JSON is the ground truth for the PDF rendered from it

Every amount is an integer in paise. No floats anywhere in this module.
"""

import random
from calendar import monthrange
from datetime import date, timedelta

SEED_BASE = 20260809


def _clamp_day(y, m, d):
    return min(d, monthrange(y, m)[1])


def _months(start: date, end: date):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


# ---------------------------------------------------------------------------
# Narration formatting — mimics real HDFC statement descriptors
# ---------------------------------------------------------------------------

def _ref(rng, width=16):
    return "".join(str(rng.randint(0, 9)) for _ in range(width))


def narrate(rng, kind, party, extra=""):
    """Return (narration, chq_ref) mimicking HDFC descriptor conventions."""
    if kind == "salary":
        r = _ref(rng, 15)
        return f"NEFT CR-HDFC0000060-{party}-SALARY{extra}-N{r}", f"N{r}"
    if kind == "invoice":
        r = _ref(rng, 15)
        return f"NEFT CR-ICIC0000004-{party}-INVOICE{extra}-N{r}", f"N{r}"
    if kind == "upi":
        vpa = party.lower().replace(" ", "") + "@ybl"
        r = _ref(rng, 12)
        return f"UPI-{party}-{vpa}-YESB0YBLUPI-{r}-PAYMENT", f"0000{r}"
    if kind == "pos":
        card = f"4160{_ref(rng, 2)}XXXXXX{_ref(rng, 4)}"
        return f"POS {card} {party} POS DEBIT", f"0000N{_ref(rng, 11)}"
    if kind == "atm":
        return f"ATW-{_ref(rng, 10)}-{party}-{extra}", f"0000{_ref(rng, 12)}"
    if kind == "neft":
        r = _ref(rng, 15)
        return f"NEFT DR-HDFC0000512-{party}-NETBANK-N{r}-PERSONAL", f"N{r}"
    if kind == "imps":
        r = _ref(rng, 12)
        return f"IMPS-{r}-{party}-HDFC", f"0000{r}"
    if kind == "ach":
        return f"ACH D- {party}-{_ref(rng, 9)}", f"00000{_ref(rng, 11)}"
    if kind == "emi":
        a, b = _ref(rng, 7), _ref(rng, 10)
        return f"EMI {a} CHQ S{b}{extra}", "000000000000000"
    if kind == "billpay":
        return f"IB BILLPAY DR-{party}-{_ref(rng, 6)}XXXXXX{_ref(rng, 4)}", \
               f"IB{_ref(rng, 14)}"
    if kind == "si":
        return f"SI-TAD-{party}-{_ref(rng, 10)}", f"0000{_ref(rng, 12)}"
    if kind == "cardpay":
        return f"IB BILLPAY DR-{party}-{_ref(rng, 6)}XXXXXX{_ref(rng, 4)}", \
               f"IB{_ref(rng, 14)}"
    if kind == "interest":
        return "CREDIT INTEREST CAPITALISED", "000000000000000"
    if kind == "cashdep":
        return f"CASH DEP {party} -", f"00000000000{_ref(rng, 4)}"
    raise ValueError(kind)


# ---------------------------------------------------------------------------
# Bank statement generation
# ---------------------------------------------------------------------------

def generate_bank(persona, start: date, end: date, card_payments=None):
    """Return (transactions, opening, closing).

    card_payments: optional dict {date: paise} of credit card bill payments
    computed by the card generator, so the two documents agree with each other.
    """
    rng = random.Random(SEED_BASE + hash(persona.key) % 100000)
    card_payments = card_payments or {}
    events = []

    for y, m in _months(start, end):
        mlabel = date(y, m, 1).strftime("%b%y").upper()

        # Income
        for day, amount, employer, variance in persona.income:
            if variance:
                # Irregular: sometimes the invoice doesn't land at all
                if rng.random() < 0.28:
                    continue
                factor = 1 + rng.uniform(-variance, variance) / 100.0
                amt = int(amount * factor / 100) * 100
                d = date(y, m, _clamp_day(y, m, day + rng.randint(-4, 6)))
                kind, extra = "invoice", f" {mlabel}"
            else:
                amt = amount
                d = date(y, m, _clamp_day(y, m, day))
                kind, extra = "salary", f" {mlabel}"
            if start <= d <= end:
                narration, ref = narrate(rng, kind, employer, extra)
                events.append(dict(date=d, narration=narration, ref=ref,
                                   deposit=amt, withdrawal=0,
                                   category="income", merchant=employer))

        # Recurring debits
        for rd in persona.recurring:
            if rd.amount == 0:
                continue  # card payments injected separately
            d = date(y, m, _clamp_day(y, m, rd.day))
            if not (start <= d <= end):
                continue
            extra = f" {_ref(rng, 10)}" if rd.kind == "emi" else ""
            narration, ref = narrate(rng, rd.kind, rd.counterparty, extra)
            events.append(dict(date=d, narration=narration, ref=ref,
                               deposit=0, withdrawal=rd.amount,
                               category=rd.label, merchant=rd.counterparty))

        # Discretionary
        for sp in persona.spends:
            if sp.channel == "card":
                continue  # lands on the card statement, not the bank account
            n = int(sp.per_month) + (1 if rng.random() < (sp.per_month % 1) else 0)
            for _ in range(n):
                d = date(y, m, _clamp_day(y, m, rng.randint(1, 28)))
                if not (start <= d <= end):
                    continue
                amt = rng.randint(sp.lo // 100, sp.hi // 100) * 100
                merchant = rng.choice(sp.merchants)
                kind = {"upi": "upi", "pos": "pos", "atm": "atm"}[sp.channel]
                extra = "PUNE MH" if kind == "atm" else ""
                narration, ref = narrate(rng, kind, merchant, extra)
                events.append(dict(date=d, narration=narration, ref=ref,
                                   deposit=0, withdrawal=amt,
                                   category=sp.category, merchant=merchant))

        # Quarterly savings interest
        if m in (3, 6, 9, 12):
            d = date(y, m, _clamp_day(y, m, 30))
            if start <= d <= end:
                narration, ref = narrate(rng, "interest", "")
                events.append(dict(date=d, narration=narration, ref=ref,
                                   deposit=rng.randint(90, 480) * 100,
                                   withdrawal=0, category="interest_income",
                                   merchant="HDFC BANK"))

    # Credit card bill payments, sourced from the card generator
    for d, amt in card_payments.items():
        if start <= d <= end and amt > 0:
            issuer = persona.card.issuer.split()[0] + " CARDS"
            narration, ref = narrate(rng, "cardpay", issuer)
            events.append(dict(date=d, narration=narration, ref=ref,
                               deposit=0, withdrawal=amt,
                               category="card_payment", merchant=issuer))

    events.sort(key=lambda e: (e["date"], e["withdrawal"] == 0))

    # Running balance, with an overdraft guard: if the account would go
    # negative, inject a realistic top-up rather than emit an invalid statement.
    balance = persona.opening_balance
    out = []
    for e in events:
        delta = e["deposit"] - e["withdrawal"]
        if balance + delta < 0:
            topup = ((abs(balance + delta) // 500000) + 1) * 500000
            # Funding the shortfall from savings elsewhere. Worth surfacing:
            # a persona repeatedly topping up from investments is a signal.
            src = rng.choice(["MF REDEMPTION-MIRAE LARGE CAP",
                              "MF REDEMPTION-PARAG PARIKH FLEXI",
                              "SELF-SAVINGS TRANSFER"])
            narration, ref = narrate(rng, "imps", src)
            balance += topup
            out.append(dict(date=e["date"], narration=narration, ref=ref,
                            deposit=topup, withdrawal=0, balance=balance,
                            category="transfer_in", merchant=src))
        balance += delta
        e["balance"] = balance
        out.append(e)

    return out, persona.opening_balance, balance


# ---------------------------------------------------------------------------
# Credit card statement generation
# ---------------------------------------------------------------------------

MIN_DUE_PCT = 5          # percent of closing balance
MIN_DUE_FLOOR = 20000    # paise (Rs 200)
MONTHLY_RATE = 355       # 3.55% per month, ~42.6% APR — typical Indian card
LATE_FEE = 130000        # paise (Rs 1,300)
GST_PCT = 18


def generate_card(persona, start: date, end: date):
    """Return (cycles, payments_by_date).

    A cycle is one monthly statement: opening, purchases, payments, finance
    charges, closing, minimum due, and its transaction list.
    """
    card = persona.card
    rng = random.Random(SEED_BASE + 7717 + hash(persona.key) % 100000)
    cycles = []
    payments = {}
    opening = 0

    for y, m in _months(start, end):
        stmt_day = _clamp_day(y, m, card.statement_day)
        stmt_date = date(y, m, stmt_day)
        if stmt_date > end:
            break

        cycle_start = stmt_date - timedelta(days=30)
        txns = []

        # Purchases during the cycle
        for sp in card.spends:
            n = int(sp.per_month) + (1 if rng.random() < (sp.per_month % 1) else 0)
            for _ in range(n):
                d = cycle_start + timedelta(days=rng.randint(1, 29))
                if d > stmt_date:
                    continue
                amt = rng.randint(sp.lo // 100, sp.hi // 100) * 100
                txns.append(dict(date=d, description=rng.choice(sp.merchants),
                                 amount=amt, type="debit",
                                 category=sp.category))

        # Payment made against the PREVIOUS cycle, lands in this one
        payment = 0
        if opening > 0:
            if card.payment_style == "full":
                payment = opening
            elif card.payment_style == "minimum":
                payment = max(opening * MIN_DUE_PCT // 100, MIN_DUE_FLOOR)
            else:  # partial
                payment = int(opening * rng.uniform(0.30, 0.65) / 100) * 100
            payment = min(payment, opening)
            pay_date = cycle_start + timedelta(days=rng.randint(2, 12))
            txns.append(dict(date=pay_date,
                             description="PAYMENT RECEIVED - THANK YOU",
                             amount=payment, type="credit", category="payment"))
            payments[pay_date] = payments.get(pay_date, 0) + payment

        # Finance charges apply when a balance was carried
        finance_charge = 0
        gst = 0
        if opening > 0 and payment < opening:
            carried = opening - payment
            finance_charge = carried * MONTHLY_RATE // 10000
            # Cash advances attract interest from day one
            cash = sum(t["amount"] for t in txns
                       if t["category"] == "cash_advance")
            if cash:
                finance_charge += cash * MONTHLY_RATE // 10000
            gst = finance_charge * GST_PCT // 100
            txns.append(dict(date=stmt_date, description="FINANCE CHARGES",
                             amount=finance_charge, type="debit",
                             category="finance_charge"))
            txns.append(dict(date=stmt_date, description="GST ON FINANCE CHARGES",
                             amount=gst, type="debit", category="tax"))

        txns.sort(key=lambda t: t["date"])

        purchases = sum(t["amount"] for t in txns
                        if t["type"] == "debit"
                        and t["category"] not in ("finance_charge", "tax"))
        closing = opening - payment + purchases + finance_charge + gst
        min_due = max(closing * MIN_DUE_PCT // 100, MIN_DUE_FLOOR) if closing > 0 else 0
        min_due = min(min_due, closing)

        due = stmt_date + timedelta(days=20)
        cycles.append(dict(
            statement_date=stmt_date,
            cycle_start=cycle_start,
            due_date=due,
            opening=opening,
            payments=payment,
            purchases=purchases,
            finance_charge=finance_charge,
            gst=gst,
            closing=closing,
            minimum_due=min_due,
            credit_limit=card.limit,
            available=max(card.limit - closing, 0),
            transactions=txns,
        ))
        opening = closing

    return cycles, payments
