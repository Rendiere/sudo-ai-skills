#!/usr/bin/env python3
"""Generate a Sudo Tech Consulting quotation PDF from a JSON spec.

Usage: python generate_quote.py <quote.json> <output.pdf>

Company + banking details are constants below (one registered entity).
Edit COMPANY / BANK here only if the registration, address or bank changes.
"""
import json
import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

# ---- Constants for the registered entity (rarely change) ----
COMPANY = {
    "name": "SUDO TECH CONSULTING (PTY) LTD",
    "reg": "2019/621707/07",
    "address": ["4 Upper Union Street, Unit 12 Palmkloof Apartments",
                "Cape Town, Western Cape, 8001"],
    "email": "ren@sudolabs.co.uk",
}
BANK = {
    "Bank": "First National Bank (FNB)",
    "Account name": "Sudo Tech Consulting (Pty) Ltd",
    "Account number": "63129905296 (Gold Business Account)",
    "Branch code": "250655 (universal)",
}
VAT_NOTE = "Sudo Tech Consulting (Pty) Ltd is not VAT-registered; no VAT applies."

INK = colors.HexColor("#1a1a1a")
ACCENT = colors.HexColor("#0b7a6b")
MUTE = colors.HexColor("#6b6b6b")
LINE = colors.HexColor("#d9d9d9")
BG = colors.HexColor("#f4f6f5")

styles = getSampleStyleSheet()


def st(name, **kw):
    return ParagraphStyle(name, parent=styles["Normal"], **kw)


def fmt(n):
    return "R {:,.2f}".format(float(n))


def build(spec, out):
    s_company = st("company", fontName="Helvetica-Bold", fontSize=15, textColor=INK, leading=18)
    s_meta = st("meta", fontName="Helvetica", fontSize=8.5, textColor=MUTE, leading=12)
    s_quoteword = st("quoteword", fontName="Helvetica-Bold", fontSize=22, textColor=ACCENT, leading=24, alignment=2)
    s_label = st("label", fontName="Helvetica-Bold", fontSize=8, textColor=MUTE, leading=12)
    s_val = st("val", fontName="Helvetica", fontSize=9.5, textColor=INK, leading=13)
    s_valr = st("valr", fontName="Helvetica", fontSize=9.5, textColor=INK, leading=13, alignment=2)
    s_h = st("h", fontName="Helvetica-Bold", fontSize=10, textColor=INK, leading=14, spaceAfter=3)
    s_body = st("body", fontName="Helvetica", fontSize=9, textColor=INK, leading=12.5)
    s_bodymute = st("bodymute", fontName="Helvetica", fontSize=8.5, textColor=MUTE, leading=12)
    s_cell = st("cell", fontName="Helvetica", fontSize=9, textColor=INK, leading=12)
    s_cellb = st("cellb", fontName="Helvetica-Bold", fontSize=9.5, textColor=INK, leading=12)
    s_cellr = st("cellr", fontName="Helvetica-Bold", fontSize=9.5, textColor=INK, leading=12, alignment=2)
    s_foot = st("foot", fontName="Helvetica", fontSize=7.5, textColor=MUTE, leading=10, alignment=1)
    s_amt = ParagraphStyle("amt", parent=s_label, alignment=2)

    doc = SimpleDocTemplate(out, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=14*mm, bottomMargin=12*mm)
    S = []

    # Header
    company_block = [Paragraph(COMPANY["name"], s_company),
                     Paragraph("Reg. " + COMPANY["reg"] + "<br/>" +
                               "<br/>".join(COMPANY["address"]) + "<br/>" +
                               COMPANY["email"], s_meta)]
    header = Table([[company_block, [Paragraph("QUOTATION", s_quoteword)]]],
                   colWidths=[105*mm, 65*mm])
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    S += [header, Spacer(1, 5), HRFlowable(width="100%", thickness=1, color=ACCENT), Spacer(1, 8)]

    # Bill-to + meta
    bt = spec["bill_to"]
    billto = [Paragraph("BILL TO", s_label), Paragraph(bt["name"], s_val)]
    if bt.get("org"):
        billto.append(Paragraph(bt["org"], s_val))
    if bt.get("email"):
        billto.append(Paragraph(bt["email"], s_val))
    meta = [[Paragraph("Quote No.", s_label), Paragraph(spec["quote_no"], s_valr)],
            [Paragraph("Date", s_label), Paragraph(spec["date"], s_valr)],
            [Paragraph("Valid until", s_label), Paragraph(spec["valid_until"], s_valr)]]
    meta_tbl = Table(meta, colWidths=[30*mm, 35*mm])
    meta_tbl.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                                  ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                  ("TOPPADDING", (0, 0), (-1, -1), 1),
                                  ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    top = Table([[billto, meta_tbl]], colWidths=[105*mm, 65*mm])
    top.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                             ("LEFTPADDING", (0, 0), (-1, -1), 0),
                             ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    S += [top, Spacer(1, 10), Paragraph("Project: " + spec["project"], s_h), Spacer(1, 5)]

    # Line items
    rows = [[Paragraph("DESCRIPTION", s_label), Paragraph("AMOUNT (ZAR)", s_amt)]]
    once_total = 0.0
    monthly = []
    for it in spec["items"]:
        unit = it.get("unit", "once-off")
        cell = [Paragraph(it["title"], s_cellb), Spacer(1, 2), Paragraph(it["desc"], s_cell)]
        amt = Paragraph(fmt(it["amount"]) +
                        "<br/><font size=7 color='#6b6b6b'>" + unit + "</font>", s_cellr)
        rows.append([cell, amt])
        if "month" in unit:
            monthly.append(it["amount"])
        else:
            once_total += float(it["amount"])
    items = Table(rows, colWidths=[130*mm, 40*mm])
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("BACKGROUND", (0, 0), (-1, 0), BG),
             ("LINEBELOW", (0, 0), (-1, 0), 0.6, LINE),
             ("TOPPADDING", (0, 0), (-1, -1), 6),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
             ("LEFTPADDING", (0, 0), (-1, -1), 8),
             ("RIGHTPADDING", (0, 0), (-1, -1), 8)]
    for i in range(1, len(rows)):
        style.append(("LINEBELOW", (0, i), (-1, i), 0.4, LINE))
    items.setStyle(TableStyle(style))
    S += [items, Spacer(1, 8)]

    # Totals
    tot_rows = []
    if once_total:
        tot_rows.append([Paragraph("One-off total", s_cell), Paragraph(fmt(once_total), s_cellr)])
    for m in monthly:
        tot_rows.append([Paragraph("Recurring", s_cell), Paragraph(fmt(m) + " / month", s_cellr)])
    totals = Table(tot_rows, colWidths=[55*mm, 40*mm])
    totals.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, len(tot_rows)-2), 0.4, LINE),
                                ("TOPPADDING", (0, 0), (-1, -1), 5),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                                ("BACKGROUND", (0, 0), (-1, -1), BG)]))
    wrap = Table([["", totals]], colWidths=[75*mm, 95*mm])
    wrap.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    S += [wrap, Spacer(1, 3), Paragraph(VAT_NOTE, s_bodymute), Spacer(1, 11)]

    # Scope (optional)
    if spec.get("scope"):
        S.append(Paragraph("Scope", s_h))
        for line in spec["scope"]:
            S.append(Paragraph(line, s_body))
            S.append(Spacer(1, 2))
        S.append(Spacer(1, 9))

    # Payment + banking
    S += [Paragraph("Payment", s_h), Paragraph(spec["payment"], s_body), Spacer(1, 7)]
    bank_rows = [[Paragraph(k, s_label), Paragraph(v, s_val)] for k, v in BANK.items()]
    bank_rows.append([Paragraph("Reference", s_label), Paragraph(spec["quote_no"], s_val)])
    bank = Table(bank_rows, colWidths=[30*mm, 90*mm])
    bank.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                              ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                              ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    S += [bank, Spacer(1, 16),
          HRFlowable(width="100%", thickness=0.4, color=LINE), Spacer(1, 12)]

    # Acceptance
    accepted_label = "Accepted by (" + (bt.get("org") or bt["name"]) + ")"
    acc = Table([[Paragraph(accepted_label + "<br/><br/>__________________________", s_bodymute),
                  Paragraph("Date<br/><br/>__________________________", s_bodymute)]],
                colWidths=[90*mm, 80*mm])
    acc.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0),
                             ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    S += [acc, Spacer(1, 12),
          Paragraph(COMPANY["name"].title() + " &middot; Reg. " + COMPANY["reg"] +
                    " &middot; Quote valid 30 days from date of issue.", s_foot)]

    doc.build(S)


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    build(spec, out)
    print("WROTE", out)
