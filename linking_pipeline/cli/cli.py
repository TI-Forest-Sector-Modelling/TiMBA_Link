import click
from linking_pipeline.main import TiMBALink
from linking_pipeline.parameters.defines import VarNames
from linking_pipeline.parameters.default_parameters import project_parameters


@click.group()
def cli():
    pass


@cli.command("run")
@click.option(
    '-SC', '--current_scenario',
    default=project_parameters[VarNames.CURRENT_SC.value],
    show_default=True,
    required=True,
    type=str,
    help="Current scenario name."
)
@click.option(
    '-LT', '--link_type',
    default=project_parameters[VarNames.LINK_TYPE.value],
    show_default=True,
    required=True,
    type=str,
    help="Linkage type (options: `continuous` or `end_point`)."
)
@click.option(
    '-LM', '--linked_CGE',
    default=project_parameters[VarNames.LINKED_CGE.value],
    show_default=True,
    required=True,
    type=str,
    help="Linked CGE (options: `MAGNET` or `DART-BIO`)."
)
@click.option(
    '-P', '--project',
    default=project_parameters[VarNames.PROJECT.value],
    show_default=True,
    required=True,
    type=str,
    help="Current project name (options: `default_project` or own project name)."
)
@click.option(
    '-IN', '--iter_num',
    default=0,
    show_default=True,
    required=True,
    type=int,
    help="Current iteration number."
)
@click.option(
    '-AS', '--aggregation_switch',
    default=project_parameters[VarNames.AGGREGATION_SWITCH.value],
    show_default=True,
    required=True,
    type=click.BOOL,
    help="Switch for aggregation pipeline."
)
@click.option(
    '-DS', '--disaggregation_switch',
    default=project_parameters[VarNames.DISAGGREGATION_SWITCH.value],
    show_default=True,
    required=True,
    type=click.BOOL,
    help="Switch for disaggregation pipeline."
)
@click.option(
    '-TS', '--run_timba_switch',
    default=project_parameters[VarNames.RUN_TIMBA_SWITCH.value],
    show_default=True,
    required=True,
    type=click.BOOL,
    help="Switch for running TiMBA."
)
def timba_link_cli(
        current_scenario: str,
        link_type: str,
        linked_cge: str,
        project: str,
        iter_num: int,
        aggregation_switch: bool,
        disaggregation_switch: bool,
        run_timba_switch: bool,
):
    """
    Starts TiMBA_Link with defined cli project parameters
    :param current_scenario: Current scenario name
    :param link_type: Type of link
    :param linked_cge: Linked CGE
    :param project: Current project name
    :param iter_num: Current iteration number
    :param aggregation_switch: Switch for aggregation pipeline
    :param disaggregation_switch: Switch for disaggregation pipeline
    :param run_timba_switch: Switch for running timba
    """
    project_parameters_cli = {
        VarNames.CURRENT_SC.value: current_scenario,
        VarNames.LINK_TYPE.value: link_type,
        VarNames.LINKED_CGE.value: linked_cge,
        VarNames.PROJECT.value: project,
        VarNames.ITER_NUM.value: iter_num,
        VarNames.AGGREGATION_SWITCH.value: aggregation_switch,
        VarNames.DISAGGREGATION_SWITCH.value: disaggregation_switch,
        VarNames.RUN_TIMBA_SWITCH.value: run_timba_switch,
        VarNames.CALIBRATION_SWITCH.value: project_parameters[VarNames.CALIBRATION_SWITCH.value],
        VarNames.DETAILED_LOGGER.value: project_parameters[VarNames.DETAILED_LOGGER.value]
    }
    timba_link_cli = TiMBALink(project_parameters=project_parameters_cli)
    timba_link_cli.header()
    timba_link_cli.run()

