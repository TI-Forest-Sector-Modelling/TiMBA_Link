# -----------------------------------------------------
# CGE_linking_pipeline (Tomke Honkomp (TH) - Thuenen-Institut)
# Soft linkage of TiMBA to selected CGE (spatial and sectoral aggregation and disaggregation)
# Projects: BioSDG, CarbonLeak
# -----------------------------------------------------
# imports
import datetime as dt
from linking_pipeline.logic.aggregation_pipeline import AggregateTiMBAResults
from linking_pipeline.logic.disaggregation_pipeline import DisaggregateCGEResults
from linking_pipeline.logic.calibration_pipeline import CalibrateTiMBA

class main_linking_pipeline(object):
    def __init__(self,
                 current_scenario: str,
                 link_typ: str,
                 linked_CGE: str,
                 project: str,
                 aggregation_switch: bool,
                 disaggregation_switch: bool,
                 calibration_switch: bool):

        self.current_scenario = current_scenario
        self.current_dt = dt.datetime.now().strftime("%Y%m%d")
        self.link_typ = link_typ
        self.linked_CGE = linked_CGE
        self.project = project
        self.aggregation_switch = aggregation_switch
        self.disaggregation_switch = disaggregation_switch
        self.calibration_switch = calibration_switch


if __name__ == '__main__':
    pipeline = main_linking_pipeline(
        current_scenario='2025_CarbonLeak_REF_sc_SSP2_v3_fin_10periods_new_forest_IR_iter0',
        link_typ='end_point',  # Alternatives: 'continous', 'end_point'
        # Note:
        # If 'continous' TiMBA results all intermediate periods are processed
        # If 'end_point' TiMBA results for first and final periods are processed
        linked_CGE='MAGNET',  # Alternatives: 'DART-BIO', 'MAGNET'
        project='CarbonLeak',  # Alternatives: 'BioSDG', 'BioSDG_cp', 'CarbonLeak', 'BEPASO'
        # Note: linked_CGE and project must be harmonized (e.g., DART-BIO + BioSDG)
        aggregation_switch=True,  # Note: activates aggregation if True
        disaggregation_switch=False,  # Note: activates disaggregation if True
        calibration_switch=False
    )

    if pipeline.aggregation_switch:
        AggregateTiMBAResults.main_aggregation_pipeline(
            self=pipeline,
            input_timba='20250719_CarbonLeak_REF_sc_SSP2_v3_fin_10periods_new_forest_IR_iter0',
            domains_to_aggregate=['production', 'forest', 'carbon', 'io']
            # Alternatives: 'production', 'forest', 'carbon', 'io'
        )

    if pipeline.disaggregation_switch:
        DisaggregateCGEResults.main_disaggregation_pipeline(
            self=pipeline,
            input_timba='20250719_CarbonLeak_REF_sc_SSP2_v3_fin_10periods_new_forest_IR_iter0',
            input_sc_file='2025_CarbonLeak_REF_sc_SSP2_v3_fin_10periods_new_forest_IR_iter0',
            input_gdp_CGE='20250719_gdp_magnet_REF_iter0_test',
            input_forest_CGE='20250719_forestland_magnet_REF_iter0',
            linked_var=['gdp', 'gdp_cap', 'forest_area'],  # Options: 'gdp', 'gdp_cap', and 'forest_area'
            updated_file="xlsx"  #Alternatives: "pkl" or "xlsx"
        )
    if pipeline.calibration_switch:
        CalibrateTiMBA.main_calibration_pipeline(
            self=pipeline
        )




