from typing import Union
import os
from pathlib import Path
import datetime as dt
import logging


def get_logger(user_path: Union[str, Path, None], aggregation_flag: bool):
    """
    Creates a basic logger with defined user_path, if aggregation_flag is true logger output is saved under
    data_aggregation (= used for aggregation scripts). If aggregation_flag is false logger output is saved under
    data_disaggregation (= used for disaggregation scripts).
    :param user_path: path where logger output is saved
    :param aggregation_flag: allows to select the storing folder
    :return:
    """
    current_dt = dt.datetime.now().strftime("%Y%m%d")
    if aggregation_flag:
        filename = rf"{current_dt}_aggregation.log"
        LOGGING_OUTPUT_FOLDER = r"output"
    else:
        filename = rf"{current_dt}_disaggregation.log"
        LOGGING_OUTPUT_FOLDER = r"output"

    if user_path is None:
        filepath = os.path.join(LOGGING_OUTPUT_FOLDER, filename)
    else:
        filepath = os.path.join(user_path, "output", filename)
    if not os.path.exists(filepath):
        os.makedirs(Path(filepath).parent, exist_ok=True)

    Logger = logging.getLogger("GFPMpt update world")
    Logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(lineno)s: %(message)s',
        '%d.%m.%y %H:%M:%S'
    )
    handler = logging.FileHandler(filepath, 'a+')
    handler.setFormatter(formatter)
    Logger.addHandler(handler)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(name)-10s: %(levelname)-10s %(message)s')
    console.setFormatter(console_formatter)
    Logger.addHandler(console)
    return Logger
