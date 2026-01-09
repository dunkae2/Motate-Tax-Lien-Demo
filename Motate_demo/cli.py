import typer
from dotenv import load_dotenv

from Motate_demo.db import init_db
from Motate_demo.load import ingest_dc

app = typer.Typer()


@app.command()
def initdb():
    load_dotenv()
    init_db()
    print("DB initialized")


@app.command()
def ingest(tax_year: int = 2025):
    load_dotenv()
    parsed, loaded = ingest_dc(tax_year=tax_year)
    print(f"Parsed rows: {parsed}")
    print(f"Loaded rows: {loaded}")


if __name__ == "__main__":
    app()
