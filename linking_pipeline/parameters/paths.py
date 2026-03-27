import os

# Folders
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(BASE_DIR, "data", "input")
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "output")

# Input data
INPUT_POP_DART_BIO = os.path.join(INPUT_PATH, "dartbio_data_pop.xlsx")
INPUT_POP_MAGNET = os.path.join(INPUT_PATH, "magnet_data_pop.xlsx")
INPUT_GDP_WORLD_BANK = os.path.join(INPUT_PATH, "worldbank_data_2025.xlsx")
INPUT_GDP_OECD = os.path.join(INPUT_PATH, "oecd_data.xlsx")
INPUT_FRA = os.path.join(INPUT_PATH, "fra_data.csv")

COUNTRY_CONCORDANCE_TIMBA = os.path.join(INPUT_PATH, "country_concordance.xlsx")
COUNTRY_CONCORDANCE_WB_OECD = os.path.join(INPUT_PATH, "worldbank_oecd_countries.xlsx")
