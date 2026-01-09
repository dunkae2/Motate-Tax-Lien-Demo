# Motate-Tax-Lien-Demo (DC)

This demo scrapes the District of Columbia tax lien sale list PDF from the DC OTR website, parses lien rows, and loads them into a Postgres database (via Docker). It is rerunnable.

## Tech Stack
- Python 3
- Docker + Postgres 16
- requests, beautifulsoup4
- pdfplumber
- psycopg

## Setup

### 1) Create virtual env + install deps
```bash
pip install -r requirements.txt
```

### 2) Start Postgres (Docker)
```bash
docker compuse up -d
```

### 3) Initialize DB schema
```bash
python -c "from Motate_demo.db import init_db; init_db(); print('tables created')"
```

## Run the pipeline

### 4) Download latest DC PDF
```bash
python -c "from Motate_demo.scrape_dc import find_latest_listing_page_url, resolve_pdf_url, download_pdf; from pathlib import Path; listing=find_latest_listing_page_url(); pdf=resolve_pdf_url(listing); path,sha=download_pdf(pdf, Path('data/raw')); print('saved:', path, 'sha:', sha)"
```

### 5) Load into Postgres
```bash
python -c "from Motate_demo.load import ingest_dc; ingest_dc(tax_year=2025)"
```

## Verification Queries

### 1) Liens by quadrant
### NE 589, NW 562, SE 488, SW 28, NULL 9
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); import psycopg; conn=psycopg.connect(os.getenv('DATABASE_URL')); cur=conn.cursor(); cur.execute('SELECT quadrant, COUNT(*) FROM tax_lien GROUP BY quadrant ORDER BY COUNT(*) DESC'); print(cur.fetchall()); conn.close()"
```

### 2) Total taxes owned
### $4113721.37
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); import psycopg; conn=psycopg.connect(os.getenv('DATABASE_URL')); cur=conn.cursor(); cur.execute('SELECT SUM(taxes_owed) FROM tax_lien'); print(cur.fetchone()[0]); conn.close()"
```
