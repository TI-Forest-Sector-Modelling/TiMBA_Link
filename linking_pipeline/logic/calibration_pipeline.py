# imports
import pandas as pd
import numpy as np
import pickle
import gzip
import os
from pathlib import Path
import datetime as dt
from linking_pipeline.helper_functions.base_logger import get_logger
from linking_pipeline.parameters.defines import Constants, ProductStructures


class CalibrateTiMBA(object):
    def __init__(self,
                 current_scenario: str,
                 input_path_timba: str,
                 input_path_cge: str,
                 link_typ: str,
                 linked_CGE: str,
                 project: str
                 ):
        self.sfile = os.path.dirname(Path(__file__).resolve().parents[0])
        self.Logger = get_logger(user_path=None, aggregation_flag=True)
        self.current_scenario = current_scenario
        self.current_dt = dt.datetime.now().strftime("%Y%m%d")
        self.input_path_timba = input_path_timba
        self.input_path_cge = input_path_cge
        self.link_typ = link_typ
        self.linked_CGE = linked_CGE
        self.project = project
        self.timba_data, self.timba_data_add, self.magnet_data = CalibrateTiMBA.readin_model_data(self)
        (self.region_key, self.commodity_key) = CalibrateTiMBA.readin_help_data(self)

        self.calibration_data = None

    def readin_help_data(self):
        # read in region aggregation
        # read in sector aggregation
        self.Logger.info(f"Read in help data.")
        timba_commodities = self.timba_data['CommodityCode'].unique()

        if len(timba_commodities) == 14:
            commodity_key = pd.DataFrame.from_dict(ProductStructures.com_info_14.value)
        if len(timba_commodities) == 16:
            if self.project == 'BioSDG':
                commodity_key = pd.DataFrame.from_dict(ProductStructures.com_info_16_biosdg.value)
            else:
                commodity_key = pd.DataFrame.from_dict(ProductStructures.com_info_16.value)

        region_key = pd.ExcelFile(f'{self.sfile}\\data\\input\\m_Country.xlsx')
        region_key = region_key.parse('m_Country')
        region_key = region_key[['GFPM_CountryCode', 'GTAP10', f'{self.linked_CGE}_{self.project}']]
        region_key = region_key[~region_key[f'{self.linked_CGE}_{self.project}'].isna()].reset_index(drop=True)

        return region_key, commodity_key

    def readin_model_data(self):
        self.Logger.info(f"Read in TiMBA results {self.input_path_timba}.")
        src_path = f'{self.sfile}\\data\\input\\{self.input_path_timba}.pkl'

        try:
            with open(src_path, "rb") as pkl_file:
                timba_data = pickle.load(pkl_file)
        except pickle.UnpicklingError:
            with gzip.open(src_path, "rb") as pkl_file:
                timba_data = pickle.load(pkl_file)

        timba_data = timba_data["data_periods"]
        timba_data = timba_data[(timba_data["domain"] == "Supply") | (timba_data["domain"] == "ManufactureCost")]
        timba_data_add = timba_data.groupby(["RegionCode", "CommodityCode", "year", "Period"])[
            ["price", "elasticity_price"]].sum().reset_index()

        timba_data = timba_data.groupby(["RegionCode", "CommodityCode", "year", "Period"])[
            "quantity"].sum().reset_index()
        timba_data = timba_data[timba_data["RegionCode"] != "zy"].reset_index(drop=True)
        timba_data["domain"] = "Supply"
        self.Logger.info(f"Read in MAGNET results {self.input_path_cge}.")
        src_path = f'{self.sfile}\\data\\input\\{self.input_path_cge}.csv'
        magnet_data = pd.read_csv(src_path)

        return timba_data, timba_data_add, magnet_data

    def calc_weights(self):
        """
        Calculates weights for each TiMBA product and region in each MAGNET regions and sectors. Weights are saved in
        timba_data.
        """
        self.Logger.info(f"Calculate weights for CGE dissaggregation")
        timba_data = self.timba_data
        cge_region = self.region_key
        cge_sector = self.commodity_key
        timba_data = timba_data.merge(cge_sector, left_on="CommodityCode", right_on="GFPMpt_Comcode", how="left")
        timba_data = timba_data.merge(cge_region, left_on="RegionCode", right_on="GFPM_CountryCode", how="left")
        cge_sum = timba_data.groupby([f"{self.linked_CGE}_{self.project}", "GTAP-Sector", "year", "Period"])["quantity"].sum().reset_index()
        cge_sum = cge_sum.rename(columns={"quantity": "cge_sum"})
        timba_data = timba_data.merge(
            cge_sum,
            left_on=[f"{self.linked_CGE}_{self.project}", "GTAP-Sector", "year", "Period"],
            right_on=[f"{self.linked_CGE}_{self.project}", "GTAP-Sector", "year", "Period"],
            how="left")
        timba_data["weight"] = timba_data["quantity"] / timba_data["cge_sum"]
        timba_data["weight"] = timba_data["weight"].fillna(0)

        self.timba_data = timba_data

    def dissagg_cge_data(self):
        """
        Dissaggregates CGE data using calculated weights for MAGNET regions and sectors. Dissaggregated data are saved
        in magnet_data.
        """
        self.Logger.info(f"Dissaggregate CGE data")
        cge_data = self.magnet_data
        weights = self.timba_data[["RegionCode", "CommodityCode", "year", "Period",
                                   f"{self.linked_CGE}_{self.project}", "GTAP-Sector", "weight"]]
        cge_data = weights.merge(
            cge_data,
            left_on=[f"{self.linked_CGE}_{self.project}", "GTAP-Sector", "year"],
            right_on=["region", "sector", "year"], how="left")

        cge_data["dissagg_quantity"] = cge_data["weight"] * cge_data["quantity"]
        cge_data["dissagg_quantity"] = cge_data["dissagg_quantity"].fillna(0)
        self.magnet_data = cge_data

    def calc_rel_change(self):
        """
        Calculates relative changes in production for TiMBA and MAGNET.
        :return: DataFrame with relative changes in production for TiMBA and MAGNET.
        """
        timba_data = self.timba_data
        cge_data = self.magnet_data

        growth_data = pd.DataFrame()
        if len(timba_data["year"].unique()) == len(cge_data["year"].unique()):
            prev_year = timba_data["year"].unique()[0]
            for present_year in timba_data["year"].unique()[1: ]:
                timba_data_present = timba_data[timba_data["year"] == present_year].reset_index(drop=True)
                timba_data_prev = timba_data[timba_data["year"] == prev_year].reset_index(drop=True)

                magnet_data_present = cge_data[cge_data["year"] == present_year].reset_index(drop=True)
                magnet_data_prev = cge_data[cge_data["year"] == prev_year].reset_index(drop=True)

                growth_data_info = timba_data_present[["RegionCode", "CommodityCode", "year", "Period"]].copy()
                timba_growth = (timba_data_present["quantity"] -
                                timba_data_prev["quantity"]) / timba_data_prev["quantity"] * 100
                magnet_growth = (magnet_data_present["quantity"] -
                                 magnet_data_prev["quantity"]) / magnet_data_prev["quantity"] * 100

                growth_data_info["timba_growth"] = timba_growth
                growth_data_info["magnet_growth"] = magnet_growth

                growth_data = pd.concat([growth_data, growth_data_info], axis=0).reset_index(drop=True)

                prev_year = present_year

            growth_data["growth_diff"] = growth_data["magnet_growth"] - growth_data["timba_growth"]

        else:
            self.Logger.info(f"year structure of TiMBA and MAGNET does not match; check input data")

        return growth_data

    def calc_calibration_param(self):
        """
        Calculates calibration parameters (new supply, gamma, slope, and intercept) based on TiMBA and MAGNET data
        :return: Updated calibration DataFrame
        """
        self.Logger.info(f"Calculate calibration parameters")
        calibration_data = self.calibration_data
        timba_data = self.timba_data
        timba_data_add = self.timba_data_add

        timba_data = timba_data[timba_data["Period"] != 0].reset_index(drop=True)
        timba_data = timba_data.sort_values(by=["RegionCode", "CommodityCode", "Period"])

        timba_data_add = timba_data_add[(timba_data_add["Period"] != 0) &
                                        (timba_data_add["RegionCode"] != "zy")].reset_index(drop=True)

        calibration_data["new_supply"] = (1 + (calibration_data["growth_diff"] +
                                               calibration_data["timba_growth"]) / 100) * timba_data["quantity"]

        calibration_data["gamma"] = (timba_data_add["elasticity_price"] * calibration_data["new_supply"]
                                     ) / timba_data_add["price"]
        calibration_data["gamma"] = calibration_data["gamma"].fillna(0)
        calibration_data["gamma"] = calibration_data["gamma"].replace([np.inf, -np.inf], 0)
        calibration_data["slope"] = calibration_data["new_supply"] - (calibration_data["gamma"] * timba_data_add["price"])
        calibration_data["intercept"] = - (calibration_data["slope"] / calibration_data["gamma"])
        calibration_data["intercept"] = calibration_data["intercept"].replace([np.inf, -np.inf], 0)

        return calibration_data

    def save_calibration_data(self):
        """
        Saves calibration data for implementation in TiMBA
        """
        self.Logger.info(f"Save calibration data")
        calibration_data = self.calibration_data
        calibration_data.to_csv(f"{self.sfile}\\data\\output\\magnet_calibration_data.csv", index=False)

    def main_calibration_pipeline(self):
        Pipeline_Cali = CalibrateTiMBA(
            current_scenario=self.current_scenario,
            input_path_timba=self.input_path_timba,
            input_path_cge=self.input_path_CGE,
            link_typ=self.link_typ,  # Alternatives: 'continuous', 'end_point'
            linked_CGE=self.linked_CGE,  # Alternatives: 'DART-BIO', 'MAGNET'
            project=self.project  # Alternatives: 'BioSDG', 'CarbonLeak', 'BEPASO'
            # Note: linked_CGE and project must be harmonized (e.g., DART-BIO + BioSDG)
        )
        Pipeline_Cali.calc_weights()
        Pipeline_Cali.dissagg_cge_data()
        Pipeline_Cali.calibration_data = Pipeline_Cali.calc_rel_change()
        Pipeline_Cali.calibration_data = Pipeline_Cali.calc_calibration_param()
        Pipeline_Cali.save_calibration_data()
