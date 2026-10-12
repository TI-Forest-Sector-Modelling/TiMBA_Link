from linking_pipeline.parameters.defines import VarNames

project_parameters = {
    VarNames.CURRENT_SC.value: "default_scenario",
    VarNames.LINK_TYPE.value: "end_point",
    VarNames.LINKED_CGE.value: "MAGNET",
    VarNames.PROJECT.value: "default_project",
    VarNames.ITER_NUM.value: "iterx",
    VarNames.AGGREGATION_SWITCH.value: False,
    VarNames.DISAGGREGATION_SWITCH.value: True,
    VarNames.CALIBRATION_SWITCH.value: False
}

aggregation_parameters = {
    VarNames.INPUT_TIMBA.value:"default_timba_scenario_output",
    VarNames.DOMAINS_TO_AGGREGATE.value: ["production", 'forest', 'carbon', 'io']
}

disaggregation_parameters = {
    VarNames.INPUT_TIMBA_TO_UPDATE.value: "default_timba_scenario_input",
    VarNames.INPUT_GDP_CGE.value: "default_cge_GDP",
    VarNames.INPUT_FOREST_CGE.value: "default_cge_FOREST",
    VarNames.LINKED_VAR.value: ["gdp", "gdp_cap", "forest_area"],
    VarNames.UPDATED_FILE.value: "xlsx"
}

timba_parameters = {

}

calibration_parameters = {

}