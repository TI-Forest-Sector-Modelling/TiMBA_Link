import os

# Folders
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_PATH = os.path.join(BASE_DIR, "data", "input")
OUTPUT_PATH = os.path.join(BASE_DIR, "data", "output")

SUPPORTIVE_INPUT_PATH = os.path.join(INPUT_PATH, "supportive_data")
CGE_INPUT_PATH = os.path.join(INPUT_PATH, "cge_data")
TIMBA_INPUT_PATH = os.path.join(INPUT_PATH, "timba_data")

# Input data
INPUT_POP_DART_BIO = os.path.join(SUPPORTIVE_INPUT_PATH, "POP_DART-BIO_data.csv")
INPUT_POP_MAGNET = os.path.join(SUPPORTIVE_INPUT_PATH, "POP_MAGNET_data.csv")
INPUT_GDP_WORLD_BANK = os.path.join(SUPPORTIVE_INPUT_PATH, "worldbank_data_2025.xlsx")
INPUT_GDP_OECD = os.path.join(SUPPORTIVE_INPUT_PATH, "oecd_data.xlsx")
INPUT_FRA = os.path.join(SUPPORTIVE_INPUT_PATH, "fra_data.csv")

COUNTRY_CONCORDANCE_TIMBA = os.path.join(SUPPORTIVE_INPUT_PATH, "country_concordance.xlsx")
COUNTRY_CONCORDANCE_WB_OECD = os.path.join(SUPPORTIVE_INPUT_PATH, "worldbank_oecd_countries.xlsx")

# Output data
AGGREGATION_OUTPUT_PATH = os.path.join(OUTPUT_PATH, "aggregation")
DISAGGREGATION_OUTPUT_PATH = os.path.join(OUTPUT_PATH, "disaggregation")
