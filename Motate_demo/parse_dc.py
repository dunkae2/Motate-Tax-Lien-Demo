import re
from decimal import Decimal
import pdfplumber

SSL_RE = re.compile(r"^(?P<square>\d{4})-(?P<suffix>[A-Z])?-(?P<lot>\d{4})$")


def parse_pdf(pdf_path):
    rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                if line.lower().startswith("square-suffix-lot"):
                    continue

                parts = line.split()
                if len(parts) < 5:
                    continue

                ssl_raw = (parts[0] + parts[1]).replace(" ", "")
                m = SSL_RE.match(ssl_raw)
                if not m:
                    continue

                square = m.group("square")
                suffix = m.group("suffix") or ""
                lot = m.group("lot")

                idx = 2
                improved = False
                if idx < len(parts) and parts[idx] == "&IMP":
                    improved = True
                    idx += 1

                amt = parts[-1].replace("$", "").replace(",", "")
                try:
                    taxes_owed = Decimal(amt)
                except Exception:
                    continue

                body = parts[idx:-1]

                premise_i = None
                for i, tok in enumerate(body):
                    if tok.isdigit():
                        premise_i = i
                        break

                owner = " ".join(body[:premise_i]).strip() if premise_i is not None else " ".join(body).strip()
                premise_number = body[premise_i] if premise_i is not None else None

                quadrant = None
                street_name = None
                if premise_i is not None:
                    after = body[premise_i + 1 :]
                    for q in ["NW", "NE", "SW", "SE"]:
                        if q in after:
                            qi = after.index(q)
                            street_name = " ".join(after[:qi]).strip() or None
                            quadrant = q
                            break

                rows.append(
                    {
                        "ssl": ssl_raw,
                        "square": square,
                        "suffix": suffix,
                        "lot": lot,
                        "improved": improved,
                        "owner": owner or None,
                        "premise_number": premise_number,
                        "street_name": street_name,
                        "quadrant": quadrant,
                        "taxes_owed": taxes_owed,
                    }
                )

    return rows
