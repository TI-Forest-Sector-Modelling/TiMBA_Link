# imports
import pandas as pd
import numpy as np
import pickle
import gzip
import shutil
import os
from linking_pipeline.parameters.paths import (CGE_INPUT_PATH, TIMBA_INPUT_PATH, TIMBA_INPUT_BLANK_PATH,
                                               DISAGGREGATION_OUTPUT_PATH, INPUT_POP_DART_BIO, INPUT_POP_MAGNET,
                                               COUNTRY_CONCORDANCE_TIMBA, COUNTRY_CONCORDANCE_WB_OECD,
                                               INPUT_GDP_WORLD_BANK, INPUT_GDP_OECD, INPUT_FRA)
from linking_pipeline.parameters.REGEX_patterns import PERIOD_PATTERN
from openpyxl import load_workbook
import datetime as dt
from linking_pipeline.helper_functions.base_logger import get_logger
from linking_pipeline.parameters.defines import Constants, ProductStructures, VarNames
from linking_pipeline.parameters.default_parameters import disaggregation_parameters


class DisaggregateCGEResults(object):
    def __init__(self,
                 current_scenario: str,
                 input_gdp_CGE: str,
                 input_world: str,
                 input_forest_CGE: str,
                 link_typ: str,
                 linked_CGE: str,
                 linked_var: list,
                 project: str,
                 updated_file: str,
                 detailed_logger: bool,
                 iter_num: int,
                 ):
        DisaggregateCGEResults.header_disaggregation(self, detailed_logger=detailed_logger)
        self.Logger = get_logger(user_path=None, aggregation_flag=True)
        self.current_scenario = current_scenario
        self.current_dt = dt.datetime.now().strftime("%Y%m%d")
        self.input_gdp_CGE = input_gdp_CGE
        self.input_world = input_world
        self.input_forest_CGE = input_forest_CGE
        self.link_typ = link_typ
        self.linked_CGE = linked_CGE
        self.linked_var = linked_var
        self.project = project
        self.updated_file = updated_file
        self.iter_num = iter_num

        self.region_key = None
        self.region_key_timba = None
        self.commodity_key = None
        self.oecd_data = None
        self.worldbank_data = None
        self.fra_data = None
        self.cge_forest_data = None
        self.exogenous_change_structure = None
        self.exogchange_description = None
        self.exogchange_data = None
        self.commodity_num = None
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
        self.growth_rate_forest = None
        self.new_exogChange = None
        self.cge_data = DisaggregateCGEResults.readin_model_data(self, updated_file)

    def header_disaggregation(self, detailed_logger):
        """
        Header of disaggregation pipeline
        :param detailed_logger: Flag controling if parameter details are provided
        """
        print("\n")
        print("===============================")
        print("=== Disaggregation-Pipeline ===")
        print("===============================")
        if detailed_logger:
            print("========= Parameters =========")
            print("==============================")
            print(f"Disaggregated Domains:{disaggregation_parameters[VarNames.LINKED_VAR.value]}")
            print("==============================")
        print("\n")

    def readin_model_data(self, updated_file):
        """
        Read in projection data from CGE for disaggregation. Processed data are specific to the linked CGE and the
        project. Add specific if-statements in the following to account for project specific TiMBA-CGE-linkages.
        :param updated_file: File format that has been chosen to be updated
        :return: Project and CGE model specific return (see in function for details)
        """
        self.Logger.info(f'Read in TiMBA input to update {self.input_world}.')
        world_to_update_path = TIMBA_INPUT_BLANK_PATH / f'{self.input_world}.{updated_file}'

        if updated_file == "xlsx":
            world_to_update = pd.ExcelFile(world_to_update_path)
            new_ExogChange = world_to_update.parse('ExogChange')
            Specification_data = world_to_update.parse('Specification')
            filter_col = new_ExogChange.columns[0]
            slicing_index = new_ExogChange[new_ExogChange[filter_col] == "="].index[1] + 1
            ExogChange_description = new_ExogChange.iloc[:slicing_index]
            ExogChange_data = new_ExogChange.iloc[slicing_index:].reset_index(drop=True)
        else:
            # TODO not implemented yet
            try:
                with open(world_to_update_path, "rb") as pkl_file:
                    world_to_update = pickle.load(pkl_file)
            except pickle.UnpicklingError:
                with gzip.open(world_to_update_path, "rb") as pkl_file:
                    world_to_update = pickle.load(pkl_file)

        self.start_year = DisaggregateCGEResults.retrieve_start_year(self, data=Specification_data)
        self.exogenous_change_structure = DisaggregateCGEResults.retrieve_period_structure(self, data=ExogChange_data)
        self.commodity_num = DisaggregateCGEResults.retrieve_commodity_num(self, data=Specification_data)

        self.exogchange_description = ExogChange_description
        self.exogchange_data = ExogChange_data


        cge_data = {}
        if ('gdp' in self.linked_var) or ('gdp_cap' in self.linked_var):
            self.Logger.info(f'Read in {self.input_gdp_CGE} for GDP.')
            cge_gdp_data = pd.read_csv(CGE_INPUT_PATH / f'{self.input_gdp_CGE}.csv')
            if len(cge_gdp_data.columns) == 1:
                cge_gdp_data = pd.read_csv(CGE_INPUT_PATH / f'{self.input_gdp_CGE}.csv', delimiter=';')
            cge_gdp_data.columns = DisaggregateCGEResults.convert_year_col_to_int(self, data=cge_gdp_data)
            cge_gdp_data = DisaggregateCGEResults.interpolate_cge_data_missing_years(self,
                                                                                     data=cge_gdp_data,
                                                                                     growth_rate="exponential")

            cge_data['gdp'] = cge_gdp_data.dropna()
            self.Logger.info(f'Read in constant POP data from {self.linked_CGE}.')
            if self.linked_CGE == "DART-BIO":
                pop_data_path = INPUT_POP_DART_BIO
            if self.linked_CGE == "MAGNET":
                pop_data_path = INPUT_POP_MAGNET

            cge_pop_data = pd.read_csv(f'{pop_data_path}', sep=";")
            if len(cge_pop_data) == 1:
                cge_pop_data = pd.read_csv(f'{pop_data_path}', sep=",")
            cge_pop_data.columns = DisaggregateCGEResults.convert_year_col_to_int(self, data=cge_pop_data)
            cge_pop_data = DisaggregateCGEResults.interpolate_cge_data_missing_years(self,
                                                                                     data=cge_pop_data,
                                                                                     growth_rate="linear")
            cge_data['pop'] = cge_pop_data.dropna()

        if 'forest_area' in self.linked_var:
            cge_forest_data = pd.read_csv(CGE_INPUT_PATH / f'{self.input_forest_CGE}.csv', delimiter=';')
            cge_forest_data.columns = DisaggregateCGEResults.convert_year_col_to_int(self, cge_forest_data)
            cge_forest_data = DisaggregateCGEResults.interpolate_cge_data_missing_years(self,
                                                                                        data=cge_forest_data,
                                                                                        growth_rate="linear")
            cge_data['forest_area'] = cge_forest_data.dropna()

        return cge_data

    def readin_help_data(self):
        """
        Read in help data to disaggregate CGE data to product- and country-structure of TiMBA.
        :return: Project and CGE model specific return (see in function for details)
        """
        self.Logger.info(f"Read in help data.")
        if self.commodity_num == 14:
            commodity_key = pd.DataFrame.from_dict(ProductStructures.com_info_14.value)
        if self.commodity_num == 16:
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
            years_for_average = list(range(self.start_year - 1, self.start_year + 2))  # 3-years average
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
            fra_forest_data = pd.read_csv(f"{INPUT_FRA}")
            self.fra_data = fra_forest_data

        self.commodity_key = commodity_key
        self.region_key_timba = region_key_timba

    def retrieve_period_structure(self, data):
        """
        Retrieves Period Nr and Year from ExogChange and adds to ExogChange.
        :param data:  DataContainer to be filled with data from Excel
        """
        start_year = self.start_year
        data_period = pd.DataFrame()
        data_period.loc[0, 'Period'] = int(0)
        data_period.loc[0, 'year'] =  int(start_year)
        regex_res = data.iloc[:, 0].apply(
            lambda x: PERIOD_PATTERN.findall(x)[0] if PERIOD_PATTERN.findall(x) else None).dropna()
        year_runner = start_year
        for i, (idx, (period, forcast_years)) in enumerate(regex_res.items()):
            i += 1
            year_runner += int(forcast_years)
            data_period.loc[i, 'Period'] = int(period)
            data_period.loc[i, 'year'] = year_runner

        self.end_year = int(data_period['year'][max(data_period.index)])

        exogenous_change_structure = {}
        year_prev = data_period['year'][0]
        for period in data_period['Period'][1:]:
            index = data_period[data_period['Period'] == period]['year'].index[0]
            year = data_period[data_period['Period'] == period]['year'][index]
            period_len = year - year_prev
            exogenous_change_structure[f'Period_{period}'] = [year_prev, period_len]
            year_prev = year

        return exogenous_change_structure

    def retrieve_start_year(self, data):
        """
        Retrieves the start year for TiMBA projections from input data
        :param data: Specification data from TiMBA
        :return: Start year for TiMBA projections
        """
        start_year = int(data["Property Value"][0])

        return start_year

    def retrieve_commodity_num(self, data):
        """
        Retrieves the number of commodities used in the TiMBA projections from input data
        :param data: Specification data from TiMBA
        :return: Number of commodities used in the TiMBA projections
        """
        commodity_num = len(data["Commodity Code"].dropna())

        return commodity_num


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

    def calc_worldbank_gdp_weights(self):
        """
        Calculates GDP weights based on 3-years average of GDP data from Worldbank to disaggregate CGE data of GDP to
        country level of TiMBA. Disaggregation of GDP data assumes that GDP shares of countries in each CGE region is
        not changing over the projection period.
        :return: GDP weights for each country in each regions of the linked CGE model.
        """
        self.Logger.info(f'Calculate GDP-weights using Worldbank GDP-data to disaggregate '
                         f'{self.linked_CGE}_{self.project} data')

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
        self.Logger.info(f'Calculate POP-weights using Worldbank population data to disaggregate '
                         f'{self.linked_CGE}_{self.project} data')

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

            forest_weights = forest_weights[['ISO-Code', "GFPM_CountryCode", cge_region, "forest_weights",
                                             "managed_forest_share"]]

        else:
            forest_weights = forest_weights[['ISO-Code', "GFPM_CountryCode", cge_region, "forest_weights"]]

        return forest_weights

    def disagg_gdp(self):
        """
        Disaggregate CGE data for GDP using calculated GDP weights based on Worldbank data. Converting GDP data from
        BillionUSD to USD. Disaggregation assume that country-specific weights are not changing over the projection
        period.
        :return: Disaggregated CGE data for GDP
        """
        self.Logger.info(f'Disaggregate GDP from {self.linked_CGE}_{self.project} using calculated GDP weights.')

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
        self.Logger.info(f'Disaggregate POP from {self.linked_CGE}_{self.project} using calculated POP weights.')

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
        self.Logger.info(f'Disaggregate FOREST AREA from {self.linked_CGE}_{self.project} using calculated FOREST AREA weights.')
        cge_forest_data = self.cge_data['forest_area']
        forest_weights = self.forest_weights

        disagg_forest_data = forest_weights.merge(cge_forest_data, left_on=f"{self.linked_CGE}_{self.project}",
                                                  right_on="Region", how="left")
        disagg_forest_data_fin = disagg_forest_data[['GFPM_CountryCode', f'{self.linked_CGE}_{self.project}']]

        year_list = list(range(self.start_year, self.end_year + 1))
        for year in year_list:
            if split_forest_type:
                temp_disagg_forest = pd.DataFrame(disagg_forest_data[year] * disagg_forest_data['forest_weights'] *
                                                  disagg_forest_data['managed_forest_share']).rename(columns={0: year})
            else:
                temp_disagg_forest = pd.DataFrame(disagg_forest_data[year] * disagg_forest_data['forest_weights']
                                                  ).rename(columns={0: year})

            disagg_forest_data_fin = pd.concat([disagg_forest_data_fin, temp_disagg_forest], axis=1)

        return disagg_forest_data

    def calc_gdp_per_capita(self):
        """
        Calculate GDP per capita with disaggregated projected GDP data from CGE and Population data from OECD (not
        changing in the CGE projections).
        :return: Calculated data for GDP per capita
        """
        self.Logger.info(f'Calculate GDP per capita using disaggregated data of dynamic GDP and constant POP data from '
                         f'{self.linked_CGE}_{self.project}.')
        gdp_per_capita = self.disagg_gdp_data[['Country Name', 'ISO-Code', 'GFPM_CountryCode', 'OECD_Ccodes',
                                               f'{self.linked_CGE}_{self.project}']]
        gpd_data = self.disagg_gdp_data.copy()
        pop_data = self.disagg_pop_data.copy()

        year_list = list(range(self.start_year, self.end_year + 1))
        for year in year_list:
            temp_gdp_per_capita = self.disagg_gdp_data[year] / self.disagg_pop_data[year]
            gdp_per_capita = pd.concat([gdp_per_capita, temp_gdp_per_capita], axis=1)

        return gdp_per_capita

    def calc_growth_rate(self, parameter_name: str, target_parameter: pd.DataFrame, link_typ: str):
        """
        Calculate annual growth rate of economic (GDP and GDP per capita) or land use variables (Forest area) projected
        by linked CGE and disaggregated to TiMBA country level
        :param parameter_name: Name of parameter
        :param target_parameter: Parameter for which growth rates will be calculated
        :param link_typ: Type of linkage used in model linkage. If "continous" is chosen, growth rates for each period
        are calculated for the exchanged variable. If "end_point" is chosen, growth rates between the first and the last
        period are calculated.
        :return: Calculated growth rate
        """
        self.Logger.info(f'Calculate growth rate for {parameter_name} from {self.linked_CGE}_{self.project}.')
        if ('GDP' in parameter_name) or ('GDPcap' in parameter_name):
            growth_rate = target_parameter[['Country Name', 'ISO-Code', 'GFPM_CountryCode', 'OECD_Ccodes',
                                            f'{self.linked_CGE}_{self.project}', self.start_year]]
        if 'FOREST_AREA' in parameter_name:
            growth_rate = target_parameter[['ISO-Code', 'GFPM_CountryCode', f'{self.linked_CGE}_{self.project}',
                                            self.start_year]]

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
            year_period_tmp = year_period_min
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
        self.Logger.info(f"Update {self.input_world}:")
        if "gdp" in updated_domains:
            self.Logger.info(
                f"  --> Update World-file (ExogChange-sheet) with disaggregate GDP data from"
                f" {self.linked_CGE}_{self.project}.")
        if "gdp_cap" in updated_domains:
            self.Logger.info(
                f"  --> Update World-file (ExogChange-sheet) with disaggregate GDPpc data from"
                f" {self.linked_CGE}_{self.project}.")
        if "forest_area" in updated_domains:
            self.Logger.info(
                f"  --> Update World-file (ExogChange-sheet) with disaggregate forest data from"
                f" {self.linked_CGE}_{self.project}.")

        ExogChange_description = self.exogchange_description
        filter_col = ExogChange_description.columns[0]
        ExogChange_data = self.exogchange_data
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
                reformated_growth_rate_forest = self.reformate_growth_rate(
                    growth_rate_to_reformate=self.growth_rate_forest,
                    year=year)
                temp_ExogChange.loc[index_forest, 'Unnamed: 8'] = reformated_growth_rate_forest.set_index(
                    index_forest)[f'{year}']

            ExoChange_data_updated = pd.concat([ExoChange_data_updated, temp_ExogChange], axis=0)

        new_ExogChange = pd.concat([ExogChange_description, ExoChange_data_updated], axis=0).reset_index(drop=True)

        return new_ExogChange

    def update_world(self):
        self.Logger.info(f'Update {self.project} World with new ExogChange')
        time_stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")

        separator = '_'
        updated_world_name = self.input_world.split(separator)[1:]
        updated_world_name = f'{time_stamp}_Updated_{separator.join(updated_world_name)}_it{self.iter_num}'

        if not os.path.exists(DISAGGREGATION_OUTPUT_PATH):
            os.makedirs(DISAGGREGATION_OUTPUT_PATH, exist_ok=True)

        shutil.copy2(src=TIMBA_INPUT_BLANK_PATH / f'{self.input_world}.{self.updated_file}',
                     dst=DISAGGREGATION_OUTPUT_PATH / f'{updated_world_name}.{self.updated_file}')

        wb = load_workbook(DISAGGREGATION_OUTPUT_PATH / f'{updated_world_name}.{self.updated_file}')
        if 'ExogChange' in wb.sheetnames:
            wb.remove(wb['ExogChange'])
        wb.save(DISAGGREGATION_OUTPUT_PATH / f'{updated_world_name}.{self.updated_file}')

        self.Logger.info(f'Save updated world')

        with pd.ExcelWriter(DISAGGREGATION_OUTPUT_PATH / f'{updated_world_name}.{self.updated_file}', engine='openpyxl',
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

        self.growth_rate_gdp = self.calc_growth_rate(parameter_name="GDP",
                                                     target_parameter=self.disagg_gdp_data,
                                                     link_typ=self.link_typ)
        self.growth_rate_gdp_cap = self.calc_growth_rate(parameter_name="GDPcap",
                                                         target_parameter=self.disagg_gdp_cap_data,
                                                         link_typ=self.link_typ)

    def forest_disaggregation_pipeline(self, split_forest_type, fra_splitting):
        """
        Pipeline disaggregating forest data from the linked CGE model using country-specific weights based on FRA
        :param split_forest_type: Flag controls if forest area type (managed and unmanaged forest) are splitted
        :param fra_splitting: Flag controls if forest area type is splitted according to FRA method
        data.
        """
        self.forest_weights = self.calc_forest_weights(split_forest_type=split_forest_type,
                                                       fra_splitting=fra_splitting)
        self.disagg_forest_data = self.disagg_forest(split_forest_type=split_forest_type)

        self.growth_rate_forest = self.calc_growth_rate(parameter_name="FOREST_AREA",
                                                        target_parameter=self.disagg_forest_data,
                                                        link_typ=self.link_typ)

    def main_disaggregation_pipeline(self, disaggregation_parameters):
        """
        Main disaggregation pipeline scaling down geographical regions of the linked CGE to TiMBA's spatial resolution
        using country-specific weights calculated based on world bank data (for GDP and GDP per capita) and forest
        resource assessment data (for forest area).
        :param disaggregation_parameters: Dict holding all parameters relevant for the disaggregation pipeline
        """
        Pipeline_Disagg = DisaggregateCGEResults(
            current_scenario=self.current_scenario,
            input_gdp_CGE=disaggregation_parameters[VarNames.INPUT_GDP_CGE.value],
            input_world=disaggregation_parameters[VarNames.INPUT_TIMBA_TO_UPDATE.value],
            input_forest_CGE=disaggregation_parameters[VarNames.INPUT_FOREST_CGE.value],
            link_typ=self.link_typ,
            linked_CGE=self.linked_CGE,
            linked_var=disaggregation_parameters[VarNames.LINKED_VAR.value],
            project=self.project,
            updated_file=disaggregation_parameters[VarNames.UPDATED_FILE.value],
            detailed_logger=self.detailed_logger,
            iter_num=self.iter_num
        )

        DisaggregateCGEResults.readin_help_data(Pipeline_Disagg)

        if ('gdp' in disaggregation_parameters[VarNames.LINKED_VAR.value]) or (
                'gdp_cap' in disaggregation_parameters[VarNames.LINKED_VAR.value]):
            Pipeline_Disagg.gdp_disaggregation_pipeline()

        if 'forest_area' in disaggregation_parameters[VarNames.LINKED_VAR.value]:
            Pipeline_Disagg.forest_disaggregation_pipeline(split_forest_type=False,
                                                           fra_splitting=False)

        if ('gdp' not in disaggregation_parameters[VarNames.LINKED_VAR.value]) or (
                'gdp_cap' not in disaggregation_parameters[VarNames.LINKED_VAR.value]) or (
                'forest_area' not in disaggregation_parameters[VarNames.LINKED_VAR.value]):
            Pipeline_Disagg.Logger.info(f'Disaggregation for {self.linked_CGE} is yet not implemented.')

        Pipeline_Disagg.new_exogChange = Pipeline_Disagg.update_exogChange(
            updated_domains=disaggregation_parameters[VarNames.LINKED_VAR.value],
            updated_file=disaggregation_parameters[VarNames.UPDATED_FILE.value])
        Pipeline_Disagg.update_world()

        Pipeline_Disagg.Logger.info(f'This link is unbreakable.')
