import hashlib
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from Motate_demo.db import get_conn
from Motate_demo.parse_dc import parse_pdf
from Motate_demo.scrape_dc import find_latest_listing_page_url, resolve_pdf_url


def ingest_dc(tax_year, pdf_path: str = "data/raw/dc_tax_sale_2025_07_15.pdf"):
    load_dotenv()

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path.resolve()}")

    listing_url = find_latest_listing_page_url()
    pdf_url = resolve_pdf_url(listing_url)

    content = pdf_path.read_bytes()
    sha256 = hashlib.sha256(content).hexdigest()
    fetched_at = datetime.now(timezone.utc)

    rows = parse_pdf(str(pdf_path))
    print(f"Parsed {len(rows)} rows from {pdf_path.name}")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM jurisdiction WHERE code = %s", ("DC",))
            rec = cur.fetchone()
            if not rec:
                raise RuntimeError("Jurisdiction 'DC' not found. Did you run init_db()?")
            jurisdiction_id = rec[0]

            cur.execute(
                """
                INSERT INTO source_document (jurisdiction_id, source_url, fetched_at, sha256, file_path)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (jurisdiction_id, sha256)
                DO UPDATE SET
                    source_url = EXCLUDED.source_url,
                    fetched_at  = EXCLUDED.fetched_at,
                    file_path   = EXCLUDED.file_path
                RETURNING id
                """,
                (jurisdiction_id, pdf_url, fetched_at, sha256, str(pdf_path)),
            )
            source_document_id = cur.fetchone()[0]

            prop_id_cache: dict[str, int] = {}

            for r in rows:
                ssl = r["ssl"]

                prop_id = prop_id_cache.get(ssl)
                if prop_id is None:
                    cur.execute(
                        """
                        INSERT INTO property (jurisdiction_id, ssl, square, suffix, lot)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (jurisdiction_id, ssl)
                        DO UPDATE SET
                            square = EXCLUDED.square,
                            suffix = EXCLUDED.suffix,
                            lot    = EXCLUDED.lot
                        RETURNING id
                        """,
                        (jurisdiction_id, ssl, r.get("square"), r.get("suffix") or None, r.get("lot")),
                    )
                    prop_id = cur.fetchone()[0]
                    prop_id_cache[ssl] = prop_id

                cur.execute(
                    """
                    INSERT INTO tax_lien (
                        jurisdiction_id, property_id, tax_year, improved, owner,
                        premise_number, street_name, quadrant, taxes_owed, source_document_id
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (jurisdiction_id, property_id, tax_year)
                    DO UPDATE SET
                        improved = EXCLUDED.improved,
                        owner = EXCLUDED.owner,
                        premise_number = EXCLUDED.premise_number,
                        street_name = EXCLUDED.street_name,
                        quadrant = EXCLUDED.quadrant,
                        taxes_owed = EXCLUDED.taxes_owed,
                        source_document_id = EXCLUDED.source_document_id
                    """,
                    (
                        jurisdiction_id,
                        prop_id,
                        tax_year,
                        r.get("improved"),
                        r.get("owner"),
                        r.get("premise_number"),
                        r.get("street_name"),
                        r.get("quadrant"),
                        r.get("taxes_owed"),
                        source_document_id,
                    ),
                )

        conn.commit()

    print(f"Loaded liens={len(rows)} properties={len(prop_id_cache)} source_document_id={source_document_id}")
