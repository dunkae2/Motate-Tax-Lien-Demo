import re
import hashlib
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

DC_RESOURCE_PAGE = "https://otr.cfo.dc.gov/page/real-property-tax-lien-sale-and-resources"
ASOF_RE = re.compile(r"as of\s+(\d{1,2})/(\d{1,2})/(\d{4})", re.IGNORECASE)


def _asof_date(text):
    m = ASOF_RE.search(text)
    if not m:
        return None
    mm, dd, yyyy = map(int, m.groups())
    return datetime(yyyy, mm, dd)


def find_latest_listing_page_url():
    html = requests.get(DC_RESOURCE_PAGE, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")

    candidates = []
    for a in soup.select("a[href]"):
        text = a.get_text(" ", strip=True)
        href = a["href"]

        if "Tax Lien Sale List as of" in text and "Discount" not in text:
            dt = _asof_date(text)
            if dt:
                candidates.append((dt, urljoin(DC_RESOURCE_PAGE, href)))

    if not candidates:
        raise RuntimeError("No matching DC tax lien list links found.")

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def resolve_pdf_url(page_url):
    if page_url.lower().endswith(".pdf"):
        return page_url

    html = requests.get(page_url, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")

    for a in soup.select("a[href]"):
        href = a["href"]
        if href.lower().endswith(".pdf"):
            return urljoin(page_url, href)

    raise RuntimeError("Could not find a PDF file on the listing page.")


def download_pdf(pdf_url, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = pdf_url.split("/")[-1].split("?")[0]
    path = out_dir / filename

    r = requests.get(pdf_url, timeout=60)
    r.raise_for_status()
    content = r.content

    path.write_bytes(content)
    sha = hashlib.sha256(content).hexdigest()
    return path, sha
