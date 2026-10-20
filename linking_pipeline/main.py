# imports
import datetime as dt
from linking_pipeline.logic.aggregation_pipeline import AggregateTiMBAResults
from linking_pipeline.logic.disaggregation_pipeline import DisaggregateCGEResults
from linking_pipeline.logic.run_timba_pipeline import RunTimbaPipeline
from linking_pipeline.logic.calibration_pipeline import CalibrateTiMBA
from linking_pipeline.parameters.defines import VarNames
from linking_pipeline.parameters.default_parameters import (project_parameters, aggregation_parameters,
                                                            disaggregation_parameters, calibration_parameters,
                                                            timba_parameters)


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
        self.detailed_logger = project_parameters[VarNames.DETAILED_LOGGER.value]

    def header(self):
        """
        Header of TiMBA_Link
        """
        print("==============================")
        print("========= TiMBA_Link =========")
        print("==============================")
        print("========= Parameters =========")
        print("==============================")
        print(f"Scenario: {self.current_scenario}")
        print(f"Iteration: {self.iter_num}")
        print(f"Link Type: {self.link_typ}")
        print(f"Linked CGE: {self.linked_CGE}")
        print(f"Aggregation switch: {self.aggregation_switch}")
        print(f"Disaggregation switch: {self.disaggregation_switch}")
        print(f"Run timba switch: {self.run_timba_switch}")
        print("==============================")

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
            RunTimbaPipeline.main_run_timba_pipeline(self=self,
                                                     timba_parameters=timba_parameters)

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
    timba_link_pipeline.header()
    timba_link_pipeline.run()



