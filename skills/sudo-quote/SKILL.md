---
name: sudo-quote
description: Use when generating a quotation (or quote PDF) from Sudo Tech Consulting (Pty) Ltd — the SA-registered entity (also referred to as "Sudo Labs"). Produces a one-page branded PDF with the company + FNB banking details baked in. Triggers on "draft a quote", "quote for <client>", "quotation PDF", "send <client> a quote". Not for invoices/payment reconciliation — for those, use a SARS-ready tool like PopPay.
---

# Sudo Quote

Generates a one-page quotation PDF for **Sudo Tech Consulting (Pty) Ltd** (reg 2019/621707/07; trades as "Sudo Labs"). Company address, contact, FNB banking details and the not-VAT-registered note are constants baked into the generator — never re-ask the user for them.

## How to use

1. Write a per-quote JSON (see `examples/icon-reservations.json` for the shape). Fields:
   - `quote_no` — `QYYYY-NN`, running number per year (e.g. `Q2026-002`).
   - `date`, `valid_until` — human dates ("15 June 2026"). Validity is 30 days.
   - `bill_to` — `{name, org?, email?}`.
   - `project` — one line.
   - `items` — list of `{title, desc, amount, unit}`. `unit` is `"once-off"` or `"per month"`; the generator groups once-off into a one-off total and lists each monthly item as recurring.
   - `scope` (optional) — list of HTML-paragraph strings (what's in/out).
   - `payment` — one HTML string (terms).
   - Use HTML entities in text fields: `&mdash;`, `&ndash;`, `&nbsp;`, and `<b>...</b>` for emphasis.
2. Run: `python3 generate_quote.py <quote.json> <output.pdf>`
3. Read the output PDF back to confirm it's **one page**. If a long quote spills, trim `desc`/`scope` wording — the layout is tuned for one page.
4. Send the PDF to the user. Log the quote number so the next one increments.

## Repeatable process (when to graduate off this skill)

This skill is the lazy path for occasional quotes. Once quoting/invoicing becomes regular — or you need to invoice and reconcile payments against a SA bank account — move to a SARS-ready tool (**PopPay**, free, EFT + proof-of-payment matching). This skill stays useful for one-off branded quotes.

## Editing company / banking details

Change `COMPANY`, `BANK`, or `VAT_NOTE` constants at the top of `generate_quote.py` only when the registration, address, contact email, or bank account actually changes.
