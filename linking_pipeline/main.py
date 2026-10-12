# imports
import datetime as dt
from linking_pipeline.parameters.paths import DATA_FOLDER
from TiMBA.main import run_timba, parameter_setter
from linking_pipeline.logic.aggregation_pipeline import AggregateTiMBAResults
from linking_pipeline.logic.disaggregation_pipeline import DisaggregateCGEResults
from linking_pipeline.logic.calibration_pipeline import CalibrateTiMBA
from linking_pipeline.parameters.defines import VarNames
from linking_pipeline.parameters.default_parameters import (project_parameters, aggregation_parameters,
                                                            disaggregation_parameters, calibration_parameters)


class TiMBALink(object):
    def __init__(self,
                 project_parameters):

        self.current_scenario = project_parameters[VarNames.CURRENT_SC.value]
        self.current_dt = dt.datetime.now().strftime("%Y%m%d")
        self.link_typ = project_parameters[VarNames.LINK_TYPE.value]
        self.linked_CGE = project_parameters[VarNames.LINKED_CGE.value]
        self.project = project_parameters[VarNames.PROJECT.value]
        self.iter_num = project_parameters[VarNames.ITER_NUM.value]
        self.aggregation_switch = project_parameters[VarNames.AGGREGATION_SWITCH.value]
        self.disaggregation_switch = project_parameters[VarNames.DISAGGREGATION_SWITCH.value]
        self.run_timba_switch = project_parameters[VarNames.RUN_TIMBA_SWITCH.value]
        self.calibration_switch = project_parameters[VarNames.CALIBRATION_SWITCH.value]

    def run(self):
        """
        Main runner for TiMBA_Link
        """
        if self.disaggregation_switch:
            DisaggregateCGEResults.main_disaggregation_pipeline(
                self=self,
                disaggregation_parameters=disaggregation_parameters
            )

        if self.run_timba_switch:
            Parameters = parameter_setter()
            Parameters.max_period = 1
            run_timba(Parameters=Parameters,
                      folderpath=DATA_FOLDER)

        if self.aggregation_switch:
            AggregateTiMBAResults.main_aggregation_pipeline(
                self=self,
                aggregation_parameters=aggregation_parameters
            )

        if self.calibration_switch:
            CalibrateTiMBA.main_calibration_pipeline(
                self=self,
                calibration_parameters=calibration_parameters
            )


if __name__ == '__main__':
    timba_link_pipeline = TiMBALink(project_parameters=project_parameters)
    timba_link_pipeline.run()



