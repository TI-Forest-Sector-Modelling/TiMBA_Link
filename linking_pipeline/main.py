# -----------------------------------------------------
# GFPMpt_linking_pipeline - aggregation_pipeline (Tomke Honkomp (TH) - Thuenen-Institut)
# GFPMpt-output aggregation to selected CGE (spatial and sectoral aggregation)
# Status: 03.2024
# Last update: 03.2024
# -----------------------------------------------------
# imports
import datetime as dt
from linking_pipeline.logic.aggregation_pipeline import AggregateGFPMptResults

class main_linking_pipeline(object):
    def __init__(self,
                 current_scenario: str,
                 input_path_gfpmpt: str,
                 link_typ: str,
                 linked_CGE: str,
                 project: str,
                 aggregation_switch: bool,
                 disaggregation_switch: bool):
        self.current_scenario = current_scenario
        self.current_dt = dt.datetime.now().strftime("%Y%m%d")
        self.input_path_gfpmpt = input_path_gfpmpt
        self.link_typ = link_typ
        self.linked_CGE = linked_CGE
        self.project = project
        self.aggregation_switch = aggregation_switch
        self.disaggregation_switch = disaggregation_switch


if __name__ == '__main__':
    pipeline = main_linking_pipeline(current_scenario='reference_scenario_SSP2_mea_elast',
                                     input_path_gfpmpt='DataContainer_Sc_20240227_Updated_World_2015_only_SSP2_DSp1E_Mea18',
                                     link_typ='continous',  # Alternatives: 'continous', 'end_point'
                                     linked_CGE='MAGNET',  # Alternatives: 'DART-BIO', 'MAGNET'
                                     project='CarbonLeak',    # Alternatives: 'BioSDG', 'CarbonLeak', 'BEPASO'
                                     # Note: linked_CGE and project must be harmonized (e.g., DART-BIO + BioSDG)
                                     aggregation_switch=True,
                                     disaggregation_switch=False)

    if pipeline.aggregation_switch:
        AggregateGFPMptResults.main_aggregation_pipeline(self=pipeline,
                                                         domains_to_aggregate=['production', 'forest', 'carbon']
                                                         # Alternatives: 'production', 'forest', 'carbon'
                                                         )

