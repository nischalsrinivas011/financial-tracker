"""Render a bank statement PDF in HDFC's layout.

Layout mirrors a real HDFC 'Statement of account' so the parser is exercised
against realistic column positions, wrapped narrations and descriptor formats.
Landscape A4.
"""

from reportlab.lib.colors import Color, black, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

W, H = landscape(A4)          # 842 x 595
CYAN = Color(0.875, 0.960, 0.960)
RED = Color(0.80, 0.09, 0.13)
BLUE = Color(0.10, 0.15, 0.55)

# column x positions and widths
COLS = [
    ("Date", 30, 58, "left"),
    ("Narration", 88, 292, "left"),
    ("Chq./Ref.No.", 380, 112, "center"),
    ("Value Dt", 492, 52, "center"),
    ("Withdrawal Amt.", 544, 92, "right"),
    ("Deposit Amt.", 636, 92, "right"),
    ("Closing Balance", 728, 84, "right"),
]
TABLE_L, TABLE_R = 30, 812
ROW_H = 11.5
HDR_H = 16


def money(paise):
    if paise == 0:
        return ""
    return f"{paise / 100:,.2f}"


def wrap(text, width_pts, font="Helvetica", size=6.5):
    """Greedy wrap on character budget, splitting long tokens like real
    statements do (they break mid-token at the column edge)."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    out, line = [], ""
    for ch in text:
        if stringWidth(line + ch, font, size) > width_pts - 4:
            out.append(line)
            line = ch
        else:
            line += ch
    if line:
        out.append(line)
    return out or [""]


def _label_value(c, x, y, label, value, lw=88):
    c.setFont("Helvetica", 7)
    c.setFillColor(black)
    c.drawString(x, y, label)
    c.drawString(x + lw, y, ":")
    c.drawString(x + lw + 7, y, str(value))


def draw_header(c, p, page_no, frm, to):
    c.setFont("Helvetica", 7.5)
    c.setFillColor(black)
    c.drawCentredString(W / 2, H - 28, f"Page No.: {page_no}")

    # Logo
    c.setFillColor(RED)
    c.rect(34, H - 66, 16, 16, fill=1, stroke=0)
    c.setFillColor(white)
    c.rect(38, H - 62, 8, 8, fill=1, stroke=0)
    c.setFillColor(RED)
    c.rect(40, H - 60, 4, 4, fill=1, stroke=0)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(56, H - 62, "HDFC BANK")
    c.setFont("Helvetica-Oblique", 7.5)
    c.setFillColor(Color(0.35, 0.35, 0.35))
    c.drawString(34, H - 78, "We understand your world")

    # Customer box
    bx, by, bw, bh = 34, H - 202, 380, 108
    c.setStrokeColor(black)
    c.setLineWidth(1.2)
    c.rect(bx, by, bw, bh, fill=0, stroke=1)
    c.setFillColor(black)
    c.setFont("Helvetica", 7.5)
    ty = by + bh - 14
    c.drawString(bx + 10, ty, p.name)
    for line in p.address:
        ty -= 11
        c.drawString(bx + 10, ty, line)
    c.drawString(bx + 10, by + 12, "JOINT HOLDERS :")
    c.setFont("Helvetica", 7)
    c.drawString(bx, by - 12, "Nomination : Registered")

    # Right detail block
    rx, ry = 448, H - 96
    SP = 9.4
    _label_value(c, rx, ry, "Account Branch", p.branch)
    ry -= SP
    _label_value(c, rx, ry, "Address", p.branch_address[0])
    for extra in p.branch_address[1:]:
        ry -= SP
        c.setFont("Helvetica", 7)
        c.drawString(rx + 95, ry, extra)
    for label, value in [
        ("City", p.city), ("State", p.state), ("Phone no.", p.phone),
        ("OD Limit", "0.00"), ("Currency", "INR"), ("Email", p.email),
        ("Cust ID", p.cust_id), ("Account No", f"{p.account_no}    OTHER"),
        ("A/C Open Date", p.ac_open_date), ("Account Status", "Regular"),
    ]:
        ry -= SP
        _label_value(c, rx, ry, label, value)
    ry -= SP
    c.setFont("Helvetica", 7)
    c.drawString(rx, ry, "RTGS/NEFT IFSC")
    c.drawString(rx + 88, ry, ":")
    c.drawString(rx + 95, ry, p.ifsc)
    c.drawString(rx + 190, ry, f"MICR : {p.micr}")
    ry -= SP
    c.drawString(rx, ry, "Branch Code")
    c.drawString(rx + 88, ry, ":")
    c.drawString(rx + 95, ry, p.branch_code)
    c.drawString(rx + 170, ry, "Product Code : 114")

    # Statement period
    c.setFont("Helvetica", 8)
    c.setFillColor(black)
    c.drawString(38, H - 246, f"From :  {frm}")
    c.drawString(160, H - 246, f"To :  {to}")
    c.setFont("Helvetica", 11)
    c.setFillColor(BLUE)
    c.drawString(430, H - 248, "Statement of account")
    c.setFillColor(black)


def draw_table_header(c, y):
    c.setFillColor(CYAN)
    c.rect(TABLE_L, y - HDR_H, TABLE_R - TABLE_L, HDR_H, fill=1, stroke=0)
    c.setStrokeColor(black)
    c.setLineWidth(0.7)
    c.rect(TABLE_L, y - HDR_H, TABLE_R - TABLE_L, HDR_H, fill=0, stroke=1)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 7)
    for name, x, w, _ in COLS:
        c.drawCentredString(x + w / 2, y - 11, name)
        if x > TABLE_L:
            c.line(x, y - HDR_H, x, y)
    return y - HDR_H


def draw_row(c, y, cells, nlines):
    h = ROW_H * nlines
    c.setFillColor(CYAN)
    c.rect(TABLE_L, y - h, TABLE_R - TABLE_L, h, fill=1, stroke=0)
    c.setStrokeColor(black)
    c.setLineWidth(0.5)
    c.rect(TABLE_L, y - h, TABLE_R - TABLE_L, h, fill=0, stroke=1)
    for _, x, _, _ in COLS[1:]:
        c.line(x, y - h, x, y)
    c.setFillColor(black)
    c.setFont("Helvetica", 6.5)
    for (name, x, w, align), value in zip(COLS, cells):
        lines = value if isinstance(value, list) else [value]
        for i, line in enumerate(lines):
            ty = y - 8 - i * ROW_H
            if align == "left":
                c.drawString(x + 4, ty, line)
            elif align == "center":
                c.drawCentredString(x + w / 2, ty, line)
            else:
                c.drawRightString(x + w - 5, ty, line)
    return y - h


def render(path, persona, txns, frm, to):
    c = canvas.Canvas(path, pagesize=(W, H))
    page = 1
    draw_header(c, persona, page, frm, to)
    y = draw_table_header(c, H - 258)
    bottom = 40

    for t in txns:
        narration_lines = wrap(t["narration"], COLS[1][2])
        n = len(narration_lines)
        if y - ROW_H * n < bottom:
            c.showPage()
            page += 1
            draw_header(c, persona, page, frm, to)
            y = draw_table_header(c, H - 258)
        cells = [
            t["date"].strftime("%d/%m/%y"),
            narration_lines,
            t["ref"],
            t["date"].strftime("%d/%m/%y"),
            money(t["withdrawal"]),
            money(t["deposit"]),
            f"{t['balance'] / 100:,.2f}",
        ]
        y = draw_row(c, y, cells, n)

    c.setFont("Helvetica-Oblique", 6.5)
    c.setFillColor(Color(0.4, 0.4, 0.4))
    c.drawString(TABLE_L, 26,
                 "SYNTHETIC TEST DATA - fictional persona, not a real account. "
                 "Generated for parser and evaluation fixtures.")
    c.save()
