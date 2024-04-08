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
    com_info_14 = {"GFPMpt_Comcode": [80, 81, 82, 83, 84, 85, 86, 87, 88, 90, 91, 92, 93],
                   "GFPMpt_Comgroup": ["F", "TR", "TR", "S", "WBP", "WBP", "WBP", "MP", "CP", "TPP",
                                       "TPP", "TPP", "TPP"],
                   "GTAP-Sector": ["FRS", "FRS", "FRS", "LUM", "LUM", "LUM", "LUM", "PPP", "PPP",
                                   "PPP", "PPP", "PPP", "PPP"]}

    # for GFPMpt CNC version (16 products)
    com_info_16 = {"GFPMpt_Comcode": [78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 90, 91, 92, 93],
                   "GFPMpt_Comgroup": ["TR", "S", "F", "TR", "TR", "S", "WBP", "WBP", "WBP", "MP", "CP", "TPP",
                                       "TPP", "TPP", "TPP"],
                   "GTAP-Sector": ["FRS", "LUM", "FRS", "FRS", "FRS", "LUM", "LUM", "LUM", "LUM", "PPP", "PPP",
                                   "PPP", "PPP", "PPP", "PPP"]}

    com_info_16_biosdg = {"GFPMpt_Comcode": [78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 90, 91, 92, 93],
                          "GFPMpt_Comgroup": ["TR", "S", "F", "TR", "TR", "S", "WBP", "WBP", "WBP", "MP", "CP", "TPP",
                                              "TPP", "TPP", "TPP"],
                          "GTAP-Sector": ["FRS", "LUM", "BIOE", "FRS", "FRS", "LUM", "LUM", "LUM", "LUM", "PPP", "PPP",
                                          "PPP", "PPP", "PPP", "PPP"]}
