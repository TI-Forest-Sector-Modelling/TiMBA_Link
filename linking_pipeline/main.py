# imports
import datetime as dt
from linking_pipeline.logic.aggregation_pipeline import AggregateTiMBAResults
from linking_pipeline.logic.disaggregation_pipeline import DisaggregateCGEResults
from linking_pipeline.logic.calibration_pipeline import CalibrateTiMBA
from linking_pipeline.parameters.defines import VarNames
from linking_pipeline.parameters.default_parameters import (project_parameters, aggregation_parameters,
                                                            disaggregation_parameters, calibration_parameters)


class main_linking_pipeline(object):
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
        self.calibration_switch = project_parameters[VarNames.CALIBRATION_SWITCH.value]


if __name__ == '__main__':
    pipeline = main_linking_pipeline(
        project_parameters=project_parameters
    )

    if pipeline.aggregation_switch:
        AggregateTiMBAResults.main_aggregation_pipeline(
            self=pipeline,
            aggregation_parameters=aggregation_parameters
        )

    if pipeline.disaggregation_switch:
        DisaggregateCGEResults.main_disaggregation_pipeline(
            self=pipeline,
            disaggregation_parameters=disaggregation_parameters
        )
    if pipeline.calibration_switch:
        CalibrateTiMBA.main_calibration_pipeline(
            self=pipeline,
            calibration_parameters=calibration_parameters
        )




