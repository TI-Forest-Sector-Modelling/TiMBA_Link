from enum import Enum


class Constants(Enum):
    """
    Class for constant float and int variables
    """
    pass


class ProductStructures(Enum):
    """
    Class groups different product structures used to aggregate GFPMpt results and disaggregate linked CGE results.
    Product structures are specific to the used GFPMpt version (14, 16 or 20 products) and project needs (e.g. separate
    aggregation of fuelwood for BioSDG)
    """
    # for GFPMpt base version (14 products)
    com_info_14 = {"GFPMpt_Comcode": [80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93],
                   "GFPMpt_Comgroup": ["F", "TR", "TR", "S", "WBP", "WBP", "WBP", "MP", "CP", "TPP",
                                       "TPP", "TPP", "TPP", "TPP"],
                   "GTAP-Sector": ["FRS", "FRS", "FRS", "LUM", "LUM", "LUM", "LUM", "PPP", "PPP",
                                   "PPP", "PPP", "PPP", "PPP", "PPP"]}

    # for GFPMpt CNC version (16 products)
    com_info_16 = {"GFPMpt_Comcode": [78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93],
                   "GFPMpt_Comgroup": ["TR", "S", "F", "TR", "TR", "S", "WBP", "WBP", "WBP", "MP", "CP", "TPP",
                                       "TPP", "TPP", "TPP", "TPP"],
                   "GTAP-Sector": ["FRS", "LUM", "FRS", "FRS", "FRS", "LUM", "LUM", "LUM", "LUM", "PPP", "PPP",
                                   "PPP", "PPP", "PPP", "PPP", "PPP"]}

    com_info_16_biosdg = {"GFPMpt_Comcode": [78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93],
                          "GFPMpt_Comgroup": ["TR", "S", "F", "TR", "TR", "S", "WBP", "WBP", "WBP", "MP", "CP", "TPP",
                                              "TPP", "TPP", "TPP", "TPP"],
                          "GTAP-Sector": ["FRS", "LUM", "BIOE", "FRS", "FRS", "LUM", "LUM", "LUM", "LUM", "PPP", "PPP",
                                          "PPP", "PPP", "PPP", "PPP", "PPP"]}


class VarNames(Enum):
    # Project parameters
    CURRENT_SC = "current_scenario"
    LINK_TYPE = "link_type"
    LINKED_CGE = "linked_CGE"
    PROJECT = "project"
    ITER_NUM = "iter_num"
    AGGREGATION_SWITCH = "aggregation_switch"
    DISAGGREGATION_SWITCH = "disaggregation_switch"
    RUN_TIMBA_SWITCH = "run_timba_switch"
    CALIBRATION_SWITCH = "calibration_switch"

    # Aggregation parameters
    INPUT_TIMBA = "input_timba"
    DOMAINS_TO_AGGREGATE = "domains_to_aggregate"

    # Disaggregation parameters
    INPUT_TIMBA_TO_UPDATE = "input_timba_to_update"
    INPUT_GDP_CGE = "input_gdp_CGE"
    INPUT_FOREST_CGE = "input_forest_CGE"
    LINKED_VAR = "linked_var"
    UPDATED_FILE = "updated_file"

