# -----------------------------------------------------
# GFPMpt_linking_pipeline - disaggregation_pipeline (Tomke Honkomp (TH) - Thuenen-Institut)
# GCE-output disaggregation to GFPMpt (spatial and sectoral disaggregation)
# Status: 03.2024
# Last update: 03.2024
# -----------------------------------------------------

# imports
import pandas as pd
import numpy as np
import os
from pathlib import Path
import datetime as dt
from linking_pipeline.helper_functions.base_logger import get_logger


class DisaggregateCGEResults(object):
    def __init__(self,
                 current_scenario: str,
                 input_path_gfpmpt: str,
                 link_typ: str,
                 linked_CGE: str,
                 project: str
                 ):
        self.sfile = os.path.dirname(Path(__file__).resolve().parents[0])
        self.Logger = get_logger(user_path=None, aggregation_flag=True)
        self.current_scenario = current_scenario
        self.current_dt = dt.datetime.now().strftime("%Y%m%d")
        self.input_path_gfpmpt = input_path_gfpmpt
        self.link_typ = link_typ
        self.linked_CGE = linked_CGE
        self.project = project
        """self.gfpmpt_data = DisaggregateCGEResults.readin_model_data(self)
        (self.region_key, self.commodity_key, self.exogenous_change_structure, self.start_year, self.end_year
         ) = DisaggregateCGEResults.readin_help_data(self)"""

    def readin_model_data(self):
        pass

    def readin_help_data(self):
        pass

    def main_disaggregation_pipeline(self):
        Pipeline_Disagg = DisaggregateCGEResults(
            current_scenario=self.current_scenario,
            input_path_gfpmpt=self.input_path_gfpmpt,
            link_typ=self.link_typ,
            linked_CGE=self.linked_CGE,
            project=self.project
        )
