from backend.processors.core.table_engine import TableConfig

# Configuration for Synevo
SYNEVO_CONFIG = TableConfig(
    headers={
        "name": ["Denumire", "Analiza", "Test"],
        "result": ["Rezultat", "Valoare"],
        "unit": ["UM", "U.M.", "Unit"],
        "reference": ["Interval", "Referinta", "Biologic"]
    },
    row_tolerance=10,
    footer_keywords=["Medic", "Rezultat eliberat", "Pagina", "Synevo", "Laborator"]
)

# Configuration for Regina Maria
REGINA_CONFIG = TableConfig(
    headers={
        "name": ["Analiza", "Denumire", "Test"],
        "result": ["Rezultate", "Rezultat"],
        "unit": ["UM", "U.M.", "Unit"],
        "reference": ["Interval", "Valori", "Biologic", "Referinta"]
    },
    row_tolerance=10,
    footer_keywords=["Medic", "Data", "Pagina"] # Regina often puts "Data..." in footer
)

PROVIDERS = {
    "synevo": SYNEVO_CONFIG,
    "regina_maria": REGINA_CONFIG
}

def get_parser_config(provider_name: str) -> TableConfig:
    return PROVIDERS.get(provider_name.lower())
