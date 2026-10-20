
import shutil
import unittest
from pathlib import Path

from linking_pipeline.main import TiMBALink
from linking_pipeline.parameters.default_parameters import project_parameters
from linking_pipeline.parameters.defines import VarNames


class TestTiMBALinkIntegration(unittest.TestCase):
    """Integration tests for the complete TiMBA_Link pipeline."""

    @classmethod
    def setUpClass(cls):
        cls.PACKAGEDIR = Path(__file__).resolve().parents[1]

        cls.project_parameters_test = {
            VarNames.CURRENT_SC.value: project_parameters[
                VarNames.CURRENT_SC.value
            ],
            VarNames.LINK_TYPE.value: project_parameters[
                VarNames.LINK_TYPE.value
            ],
            VarNames.LINKED_CGE.value: project_parameters[
                VarNames.LINKED_CGE.value
            ],
            VarNames.PROJECT.value: project_parameters[
                VarNames.PROJECT.value
            ],
            VarNames.ITER_NUM.value: project_parameters[
                VarNames.ITER_NUM.value
            ],
            VarNames.AGGREGATION_SWITCH.value: True,
            VarNames.DISAGGREGATION_SWITCH.value: True,
            VarNames.RUN_TIMBA_SWITCH.value: True,
            VarNames.CALIBRATION_SWITCH.value: False,
            VarNames.DETAILED_LOGGER.value: False
        }

    def test_run_timba_link(self):
        """Tests execution of the complete TiMBA_Link pipeline."""

        timba_link = TiMBALink(
            project_parameters=self.project_parameters_test
        )

        timba_link.run()

    @classmethod
    def tearDownClass(cls):
        """Removes generated integration test output."""

        timba_link_path = cls.PACKAGEDIR / "TiMBA_Link"

        if timba_link_path.exists():
            shutil.rmtree(timba_link_path)


if __name__ == "__main__":
    unittest.main()
