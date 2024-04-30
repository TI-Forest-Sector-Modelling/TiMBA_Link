# -----------------------------------------------------
# GFPMpt_linking_pipeline - main_linking_pipeline (Tomke Honkomp (TH) - Thuenen-Institut)
# Soft linkage of GFPMpt to selected CGE (spatial and sectoral aggregation and disaggregation)
# Projects: BioSDG, CarbonLeak
# Status: 04.2024
# Last update: 04.2024
# -----------------------------------------------------
# imports
import datetime as dt
from linking_pipeline.logic.aggregation_pipeline import AggregateGFPMptResults
from linking_pipeline.logic.disaggregation_pipeline import DisaggregateCGEResults

class main_linking_pipeline(object):
    def __init__(self,
                 current_scenario: str,
                 input_path_gfpmpt: str,
                 input_path_CGE: str,
                 input_world: str,
                 link_typ: str,
                 linked_CGE: str,
                 project: str,
                 aggregation_switch: bool,
                 disaggregation_switch: bool):
        self.current_scenario = current_scenario
        self.current_dt = dt.datetime.now().strftime("%Y%m%d")
        self.input_path_gfpmpt = input_path_gfpmpt
        self.input_path_CGE = input_path_CGE
        self.input_world = input_world
        self.link_typ = link_typ
        self.linked_CGE = linked_CGE
        self.project = project
        self.aggregation_switch = aggregation_switch
        self.disaggregation_switch = disaggregation_switch


if __name__ == '__main__':
    pipeline = main_linking_pipeline(current_scenario='reference_scenario_BioSDG_SSP2_2011_FRA',
                                     input_path_gfpmpt='DataContainer_Sc_20240409_BioSDG_World_2011_SSP2_FRA',
                                     input_path_CGE='dartbio_data_gdpA_i3',
                                     input_world='20240409_BioSDG_World_2011_SSP2_FRA',
                                     # Note: Update current_scenario if input_path_gfpmpt is changed
                                     link_typ='end_point',  # Alternatives: 'continous', 'end_point'
                                     # Note:
                                     # If 'continous' GFPMpt results all intermediate periods are processed
                                     # If 'end_point' GFPMpt results for first and final periods are processed
                                     linked_CGE='DART-BIO',  # Alternatives: 'DART-BIO', 'MAGNET'
                                     project='BioSDG_cp',    # Alternatives: 'BioSDG', 'BioSDG_cp', 'CarbonLeak', 'BEPASO'
                                     # Note: linked_CGE and project must be harmonized (e.g., DART-BIO + BioSDG)
                                     aggregation_switch=False,  # Note: activates aggregation if True
                                     disaggregation_switch=True  # Note: activates disaggregation if True
                                     )

    if pipeline.aggregation_switch:
        AggregateGFPMptResults.main_aggregation_pipeline(self=pipeline,
                                                         domains_to_aggregate=['production', 'forest', 'carbon', 'io']
                                                         # Alternatives: 'production', 'forest', 'carbon', 'io'
                                                         )

    if pipeline.disaggregation_switch:
        DisaggregateCGEResults.main_disaggregation_pipeline(self=pipeline
                                                            )


