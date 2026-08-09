"""Render a credit card statement PDF. One monthly cycle per page.

Deliberately a different shape from the bank statement: a summary block plus a
transaction ledger, rather than a running-balance table. The parser has to
handle both.
"""

from reportlab.lib.colors import Color, black, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

W, H = A4                       # 595 x 842
GREY = Color(0.94, 0.94, 0.94)
DARK = Color(0.13, 0.16, 0.22)
ACCENT = Color(0.65, 0.11, 0.16)
WARN = Color(0.72, 0.15, 0.10)

L, Rt = 40, 555


def money(paise, blank_zero=False):
    if paise == 0 and blank_zero:
        return ""
    return f"{paise / 100:,.2f}"


def render(path, persona, cycles):
    card = persona.card
    c = canvas.Canvas(path, pagesize=(W, H))

    for cyc in cycles:
        # ---- header
        c.setFillColor(DARK)
        c.rect(0, H - 74, W, 74, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(L, H - 38, card.issuer)
        c.setFont("Helvetica", 9)
        c.drawString(L, H - 54, card.product)
        c.setFont("Helvetica", 8)
        c.drawRightString(Rt, H - 38, "STATEMENT OF ACCOUNT")
        c.drawRightString(Rt, H - 54, f"Card No: XXXX XXXX XXXX {card.last4}")

        # ---- cardholder
        y = H - 96
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(L, y, persona.name)
        c.setFont("Helvetica", 7.5)
        for line in persona.address:
            y -= 10
            c.drawString(L, y, line)

        # ---- key figures panel
        py = H - 100
        c.setFillColor(GREY)
        c.rect(320, py - 76, Rt - 320, 76, fill=1, stroke=0)
        c.setStrokeColor(Color(0.75, 0.75, 0.75))
        c.setLineWidth(0.6)
        c.rect(320, py - 76, Rt - 320, 76, fill=0, stroke=1)
        rows = [
            ("Statement Date", cyc["statement_date"].strftime("%d %b %Y")),
            ("Payment Due Date", cyc["due_date"].strftime("%d %b %Y")),
            ("Total Amount Due", "Rs. " + money(cyc["closing"])),
            ("Minimum Amount Due", "Rs. " + money(cyc["minimum_due"])),
        ]
        ry = py - 15
        for i, (k, v) in enumerate(rows):
            c.setFont("Helvetica", 7.5)
            c.setFillColor(black)
            c.drawString(330, ry, k)
            c.setFont("Helvetica-Bold", 8 if i < 2 else 9)
            c.setFillColor(ACCENT if i == 2 else black)
            c.drawRightString(Rt - 10, ry, v)
            ry -= 18

        # ---- account summary
        y = min(y, py - 76) - 26
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(L, y, "ACCOUNT SUMMARY")
        y -= 6
        c.setStrokeColor(DARK)
        c.setLineWidth(0.8)
        c.line(L, y, Rt, y)
        y -= 14

        summary = [
            ("Previous Balance", cyc["opening"]),
            ("Payments / Credits", -cyc["payments"]),
            ("Purchases & Other Debits", cyc["purchases"]),
            ("Finance Charges", cyc["finance_charge"]),
            ("GST", cyc["gst"]),
            ("Total Amount Due", cyc["closing"]),
        ]
        c.setFont("Helvetica", 8)
        for label, amt in summary:
            bold = label == "Total Amount Due"
            c.setFont("Helvetica-Bold" if bold else "Helvetica", 8)
            c.setFillColor(black)
            c.drawString(L + 6, y, label)
            txt = ("-" if amt < 0 else "") + money(abs(amt))
            c.drawRightString(300, y, txt)
            y -= 12
        y -= 4
        c.setFont("Helvetica", 7.5)
        c.setFillColor(Color(0.3, 0.3, 0.3))
        c.drawString(L + 6, y, f"Credit Limit: Rs. {money(cyc['credit_limit'])}")
        c.drawString(220, y, f"Available Credit: Rs. {money(cyc['available'])}")
        util = cyc["closing"] * 100 // cyc["credit_limit"] if cyc["credit_limit"] else 0
        c.drawString(400, y, f"Utilisation: {util}%")

        # ---- minimum-due warning (regulatory-style, and it matters here)
        y -= 22
        if cyc["closing"] > 0:
            c.setFillColor(Color(1, 0.96, 0.93))
            c.rect(L, y - 26, Rt - L, 30, fill=1, stroke=0)
            c.setStrokeColor(WARN)
            c.setLineWidth(0.6)
            c.rect(L, y - 26, Rt - L, 30, fill=0, stroke=1)
            c.setFillColor(WARN)
            c.setFont("Helvetica-Bold", 7.5)
            c.drawString(L + 8, y - 6,
                         "Paying only the Minimum Amount Due will extend "
                         "repayment and increase interest payable.")
            c.setFont("Helvetica", 7)
            c.setFillColor(black)
            c.drawString(L + 8, y - 18,
                         "Interest is charged at 3.55% per month (42.60% per "
                         "annum) on the unpaid balance and on cash advances "
                         "from the date of transaction.")
            y -= 40

        # ---- transactions
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(L, y, "TRANSACTION DETAILS")
        y -= 6
        c.setStrokeColor(DARK)
        c.line(L, y, Rt, y)
        y -= 15

        c.setFillColor(GREY)
        c.rect(L, y - 4, Rt - L, 15, fill=1, stroke=0)
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(L + 6, y, "Date")
        c.drawString(L + 70, y, "Transaction Description")
        c.drawRightString(Rt - 60, y, "Amount (Rs.)")
        c.drawRightString(Rt - 8, y, "Type")
        y -= 16

        c.setFont("Helvetica", 7.5)
        for t in cyc["transactions"]:
            if y < 60:
                c.showPage()
                y = H - 60
                c.setFont("Helvetica", 7.5)
            c.setFillColor(black)
            c.drawString(L + 6, y, t["date"].strftime("%d/%m/%Y"))
            c.drawString(L + 70, y, t["description"][:52])
            c.drawRightString(Rt - 60, y, money(t["amount"]))
            c.setFillColor(Color(0.05, 0.45, 0.25) if t["type"] == "credit" else black)
            c.drawRightString(Rt - 8, y, "Cr" if t["type"] == "credit" else "Dr")
            y -= 11

        c.setFont("Helvetica-Oblique", 6.5)
        c.setFillColor(Color(0.45, 0.45, 0.45))
        c.drawString(L, 30,
                     "SYNTHETIC TEST DATA - fictional persona, not a real card "
                     "account. Generated for parser and evaluation fixtures.")
        c.showPage()

    c.save()
