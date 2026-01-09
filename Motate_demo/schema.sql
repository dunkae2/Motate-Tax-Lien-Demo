
CREATE TABLE IF NOT EXISTS jurisdiction (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  code TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS source_document (
  id SERIAL PRIMARY KEY,
  jurisdiction_id INT NOT NULL REFERENCES jurisdiction(id),
  source_url TEXT NOT NULL,
  fetched_at TIMESTAMP NOT NULL,
  sha256 TEXT NOT NULL,
  file_path TEXT NOT NULL,
  UNIQUE (jurisdiction_id, sha256)
);

CREATE TABLE IF NOT EXISTS property (
  id SERIAL PRIMARY KEY,
  jurisdiction_id INT NOT NULL REFERENCES jurisdiction(id),
  ssl TEXT NOT NULL,
  square TEXT,
  suffix TEXT,
  lot TEXT,
  UNIQUE (jurisdiction_id, ssl)
);

CREATE TABLE IF NOT EXISTS tax_lien (
  id SERIAL PRIMARY KEY,
  jurisdiction_id INT NOT NULL REFERENCES jurisdiction(id),
  property_id INT NOT NULL REFERENCES property(id),
  tax_year INT NOT NULL,
  improved BOOLEAN,
  owner TEXT,
  premise_number TEXT,
  street_name TEXT,
  quadrant TEXT,
  taxes_owed NUMERIC(12,2),
  source_document_id INT NOT NULL REFERENCES source_document(id),
  UNIQUE (jurisdiction_id, property_id, tax_year)
);
