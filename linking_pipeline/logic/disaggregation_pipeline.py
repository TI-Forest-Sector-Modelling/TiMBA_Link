# imports
import pandas as pd
import numpy as np
import pickle
import gzip
import os
import shutil
from pathlib import Path
from linking_pipeline.parameters.paths import (INPUT_PATH, OUTPUT_PATH, INPUT_POP_DART_BIO, INPUT_POP_MAGNET,
                                               COUNTRY_CONCORDANCE_TIMBA, COUNTRY_CONCORDANCE_WB_OECD,
                                               INPUT_GDP_WORLD_BANK, INPUT_GDP_OECD, INPUT_FRA)
from openpyxl import load_workbook
import datetime as dt
from linking_pipeline.helper_functions.base_logger import get_logger
from linking_pipeline.parameters.defines import Constants, ProductStructures


class DisaggregateCGEResults(object):
    def __init__(self,
                 current_scenario: str,
                 input_path_timba: str,
                 input_gdp_CGE: str,
                 input_world: str,
                 input_forest_CGE: str,
                 link_typ: str,
                 linked_CGE: str,
                 linked_var: list,
                 project: str,
                 updated_file: str
                 ):
        self.Logger = get_logger(user_path=None, aggregation_flag=True)
        self.current_scenario = current_scenario
        self.current_dt = dt.datetime.now().strftime("%Y%m%d")
        self.input_path_timba = input_path_timba
        self.input_gdp_CGE = input_gdp_CGE
        self.input_world = input_world
        self.input_forest_CGE = input_forest_CGE
        self.link_typ = link_typ
        self.linked_CGE = linked_CGE
        self.linked_var = linked_var
        self.project = project
        self.updated_file = updated_file
        self.cge_data, self.timba_data, self.timba_input = DisaggregateCGEResults.readin_model_data(self, updated_file)

        self.region_key = None
        self.region_key_timba = None
        self.commodity_key = None
        self.oecd_data = None
        self.worldbank_data = None
        self.fra_data = None
        self.cge_forest_data = None
        self.exogenous_change_structure = None
        self.exogenous_change_structure_cge = None
        self.start_year = None
        self.end_year = None
        self.year_for_avg = None

        self.worldbank_gdp_weights = None
        self.worldbank_pop_weights = None
        self.forest_weights = None
        self.disagg_forest_data = None
        self.disagg_gdp_data = None
        self.disagg_pop_data = None
        self.disagg_gdp_cap_data = None
        self.growth_rate_gdp = None
        self.growth_rate_gdp_cap = None
        self.new_exogChange = None

    def readin_model_data(self, updated_file):
        """
        Read in projection data from CGE for disaggregation. Processed data are specific to the linked CGE and the
        project. Add specific if-statements in the following to account for project specific TiMBA-CGE-linkages.
        :param updated_file: File format that has been chosen to be updated
        :return: Project and CGE model specific return (see in function for details)
        """
        self.Logger.info(f'Read in TiMBA results {self.input_path_timba}.')
        src_path_1 = f'{INPUT_PATH}\\{self.input_path_timba}.pkl'
        src_path_2 = f'{INPUT_PATH}\\{self.input_world}.{updated_file}'

        try:
            with open(src_path_1, "rb") as pkl_file:
                timba_data = pickle.load(pkl_file)
        except pickle.UnpicklingError:
            with gzip.open(src_path_1, "rb") as pkl_file:
                timba_data = pickle.load(pkl_file)

        if updated_file == "xlsx":
            timba_input = pd.ExcelFile(src_path_2)
            timba_input = timba_input.parse('ExogChange')
        else:
            try:
                with open(src_path_2, "rb") as pkl_file:
                    timba_input = pickle.load(pkl_file)
            except pickle.UnpicklingError:
                with gzip.open(src_path_2, "rb") as pkl_file:
                    timba_input = pickle.load(pkl_file)

        cge_data = {}
        if ('gdp' in self.linked_var) or ('gdp_cap' in self.linked_var):
            self.Logger.info(f'Read in {self.input_gdp_CGE} for GDP.')
            cge_gdp_data = pd.read_csv(f'{INPUT_PATH}\\{self.input_gdp_CGE}.csv')
            if len(cge_gdp_data.columns) == 1:
                cge_gdp_data = pd.read_csv(f'{INPUT_PATH}\\{self.input_gdp_CGE}.csv', delimiter=';')
            cge_gdp_data.columns = DisaggregateCGEResults.convert_year_col_to_int(self, data=cge_gdp_data)
            cge_gdp_data = DisaggregateCGEResults.interpolate_cge_data_missing_years(self,
                                                                                     data=cge_gdp_data,
                                                                                     growth_rate="exponential")

            cge_data['gdp'] = cge_gdp_data
            self.Logger.info(f'Read in constant POP data from {self.linked_CGE}.')
            if self.linked_CGE == "DART-BIO":
                cge_pop_data = pd.ExcelFile(f'{INPUT_POP_DART_BIO}')
            if self.linked_CGE == "MAGNET":
                cge_pop_data = pd.ExcelFile(f'{INPUT_POP_MAGNET}')
            cge_pop_data = cge_pop_data.parse('pop in million')
            cge_pop_data.columns = DisaggregateCGEResults.convert_year_col_to_int(self, data=cge_pop_data)
            cge_pop_data = DisaggregateCGEResults.interpolate_cge_data_missing_years(self,
                                                                                     data=cge_pop_data,
                                                                                     growth_rate="linear")
            cge_data['pop'] = cge_pop_data

        if 'forest_area' in self.linked_var:
            # TODO implement readin for forest data
            # cge_forest_area_data = pd.read_csv()
            # cge_data['forest_area'] = cge_forest_area_data
            pass

        return cge_data, timba_data, timba_input

    def readin_help_data(self):
        """
        Read in help data to disaggregate CGE data to product- and country-structure of TiMBA.
        :return: Project and CGE model specific return (see in function for details)
        """
        self.Logger.info(f"Read in help data.")

        exogenous_change_data = self.timba_data['data_periods'][
            ['Period', 'year']].drop_duplicates().reset_index(drop=True)
        start_year = exogenous_change_data['year'][0]
        end_year = exogenous_change_data['year'][max(exogenous_change_data.index)]

        exogenous_change_structure = {}
        year_prev = exogenous_change_data['year'][0]
        for period in exogenous_change_data['Period'][1:]:
            index = exogenous_change_data[exogenous_change_data['Period'] == period]['year'].index[0]
            year = exogenous_change_data[exogenous_change_data['Period'] == period]['year'][index]
            period_len = year - year_prev
            exogenous_change_structure[f'Period_{period}'] = [year_prev, period_len]
            year_prev = year

        timba_commodities = self.timba_data['data_periods']['CommodityCode'].unique()

        if len(timba_commodities) == 14:
            commodity_key = pd.DataFrame.from_dict(ProductStructures.com_info_14.value)
        if len(timba_commodities) == 16:
            if self.project == 'BioSDG':
                commodity_key = pd.DataFrame.from_dict(ProductStructures.com_info_16_biosdg.value)
            else:
                commodity_key = pd.DataFrame.from_dict(ProductStructures.com_info_16.value)

        region_key_timba = pd.ExcelFile(f'{COUNTRY_CONCORDANCE_TIMBA}')
        region_key_timba = region_key_timba.parse('m_Country')
        region_key_timba = region_key_timba[['GFPM_CountryCode', 'GTAP10', f'{self.linked_CGE}_{self.project}',
                                             'ISO-Code']]

        if ('gdp' in self.linked_var) or ('gdp_cap' in self.linked_var):

            oecd_data_collector = {}
            oecd_data = pd.ExcelFile(f'{INPUT_GDP_OECD}')
            oecd_gdp_data = oecd_data.parse('GDP_OECD')
            oecd_pop_data = oecd_data.parse('Pop_OECD_mio')
            oecd_data_collector['gdp'] = oecd_gdp_data
            oecd_data_collector['pop'] = oecd_pop_data

            worldbank_data_collector = {}
            worldbank_data = pd.ExcelFile(f'{INPUT_GDP_WORLD_BANK}')
            worldbank_gdp_data = worldbank_data.parse('worldbank_GDP')
            years_for_average = list(range(start_year - 1, start_year + 2))  # 3-years average
            col_selection = ['Country Name', 'Country Code'] + years_for_average
            worldbank_gdp_data = worldbank_gdp_data[col_selection]
            worldbank_gdp_data = worldbank_gdp_data.dropna()
            worldbank_pop_data = worldbank_data.parse('worldbank_Pop')
            worldbank_pop_data = worldbank_pop_data[col_selection]
            worldbank_pop_data = worldbank_pop_data.dropna()

            worldbank_data_collector['gdp'] = worldbank_gdp_data
            worldbank_data_collector['pop'] = worldbank_pop_data

            region_oecd_worldbank = pd.ExcelFile(f'{COUNTRY_CONCORDANCE_WB_OECD}')
            region_oecd_worldbank = region_oecd_worldbank.parse('Country_codes').dropna()

            region_key_all = region_key_timba.merge(region_oecd_worldbank, left_on="ISO-Code",
                                                   right_on="Worldbank_Ccodes", how="left"
                                                   ).dropna().reset_index(drop=True)
            region_key_all = region_key_all[['GFPM_CountryCode', 'GTAP10', f'{self.linked_CGE}_{self.project}',
                                             'ISO-Code', 'OECD_Ccodes']]

            self.region_key = region_key_all
            self.oecd_data = oecd_data_collector
            self.worldbank_data = worldbank_data_collector
            self.year_for_avg = years_for_average

        if "forest_area" in self.linked_var:
            cge_forest_data = pd.read_csv(f"{INPUT_PATH}\\{self.input_forest_CGE}.csv",
                                          delimiter=";")
            if len(cge_forest_data.columns) == 1:
                cge_forest_data = pd.read_csv(f"{INPUT_PATH}\\{self.input_forest_CGE}.csv",
                                              delimiter=",")

            fra_forest_data = pd.read_csv(f"{INPUT_FRA}")

            self.cge_forest_data = cge_forest_data
            self.fra_data = fra_forest_data

            exogenous_change_structure_cge = {}
            period_list = list(cge_forest_data["year"].unique())
            period_runner = 1
            year_prev = period_list[0]
            for year in period_list[1:]:
                period_len = year - year_prev
                exogenous_change_structure_cge[f'Period_{period_runner}'] = [year_prev, period_len]
                period_runner += 1
                year_prev = year

        self.exogenous_change_structure = exogenous_change_structure
        if self.linked_CGE == 'MAGNET':
            self.exogenous_change_structure_cge = exogenous_change_structure_cge
        self.start_year = start_year
        self.end_year = end_year
        self.commodity_key = commodity_key
        self.region_key_timba = region_key_timba

    def convert_year_col_to_int(self, data):
        """
        Converts year col from str to int
        :param data: Dataframe with columns to be converted
        :return: column list with converted column names
        """
        data_col = data.columns
        data_col_new = []
        for col in data_col:
            try:
                new_col = int(col)
                data_col_new.append(new_col)
            except ValueError:
                data_col_new.append(col)
        return data_col_new

    def interpolate_cge_data_missing_years(self, data, growth_rate):
        """
        Interpolates cge data for missing years using either exponential or linear growth rates
        :param data: CGE data to interpolate
        :param growth_rate: growth rate used for interpolation (options: exponential or linear growth)
        :return: interpolated CGE data
        """
        year_list = []
        for col in data.columns:
            if isinstance(col, int):
                year_list.append(col)
        runner = 0
        for year in year_list[1:]:
            year_prev = year_list[runner]
            missing_year_num = list(np.ones((year - year_prev) - 1))
            missing_year_start = year_prev
            if growth_rate == "linear":
                year_diff = (data[year] - data[year_prev]) / (year - year_prev)
            if growth_rate == "exponential":
                year_diff = (data[year] / data[year_prev]) ** (1 / (year - year_prev)) - 1
            if len(missing_year_num) > 0:
                for missing_year in missing_year_num:
                    missing_year_start = int(missing_year_start + missing_year)
                    if growth_rate == "linear":
                        data[missing_year_start] = data[year_prev] + year_diff
                    if growth_rate == "exponential":
                        data[missing_year_start] = data[year_prev] * (1 + year_diff)
                    year_prev += missing_year
            runner += 1

        data = pd.concat([data.iloc[:, :1],
                          data.iloc[:, 1:].sort_index(axis=1)], axis=1)
        return data

    def process_cge_forest_data(self, linkage_type: str):
        """
        Processes forest data from linked CGE
        :param linkage_type: Defines if the linkage is continuous (= for all periods) or end-point (= for end period).
        :return: DataFrame of processed forestland data
        """
        cge_forest_data = self.cge_forest_data.copy()

        cge_forest_data_new = pd.DataFrame()
        if linkage_type == "continuous":
            start_year_index = 0
            for end_year in cge_forest_data["year"].unique()[1:]:
                start_year = cge_forest_data["year"].unique()[start_year_index]
                forest_data_end = cge_forest_data[cge_forest_data["year"] == end_year].reset_index(drop=True)
                forest_data_start = cge_forest_data[cge_forest_data["year"] == start_year].reset_index(drop=True)

                forest_data_end["forestland_change"] = (
                        (forest_data_end["forestland_change"] /
                         forest_data_start["forestland_change"]) ** (1 / (end_year - start_year)) - 1)

                cge_forest_data_new = pd.concat([cge_forest_data_new,
                                                 forest_data_end], axis=0).reset_index(drop=True)
                start_year_index += 1

        if linkage_type == "end_point":
            end_year = cge_forest_data["year"].max()
            start_year = cge_forest_data["year"].min()

            forest_data_end = cge_forest_data[cge_forest_data["year"] == end_year].reset_index(drop=True)
            forest_data_start = cge_forest_data[cge_forest_data["year"] == start_year].reset_index(drop=True)

            forest_data_end["forestland_change"] = (
                    (forest_data_end["forestland_change"] /
                     forest_data_start["forestland_change"]) ** (1 / (end_year - start_year)) - 1)

            cge_forest_data_new = forest_data_end

        return cge_forest_data_new

    def calc_worldbank_gdp_weights(self):
        """
        Calculates GDP weights based on 3-years average of GDP data from Worldbank to disaggregate CGE data of GDP to
        country level of TiMBA. Disaggregation of GDP data assumes that GDP shares of countries in each CGE region is
        not changing over the projection period.
        :return: GDP weights for each country in each regions of the linked CGE model.
        """
        self.Logger.info(f'Calculate GDP-weights using Worldbank GDP-data to disaggregate {self.linked_CGE} data'
                         f' for {self.project}.')

        worldbank_gdp_data = self.worldbank_data['gdp']

        worldbank_gdp_data = worldbank_gdp_data.merge(self.region_key, left_on="Country Code", right_on="ISO-Code",
                                                      how="left").dropna()
        worldbank_gdp_data['avg_gdp'] = (np.sum(worldbank_gdp_data[self.year_for_avg], axis=1) /
                                         len(self.year_for_avg))
        worldbank_gdp_data = worldbank_gdp_data[['Country Name', 'ISO-Code', 'GFPM_CountryCode', 'OECD_Ccodes',
                                                 f'{self.linked_CGE}_{self.project}', 'avg_gdp']].reset_index(drop=True)
        # todo remove when finished
        # gdp_data_grouped_oecd_level = worldbank_gdp_data.groupby(["OECD_Ccodes"])["average_gdp"].sum().reset_index()
        # todo remove until here
        gdp_data_grouped_cge_lvl = worldbank_gdp_data.groupby([f'{self.linked_CGE}_{self.project}']
                                                              )['avg_gdp'].sum().reset_index()
        worldbank_gdp_data = worldbank_gdp_data.merge(
            gdp_data_grouped_cge_lvl,
            left_on=f'{self.linked_CGE}_{self.project}',
            right_on=f'{self.linked_CGE}_{self.project}',
            how='left').rename(columns={'avg_gdp_x': 'avg_gdp_WB',
                                        'avg_gdp_y': f'avg_gdp_{self.linked_CGE}_{self.project}'})
        worldbank_gdp_data['gdp_weights'] = (worldbank_gdp_data['avg_gdp_WB'] /
                                             worldbank_gdp_data[f'avg_gdp_{self.linked_CGE}_{self.project}'])

        return worldbank_gdp_data

    def calc_worldbank_pop_weights(self):
        """
        Calculates population weights based on 3-years average of population data from Worldbank to disaggregate CGE
        data of population to country level of TiMBA. Disaggregation of population data assumes that GDP shares of
        countries in each CGE region is not changing over the projection period.
        :return: Population weights for each country in each regions of the linked CGE model.
        """
        self.Logger.info(f'Calculate popluations weights using Worldbank population data to disaggregate '
                         f'{self.linked_CGE} data for {self.project}.')

        worldbank_pop_data = self.worldbank_data['pop']

        worldbank_pop_data = worldbank_pop_data.merge(self.region_key, left_on="Country Code", right_on="ISO-Code",
                                                      how="left").dropna()
        worldbank_pop_data['avg_pop'] = (np.sum(worldbank_pop_data[self.year_for_avg], axis=1) /
                                         len(self.year_for_avg))
        worldbank_pop_data = worldbank_pop_data[['Country Name', 'ISO-Code', 'GFPM_CountryCode', 'OECD_Ccodes',
                                                 f'{self.linked_CGE}_{self.project}', 'avg_pop']].reset_index(drop=True)
        # todo remove when finished
        # pop_data_grouped_oecd_level = worldbank_pop_data.groupby(["OECD_Ccodes"])["average_pop"].sum().reset_index()
        # todo remove until here
        pop_data_grouped_cge_lvl = worldbank_pop_data.groupby([f'{self.linked_CGE}_{self.project}']
                                                              )['avg_pop'].sum().reset_index()
        worldbank_pop_data = worldbank_pop_data.merge(
            pop_data_grouped_cge_lvl,
            left_on=f'{self.linked_CGE}_{self.project}',
            right_on=f'{self.linked_CGE}_{self.project}',
            how='left').rename(columns={'avg_pop_x': 'avg_pop_WB',
                                        'avg_pop_y': f'avg_pop_{self.linked_CGE}_{self.project}'})
        worldbank_pop_data['pop_weights'] = (worldbank_pop_data['avg_pop_WB'] /
                                             worldbank_pop_data[f'avg_pop_{self.linked_CGE}_{self.project}'])

        return worldbank_pop_data

    def calc_forest_weights(self, split_forest_type: bool, fra_splitting: bool):
        """
        Calculates country-specific weights for each CGE region based on forest data provided by the forest resource
        assessment.
        :param split_forest_type: Flag controls if forest area type (managed and unmanaged forest) are splitted
        :param fra_splitting: Flag controls if forest area type is splitted according to FRA method
        :return: DataFrame with country-specific weights
        """
        fra_data = self.fra_data[["regions", "iso3", "forest_area_2020", "land_area_2020", "primary_forest_area_2010",
                                  "primary_forest_area_2015", "primary_forest_area_2020"]]
        geo_data = self.region_key_timba

        cge_region = f"{self.linked_CGE}_{self.project}"

        geo_data = geo_data[geo_data["GFPM_CountryCode"] != "--"].reset_index(drop=True)
        forest_weights = geo_data.merge(fra_data, left_on="ISO-Code", right_on="iso3", how="left")

        forest_weights[["forest_area_2020", "land_area_2020"]] = (
            forest_weights[["forest_area_2020", "land_area_2020"]].fillna(0))

        forest_data_agg = forest_weights.groupby([cge_region]
                                                 )["forest_area_2020"].sum(numeric_only=True).reset_index()
        forest_weights["forest_area_cge_2020"] = pd.Series(dtype="float64")

        for region in forest_data_agg[cge_region].unique():
            region_index = forest_weights[forest_weights[cge_region] == region].index
            region_forest_data = float(forest_data_agg[forest_data_agg[cge_region] == region]["forest_area_2020"])
            forest_weights.loc[region_index, "forest_area_cge_2020"] = region_forest_data

        forest_weights["forest_weights"] = (forest_weights["forest_area_2020"] /
                                            forest_weights["forest_area_cge_2020"])

        if split_forest_type:
            iso_nan = forest_weights[forest_weights["primary_forest_area_2020"].isna()].copy()
            iso_no_nan = forest_weights[forest_weights["primary_forest_area_2020"].notna()].copy()
            iso_no_nan["unmanaged_forest_share"] = (iso_no_nan["primary_forest_area_2020"] /
                                                    iso_no_nan["forest_area_2020"])
            if fra_splitting:
                primary_forest_region = forest_weights.groupby(
                    ["regions"])[["forest_area_2020", "primary_forest_area_2020"]].sum().reset_index()
            else:
                primary_forest_region = iso_no_nan.groupby(
                    ["regions"])[["forest_area_2020", "primary_forest_area_2020"]].sum().reset_index()

            primary_forest_region["unmanaged_forest_share"] = (primary_forest_region["primary_forest_area_2020"] /
                                                               primary_forest_region["forest_area_2020"])
            iso_nan["unmanaged_forest_share"] = 0
            for region in primary_forest_region["regions"].unique():
                region_index = iso_nan[iso_nan["regions"] == region].index
                primary_forest_share = float(
                    primary_forest_region[primary_forest_region["regions"] == region]["unmanaged_forest_share"])
                iso_nan.loc[region_index, "unmanaged_forest_share"] = primary_forest_share

            forest_weights = pd.concat([iso_nan, iso_no_nan], axis=0).sort_values(by=['GFPM_CountryCode'])
            forest_weights["managed_forest_share"] = 1 - forest_weights["unmanaged_forest_share"]

            forest_weights = forest_weights[["GFPM_CountryCode", cge_region, "forest_weights", "managed_forest_share"]]

        else:
            forest_weights = forest_weights[["GFPM_CountryCode", cge_region, "forest_weights"]]

        return forest_weights

    def disagg_gdp(self):
        """
        Disaggregate CGE data for GDP using calculated GDP weights based on Worldbank data. Converting GDP data from
        BillionUSD to USD. Disaggregation assume that country-specific weights are not changing over the projection
        period.
        :return: Disaggregated CGE data for GDP
        """
        self.Logger.info(f'Disaggregate {self.linked_CGE} of GDP using calculated GDP weights for {self.project}.')

        cge_gdp_data = self.cge_data['gdp']
        disagg_gdp_data = self.worldbank_gdp_weights.merge(cge_gdp_data, left_on=f'{self.linked_CGE}_{self.project}',
                                                           right_on='Region', how='left')
        disagg_gdp_data_fin = disagg_gdp_data[['Country Name', 'ISO-Code', 'GFPM_CountryCode', 'OECD_Ccodes',
                                               f'{self.linked_CGE}_{self.project}']]
        year_list = list(range(self.start_year, self.end_year + 1))
        for year in year_list:
            temp_disagg_gdp = pd.DataFrame(disagg_gdp_data[year] * disagg_gdp_data['gdp_weights'] * 1000000000
                                           ).rename(columns={0: year})
            disagg_gdp_data_fin = pd.concat([disagg_gdp_data_fin, temp_disagg_gdp], axis=1)

        return disagg_gdp_data_fin

    def disagg_pop(self):
        """
        Disaggregate CGE data for Population using calculated Population weights based on Worldbank data. Converting
        Population data from Mio to unit. Disaggregation assume that country-specific weights are not changing over the
        projection period.
        :return: Disaggregated CGE data for Population
        """
        self.Logger.info(f'Disaggregate {self.linked_CGE} of GDP using calculated GDP weights for {self.project}.')

        cge_pop_data = self.cge_data['pop']
        disagg_pop_data = self.worldbank_pop_weights.merge(cge_pop_data, left_on=f'{self.linked_CGE}_{self.project}',
                                                           right_on='Region', how='left')
        disagg_pop_data_fin = disagg_pop_data[['Country Name', 'ISO-Code', 'GFPM_CountryCode', 'OECD_Ccodes',
                                               f'{self.linked_CGE}_{self.project}']]

        year_list = list(range(self.start_year, self.end_year + 1))
        for year in year_list:
            temp_disagg_pop = pd.DataFrame(disagg_pop_data[year] * disagg_pop_data['pop_weights'] * 1000000
                                           ).rename(columns={0: year})
            disagg_pop_data_fin = pd.concat([disagg_pop_data_fin, temp_disagg_pop], axis=1)

        return disagg_pop_data_fin

    def disagg_forest(self, split_forest_type: bool):
        """
        Disaggregates forestland projections from linked GCE to the geographical aggregation of TiMBA. This calculation
        assumes that the distribution of forestland across countries of each geographical aggregate from the CGE will
        not change.
        :param split_forest_type: Flag controls if forest area type (managed and unmanaged forest) are splitted
        :return: Disaggregated forestland projections
        """
        cge_forest_data = self.cge_forest_data
        forest_weights = self.forest_weights

        disagg_forest_data = forest_weights.merge(cge_forest_data, left_on=f"{self.linked_CGE}_{self.project}",
                                                  right_on="region", how="left")
        if split_forest_type:
            disagg_forest_data["disagg_forestland_change"] = (disagg_forest_data["managed_forest_share"] *
                                                              disagg_forest_data["forestland_change"])
        else:
            disagg_forest_data["disagg_forestland_change"] = disagg_forest_data["forestland_change"]

        return disagg_forest_data

    def align_forest_data(self, linkage_type: str):
        """
        Alignes disaggregated forest data with the structure of the exogenous change sheet of pkl or xlsx scenario input
        files
        :param linkage_type: Defines if the linkage is continuous (= for all periods) or end-point (= for end period).
        """
        forest_data = self.disagg_forest_data
        forest_data_new = pd.DataFrame()
        period_data_timba = self.exogenous_change_structure
        period_data_cge = self.exogenous_change_structure_cge

        if len(period_data_timba) > len(period_data_cge):  # selects the smallest period structure to align with
            period_structure = period_data_cge
        else:
            period_structure = period_data_timba

        cge_max_period = period_data_cge[list(period_data_cge.keys())[-1]]
        cge_max_period = cge_max_period[0] + cge_max_period[1]

        if linkage_type == "continuous":
            for period in period_structure:

                period_timba_tmp = period_data_timba[period]
                period_cge_tmp = period_data_cge[period]

                period_year_timba = period_timba_tmp[0]
                period_length_timba = period_timba_tmp[1]

                if period_timba_tmp == period_cge_tmp:
                    forest_data_tmp = forest_data[forest_data["year"] == period_year_timba + period_length_timba].copy()
                    forest_data_tmp["year"] = period_year_timba
                    forest_data_new = pd.concat([forest_data_new, forest_data_tmp], axis=0).reset_index(drop=True)
                else:
                    period_year_cge = period_cge_tmp[0]
                    period_length_cge = period_cge_tmp[1]
                    forest_data_tmp = forest_data[forest_data["year"] == period_year_cge + period_length_cge].copy()
                    forest_data_tmp["disagg_forestland_change"] = (forest_data_tmp["disagg_forestland_change"] /
                                                                   period_length_cge)
                    for year in range(period_year_cge, period_year_cge + period_length_cge):
                        forest_data_tmp["year"] = year
                        forest_data_new = pd.concat([forest_data_new, forest_data_tmp], axis=0).reset_index(drop=True)

        if linkage_type == "end_point":
            for period in period_data_timba:
                period_timba_tmp = period_data_timba[period]
                period_year_timba = period_timba_tmp[0]

                if period_year_timba < cge_max_period:
                    forest_data_tmp = forest_data.copy()
                else:
                    forest_data_tmp = forest_data.copy()
                    forest_data_tmp["disagg_forestland_change"] = -1  # Endogenous forest area growth rate
                forest_data_tmp["year"] = period_year_timba
                forest_data_new = pd.concat([forest_data_new, forest_data_tmp], axis=0).reset_index(drop=True)

        return forest_data_new

    def update_world_forest(self, updated_file):
        """
        Saves updated scenario input file for TiMBA in pkl or xlsx format
        :param updated_file: Selected file format
        """
        time_stamp = dt.datetime.now().strftime("%Y%m%d")
        if updated_file == "pkl":
            import pickle
            import gzip
            target_filepath = os.path.join(OUTPUT_PATH, f"{time_stamp}_updated_{self.input_world}.pkl")
            with gzip.open(target_filepath, "wb") as pkl_file:
                pickle.dump(self.timba_input, pkl_file)
        else:  # for xlsx scenario input files
            shutil.copy2(src=f'{INPUT_PATH}\\{self.input_world}.xlsx',
                         dst=f'{OUTPUT_PATH}\\{time_stamp}_updated_{self.input_world}.xlsx')

            wb = load_workbook(f'{OUTPUT_PATH}\\{time_stamp}_updated_{self.input_world}.xlsx')
            if 'ExogChange' in wb.sheetnames:
                wb.remove(wb['ExogChange'])

            wb.save(f'{OUTPUT_PATH}\\{time_stamp}_updated_{self.input_world}.xlsx')

            self.Logger.info(f'Save updated worlds')

            with pd.ExcelWriter(f'{OUTPUT_PATH}\\{time_stamp}_updated_{self.input_world}.xlsx', engine="openpyxl",
                                mode="a", if_sheet_exists='replace') as writer:

                self.timba_input.to_excel(writer, sheet_name="ExogChange", index=False)


    def calc_gdp_per_capita(self):
        """
        Calculate GDP per capita with disaggregated projected GDP data from CGE and Population data from OECD (not
        changing in the CGE projections).
        :return: Calculated data for GDP per capita
        """
        self.Logger.info(f'Calculate GDP per capita using disaggregated data of GDP from '
                         f'{self.linked_CGE}_{self.project} and data of Pop from OECD.')
        gdp_per_capita = self.disagg_gdp_data[['Country Name', 'ISO-Code', 'GFPM_CountryCode', 'OECD_Ccodes',
                                          f'{self.linked_CGE}_{self.project}']]
        year_list = list(range(self.start_year, self.end_year + 1))
        for year in year_list:
            temp_gdp_per_capita = self.disagg_gdp_data[year] / self.disagg_pop_data[year]
            gdp_per_capita = pd.concat([gdp_per_capita, temp_gdp_per_capita], axis=1)

        return gdp_per_capita

    def calc_growth_rate(self, target_parameter: pd.DataFrame, link_typ: str):
        """
        Calculate annual growth rate of economic variables (GDP and GDP per capita) projected by linked CGE and
        disaggregated to TiMBA country level
        :param target_parameter: Parameter for which growth rates will be calculated
        :param link_typ: Type of linkage used in model linkage. If "continous" is chosen, growth rates for each period
        are calculated for the exchanged variable. If "end_point" is chosen, growth rates between the first and the last
        period are calculated.
        :return: Calculated growth rate
        """
        self.Logger.info(f'Calculate growth rate for {target_parameter}.')
        growth_rate = target_parameter[['Country Name', 'ISO-Code', 'GFPM_CountryCode', 'OECD_Ccodes',
                                        f'{self.linked_CGE}_{self.project}', self.start_year]]

        year_period_min = self.start_year
        if link_typ == 'continous':
            for key in self.exogenous_change_structure.keys():
                year_period_max = year_period_min + self.exogenous_change_structure[key][1]
                periodic_growth_rate = pd.DataFrame((target_parameter[year_period_max] - target_parameter[year_period_min])
                                                    / target_parameter[year_period_min]
                                                    ).rename(columns={0: f"{year_period_max}"})
                annual_growth_rate = (1 + periodic_growth_rate) ** (1 / self.exogenous_change_structure[key][1]) - 1
                growth_rate = pd.concat([growth_rate, annual_growth_rate], axis=1)
                year_period_min = year_period_max
        if link_typ == 'end_point':
            proj_length = []
            year_period_tmp = year_period_min.copy()
            for key in self.exogenous_change_structure.keys():
                proj_length.append(self.exogenous_change_structure[key][1])
                year_period_max = year_period_tmp + self.exogenous_change_structure[key][1]
                year_period_tmp = year_period_max

            periodic_growth_rate = pd.DataFrame((target_parameter[year_period_max] - target_parameter[year_period_min])
                                                / target_parameter[year_period_min]
                                                ).rename(columns={0: f"{year_period_max}"})
            annual_growth_rate = (1 + periodic_growth_rate) ** (1 / (year_period_max - year_period_min)) - 1

            for key in self.exogenous_change_structure.keys():
                year_period_tmp = year_period_min + self.exogenous_change_structure[key][1]
                annual_growth_rate_tmp = pd.DataFrame(annual_growth_rate).rename(
                    columns={f"{year_period_max}": f"{year_period_tmp}"})
                growth_rate = pd.concat([growth_rate, annual_growth_rate_tmp], axis=1)
                year_period_min = year_period_tmp

        return growth_rate


    def reformate_growth_rate(self, growth_rate_to_reformate, year):
        reformated_growth_rate = self.region_key_timba.merge(
            growth_rate_to_reformate[['GFPM_CountryCode', f'{year}']],
            left_on='GFPM_CountryCode',
            right_on='GFPM_CountryCode', how='left')
        reformated_growth_rate = reformated_growth_rate[['GFPM_CountryCode', f'{year}']].fillna(0)
        reformated_growth_rate = reformated_growth_rate[
            reformated_growth_rate['GFPM_CountryCode'] != '--'].reset_index(drop=True)

        return reformated_growth_rate

    def update_exogChange(self, updated_domains, updated_file):
        """
        Updates exogChange-sheet in specified World-file for TiMBA with data from linked model
        :param updated_domains: Updated domains with exogen data with following options available:
            - "gdp": New annual growth rates for GDP (for demand "D" and supply "S")
            - "gdp_cap": New annual growth rates for GDP per capita (for forest "F")
            - "forest_area": New growth rates for forest area (for forest "F")
        :param updated_file: TiMBA input file which will be updated ("xlsx" or "pkl")  # TODO implement pkl
        Updated exogChange is saved as a pd.DataFrame
        """
        self.Logger.info(f"Update World-file (ExogChange-sheet) with disaggregate Data.")
        if "gdp" in updated_domains:
            self.Logger.info(
                f"Update World-file (ExogChange-sheet) with disaggregate GDP data from {self.linked_CGE}.")
        if "gdp_cap" in updated_domains:
            self.Logger.info(
                f"Update World-file (ExogChange-sheet) with disaggregate GDPpc data from {self.linked_CGE}.")
        if "forest_area" in updated_domains:
            self.Logger.info(
                f"Update World-file (ExogChange-sheet) with disaggregate forest data from {self.linked_CGE}.")

        world_to_update = pd.ExcelFile(f'{INPUT_PATH}\\{self.input_world}.xlsx')
        new_ExogChange = world_to_update.parse('ExogChange')
        filter_col = new_ExogChange.columns[0]
        slicing_index = new_ExogChange[new_ExogChange[filter_col] == "="].index[1] + 1
        ExogChange_description = new_ExogChange.iloc[:slicing_index]
        ExogChange_data = new_ExogChange.iloc[slicing_index:].reset_index(drop=True)
        period_index = ExogChange_data[ExogChange_data[filter_col].str.contains('PERIOD')].index  # [0:4]
        period_data_length = (period_index[1] - period_index[0]) - 1

        ExoChange_data_updated = pd.DataFrame()

        year = self.start_year
        for index, key in zip(period_index, self.exogenous_change_structure):
            period_length = self.exogenous_change_structure[key][1]
            year = year + period_length
            temp_ExogChange = ExogChange_data.loc[index:index + period_data_length]

            exogChange_demand = temp_ExogChange[temp_ExogChange[filter_col] == 'D']
            exogChange_supply = temp_ExogChange[(temp_ExogChange[filter_col] == 'S') &
                                                (temp_ExogChange['Unnamed: 9'] != -1)]
            exogChange_forest = temp_ExogChange[temp_ExogChange[filter_col] == 'F']

            index_demand = exogChange_demand.index
            index_supply = exogChange_supply.index
            index_forest = exogChange_forest.index

            if "gdp" in updated_domains:
                reformated_growth_rate_gdp = self.reformate_growth_rate(growth_rate_to_reformate=self.growth_rate_gdp,
                                                                        year=year)

                reformated_growth_rate_gdp_demand = exogChange_demand.merge(reformated_growth_rate_gdp,
                                                                            left_on='Unnamed: 1',
                                                                            right_on='GFPM_CountryCode',
                                                                            how='left')

                reformated_growth_rate_gdp_supply = exogChange_supply.merge(reformated_growth_rate_gdp,
                                                                            left_on='Unnamed: 1',
                                                                            right_on='GFPM_CountryCode',
                                                                            how='left')
                temp_ExogChange.loc[index_demand, 'Unnamed: 9'] = reformated_growth_rate_gdp_demand.set_index(
                    index_demand)[f'{year}']
                temp_ExogChange.loc[index_supply, 'Unnamed: 9'] = reformated_growth_rate_gdp_supply.set_index(
                    index_supply)[f'{year}']

            if "gdp_cap" in updated_domains:
                reformated_growth_rate_gdp_cap = self.reformate_growth_rate(
                    growth_rate_to_reformate=self.growth_rate_gdp_cap,
                    year=year)
                temp_ExogChange.loc[index_forest, 'Unnamed: 9'] = reformated_growth_rate_gdp_cap.set_index(
                    index_forest)[f'{year}']

            if "forest_area" in updated_domains:
                year_forest = year - period_length
                # year_forest is a workaround caused by the different calculations of growth for gdp and forest area
                # Todo Adapt forest_area calculation
                temp_forest_data = self.disagg_forest_data[
                    self.disagg_forest_data["year"] == year_forest].reset_index(drop=True).copy()
                temp_ExogChange.loc[index_forest, "Unnamed: 8"] = temp_forest_data.set_index(
                    index_forest)["disagg_forestland_change"]

            ExoChange_data_updated = pd.concat([ExoChange_data_updated, temp_ExogChange], axis=0)

        new_ExogChange = pd.concat([ExogChange_description, ExoChange_data_updated], axis=0).reset_index(drop=True)

        return new_ExogChange

    def update_world(self):
        self.Logger.info(f'Update {self.project} World with new ExogChange')
        time_stamp = dt.datetime.now().strftime("%Y%m%d")

        separator = '_'
        updated_world_name = self.input_world.split(separator)[1:]
        updated_world_name = f'{time_stamp}_Updated_{separator.join(updated_world_name)}'

        shutil.copy2(src=f'{INPUT_PATH}\\{self.input_world}.xlsx',
                     dst=f'{OUTPUT_PATH}\\{updated_world_name}.xlsx')

        wb = load_workbook(f'{OUTPUT_PATH}\\{updated_world_name}.xlsx')
        if 'ExogChange' in wb.sheetnames:
            wb.remove(wb['ExogChange'])
        wb.save(f'{OUTPUT_PATH}\\{updated_world_name}.xlsx')

        self.Logger.info(f'Save updated world')

        with pd.ExcelWriter(f'{OUTPUT_PATH}\\{updated_world_name}.xlsx', engine='openpyxl',
                            mode='a', if_sheet_exists='replace') as writer:
            self.new_exogChange.to_excel(writer, sheet_name='ExogChange', index=False)

    def gdp_disaggregation_pipeline(self):
        """
        Pipeline disaggregating GDP and Population data from the linked CGE model using country-specific weights based
        on World Bank data.
        """

        self.worldbank_gdp_weights = self.calc_worldbank_gdp_weights()
        self.worldbank_pop_weights = self.calc_worldbank_pop_weights()

        self.disagg_gdp_data = self.disagg_gdp()
        self.disagg_pop_data = self.disagg_pop()

        self.disagg_gdp_cap_data = self.calc_gdp_per_capita()

        self.growth_rate_gdp = self.calc_growth_rate(
            target_parameter=self.disagg_gdp_data, link_typ=self.link_typ)
        self.growth_rate_gdp_cap = self.calc_growth_rate(
            target_parameter=self.disagg_gdp_cap_data, link_typ=self.link_typ)

    def forest_disaggregation_pipeline(self, split_forest_type, fra_splitting):
        """
        Pipeline disaggregating forest data from the linked CGE model using country-specific weights based on FRA
        :param split_forest_type: Flag controls if forest area type (managed and unmanaged forest) are splitted
        :param fra_splitting: Flag controls if forest area type is splitted according to FRA method
        data.
        """
        self.cge_forest_data = self.process_cge_forest_data(linkage_type=self.link_typ)
        self.forest_weights = self.calc_forest_weights(split_forest_type=split_forest_type,
                                                       fra_splitting=fra_splitting)
        self.disagg_forest_data = self.disagg_forest(split_forest_type=split_forest_type)
        self.disagg_forest_data = self.align_forest_data(linkage_type=self.link_typ)

    def main_disaggregation_pipeline(self, input_timba, input_sc_file, input_gdp_CGE, input_forest_CGE, linked_var,
                                     updated_file):
        """
        Main disaggregation pipeline scaling down geographical regions of the linked CGE to TiMBA's spatial resolution
        using country-specific weights calculated based on world bank data (for GDP and GDP per capita) and forest
        resource assessment data (for forest area).
        :param input_timba: TiMBA output file containing modelling results
        :param input_sc_file: TiMBA input file to be updated with CGE data
        :param input_gdp_CGE: GDP data of linked CGE
        :param input_forest_CGE: Forest data of linked CGE
        :param linked_var: Linked variables from the CGE
        :param updated_file: File format that is updated

        """
        Pipeline_Disagg = DisaggregateCGEResults(
            current_scenario=self.current_scenario,
            input_path_timba=input_timba,
            input_gdp_CGE=input_gdp_CGE,
            input_world=input_sc_file,
            input_forest_CGE=input_forest_CGE,
            link_typ=self.link_typ,
            linked_CGE=self.linked_CGE,
            linked_var=linked_var,
            project=self.project,
            updated_file=updated_file
        )

        DisaggregateCGEResults.readin_help_data(Pipeline_Disagg)

        if ('gdp' in linked_var) or ('gdp_cap' in linked_var):
            Pipeline_Disagg.gdp_disaggregation_pipeline()

        if 'forest_area' in linked_var:
            Pipeline_Disagg.forest_disaggregation_pipeline(split_forest_type=False,
                                                           fra_splitting=False)

        if ('gdp' not in linked_var) or ('gdp_cap' not in linked_var) or ('forest_area' not in linked_var):
            Pipeline_Disagg.Logger.info(f'Disaggregation for {self.linked_CGE} is yet not implemented.')

        Pipeline_Disagg.new_exogChange = Pipeline_Disagg.update_exogChange(updated_domains=linked_var,
                                                                           updated_file=updated_file)
        Pipeline_Disagg.update_world()

        Pipeline_Disagg.Logger.info(f'This link is unbreakable.')
