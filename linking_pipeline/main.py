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
                 input_path_timba: str,
                 input_path_CGE: str,
                 input_world: str,
                 link_typ: str,
                 linked_CGE: str,
                 project: str,
                 aggregation_switch: bool,
                 disaggregation_switch: bool,
                 calibration_switch: bool):
        self.current_scenario = current_scenario
        self.current_dt = dt.datetime.now().strftime("%Y%m%d")
        self.input_path_timba = input_path_timba
        self.input_path_CGE = input_path_CGE
        self.input_world = input_world
        self.link_typ = link_typ
        self.linked_CGE = linked_CGE
        self.project = project
        self.aggregation_switch = aggregation_switch
        self.disaggregation_switch = disaggregation_switch
        self.calibration_switch = calibration_switch


if __name__ == '__main__':
    pipeline = main_linking_pipeline(current_scenario='2025_CarbonLeak_REF_sc_SSP2_30periods',
                                     input_path_timba='2025_CarbonLeak_REF_sc_SSP2_30periods',  # For result aggregation
                                     input_path_CGE='dartbio_data_gdpA_i3',   # For result disaggregation
                                     input_world='20240409_BioSDG_World_2011_SSP2_FRA',  # For result disaggregation
                                     # Note: Update current_scenario if input_path_timba is changed
                                     link_typ='continous',  # Alternatives: 'continous', 'end_point'
                                     # Note:
                                     # If 'continous' TiMBA results all intermediate periods are processed
                                     # If 'end_point' TiMBA results for first and final periods are processed
                                     linked_CGE='MAGNET',  # Alternatives: 'DART-BIO', 'MAGNET'
                                     project='CarbonLeak',    # Alternatives: 'BioSDG', 'BioSDG_cp', 'CarbonLeak', 'BEPASO'
                                     # Note: linked_CGE and project must be harmonized (e.g., DART-BIO + BioSDG)
                                     aggregation_switch=True,  # Note: activates aggregation if True
                                     disaggregation_switch=False,  # Note: activates disaggregation if True
                                     calibration_switch=False)

    if pipeline.aggregation_switch:
        AggregateTiMBAResults.main_aggregation_pipeline(self=pipeline,
                                                         domains_to_aggregate=['production', 'forest', 'carbon', 'io']
                                                         # Alternatives: 'production', 'forest', 'carbon', 'io'
                                                         )

    if pipeline.disaggregation_switch:
        DisaggregateCGEResults.main_disaggregation_pipeline(self=pipeline,
                                                            updated_file="pkl"  # "xlsx"
                                                            )
    if pipeline.calibration_switch:
        CalibrateTiMBA.main_calibration_pipeline(
            self=pipeline
        )




