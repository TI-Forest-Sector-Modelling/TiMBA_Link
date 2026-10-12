
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from linking_pipeline.cli.cli import cli
from linking_pipeline.parameters.default_parameters import project_parameters
from linking_pipeline.parameters.defines import VarNames


class TestTiMBALinkCLI(unittest.TestCase):
    """Tests CLI functionality without running the model."""

    def setUp(self):
        self.runner = CliRunner()

    def test_cli_run_command(self):
        """Tests CLI argument parsing and model initialization."""

        with patch("linking_pipeline.cli.cli.TiMBALink") as mock_timba_link:
            result = self.runner.invoke(
                cli,
                [
                    "run",
                    "--current_scenario", "scenario",
                    "--link_type", "continuous",
                    "--linked_CGE", "MAGNET",
                    "--project", "default_project",
                    "--iter_num", "1",
                    "--aggregation_switch", "False",
                    "--disaggregation_switch", "False",
                    "--run_timba_switch", "False",
                ],
            )

            self.assertEqual(
                result.exit_code,
                0,
                msg=f"{result.output}\n{result.exception!r}",
            )

            expected_parameters = {
                VarNames.CURRENT_SC.value: "scenario",
                VarNames.LINK_TYPE.value: "continuous",
                VarNames.LINKED_CGE.value: "MAGNET",
                VarNames.PROJECT.value: "default_project",
                VarNames.ITER_NUM.value: 1,
                VarNames.AGGREGATION_SWITCH.value: False,
                VarNames.DISAGGREGATION_SWITCH.value: False,
                VarNames.RUN_TIMBA_SWITCH.value: False,
                VarNames.CALIBRATION_SWITCH.value: project_parameters[
                    VarNames.CALIBRATION_SWITCH.value
                ],
            }

            mock_timba_link.assert_called_once_with(
                project_parameters=expected_parameters
            )
            mock_timba_link.return_value.run.assert_called_once_with()

    def test_cli_help(self):
        """Tests the main CLI help command."""

        result = self.runner.invoke(cli, ["--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("run", result.output)

    def test_cli_run_help(self):
        """Tests the run command help."""

        result = self.runner.invoke(cli, ["run", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("--current_scenario", result.output)
        self.assertIn("--aggregation_switch", result.output)

    def test_cli_invalid_iteration(self):
        """Tests invalid iteration input."""

        result = self.runner.invoke(
            cli,
            ["run", "--iter_num", "invalid"],
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Invalid value", result.output)


if __name__ == "__main__":
    unittest.main()
