from TiMBA.main import run_timba, parameter_setter
from TiMBA.data_management.Load_Data import load_data

from TiMBA.data_management.DataManager import DataManager
from TiMBA.data_management.DataContainer import WorldDataCollector
from linking_pipeline.parameters.paths import DATA_FOLDER
from linking_pipeline.parameters.defines import VarNames
from linking_pipeline.parameters.paths import (GIT_FOLDER, GIT_REPO, GIT_BRANCH, GIT_USER, TIMBA_ADD_INFO,
                                               TIMBA_SERIALIZATION)
import os
from pathlib import Path
import shutil


class RunTimbaPipeline(object):
    def __init__(self,
                 max_period: int):
        self.max_period = max_period

    def load_additional_data(self):
        """
        Loads additional data from TiMBA package
        """
        load_data(
            user=GIT_USER,
            repo=GIT_REPO,
            branch=GIT_BRANCH,
            source_folder=GIT_FOLDER,
            dest_folder=TIMBA_ADD_INFO
        )

    def serialize_input_data(self):
        """
        Serializes TiMBA input data
        """
        from linking_pipeline.parameters.paths import TIMBA_INPUT_FILES
        INPUT_FILE = next((f.name for f in Path(TIMBA_INPUT_FILES).iterdir() if f.is_file()), None)
        INPUT_PATH = TIMBA_INPUT_FILES / INPUT_FILE
        TARGET_FILE = r"WorldDataContent.pkl"

        try:
            os.makedirs(TIMBA_SERIALIZATION, exist_ok=True)
        except FileExistsError:
            print("file_exists")
            pass

        WorldDataContent = WorldDataCollector(INPUT_PATH)
        TARGET_PATH = TIMBA_SERIALIZATION / TARGET_FILE
        DataManager.serialize_to_pickle(
            obj=WorldDataContent,
            target_filepath=TARGET_PATH
        )

    def run_timba(self):
        Parameters = parameter_setter()
        Parameters.max_period = self.max_period
        run_timba(Parameters=Parameters,
                  folderpath=DATA_FOLDER)

    def save_and_clear_timba_input(self):
        """
        Saves generated TiMBA input data to log input and clears TiMBA input folder to avoid unintended multiple TiMBA
        runs.
        """
        from linking_pipeline.parameters.paths import TIMBA_INPUT_FILES
        INPUT_FILE = next((f.name for f in Path(TIMBA_INPUT_FILES).iterdir() if f.is_file()), None)
        INPUT_PATH = TIMBA_INPUT_FILES / INPUT_FILE
        shutil.move(src=INPUT_PATH,
                    dst=DATA_FOLDER / "output" / "disaggregation")

    def main_run_timba_pipeline(self, timba_parameters):
        """
        Main function for running timba pipeline
        :param timba_parameters: Dict holding timba parameters defined by the user
        """
        RunTimba_Pipeline = RunTimbaPipeline(max_period=timba_parameters[VarNames.MAX_PERIOD.value])
        RunTimba_Pipeline.load_additional_data()
        RunTimba_Pipeline.serialize_input_data()
        RunTimba_Pipeline.run_timba()
        RunTimba_Pipeline.save_and_clear_timba_input()
