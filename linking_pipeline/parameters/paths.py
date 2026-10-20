from pathlib import Path
from linking_pipeline.parameters.default_parameters import project_parameters
from linking_pipeline.parameters.defines import VarNames

PACKAGE_DIR = Path(__file__).parent.parent.absolute()
# Folders
DATA_FOLDER = PACKAGE_DIR / "data"
INPUT_FOLDER = DATA_FOLDER / "input"
OUTPUT_FOLDER = DATA_FOLDER / "output"

# Input data
SUPPORTIVE_INPUT_PATH = INPUT_FOLDER / "supportive_data"
CGE_INPUT_PATH = INPUT_FOLDER / "cge_data"

TIMBA_INPUT_BLANK_PATH = INPUT_FOLDER / "timba_data"

if project_parameters[VarNames.RUN_TIMBA_SWITCH.value]:
    TIMBA_INPUT_PATH = DATA_FOLDER / "TiMBA" / "data" / "output" / "data"  # Based on TiMBA package default folder structure
else:
    TIMBA_INPUT_PATH = TIMBA_INPUT_BLANK_PATH

INPUT_POP_DART_BIO = SUPPORTIVE_INPUT_PATH / "POP_DART-BIO_data.csv"
INPUT_POP_MAGNET = SUPPORTIVE_INPUT_PATH / "POP_MAGNET_data.csv"
INPUT_GDP_WORLD_BANK = SUPPORTIVE_INPUT_PATH / "worldbank_data_2025.xlsx"
INPUT_GDP_OECD = SUPPORTIVE_INPUT_PATH / "oecd_data.xlsx"
INPUT_FRA = SUPPORTIVE_INPUT_PATH / "fra_data.csv"

# Supporting data
COUNTRY_CONCORDANCE_TIMBA = SUPPORTIVE_INPUT_PATH / "country_concordance.xlsx"
COUNTRY_CONCORDANCE_WB_OECD = SUPPORTIVE_INPUT_PATH / "worldbank_oecd_countries.xlsx"

# Output data
AGGREGATION_OUTPUT_PATH = OUTPUT_FOLDER / "aggregation"
if project_parameters[VarNames.RUN_TIMBA_SWITCH.value]:
    DISAGGREGATION_OUTPUT_PATH = DATA_FOLDER / "TiMBA" / "data" / "input" / "01_Input_Files" # Based on TiMBA package default folder structure
    TIMBA_INPUT_FILES = DISAGGREGATION_OUTPUT_PATH
else:
    DISAGGREGATION_OUTPUT_PATH = OUTPUT_FOLDER / "disaggregation"

# TiMBA data (additional paths)
GIT_USER = "TI-Forest-Sector-Modelling"
GIT_REPO = "TiMBA_Additional_Information"
GIT_BRANCH = "main"
GIT_FOLDER = r"Input_Data/default_scenario/02_Additional_Information"
TIMBA_ADD_INFO = DATA_FOLDER / "TiMBA" / "data" / "input" / "02_Additional_Information"
TIMBA_SERIALIZATION = DATA_FOLDER / "TiMBA" / "data" / "input" / "03_Serialization"

