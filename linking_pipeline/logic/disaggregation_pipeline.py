# -----------------------------------------------------
# CGE_linking_pipeline (Tomke Honkomp (TH) - Thuenen-Institut)
# Soft linkage of TiMBA to selected CGE (spatial and sectoral aggregation and disaggregation)
# Projects: BioSDG, CarbonLeak
# -----------------------------------------------------

# imports
import pandas as pd
import numpy as np
import pickle
import gzip
import os
import shutil
from pathlib import Path
from openpyxl import load_workbook
import datetime as dt
from linking_pipeline.helper_functions.base_logger import get_logger
from linking_pipeline.parameters.defines import Constants, ProductStructures


class DisaggregateCGEResults(object):
    def __init__(self,
                 current_scenario: str,
                 input_path_timba: str,
                 input_path_CGE: str,
                 input_world: str,
                 link_typ: str,
                 linked_CGE: str,
                 project: str
                 ):
        self.sfile = os.path.dirname(Path(__file__).resolve().parents[0])
        self.Logger = get_logger(user_path=None, aggregation_flag=True)
        self.current_scenario = current_scenario
        self.current_dt = dt.datetime.now().strftime("%Y%m%d")
        self.input_path_timba = input_path_timba
        self.input_path_CGE = input_path_CGE
        self.input_world = input_world
        self.link_typ = link_typ
        self.linked_CGE = linked_CGE
        self.project = project
        self.cge_data, self.timba_data, self.timba_input = DisaggregateCGEResults.readin_model_data(self)

        self.region_key = None
        self.region_key_timba = None
        self.commodity_key = None
        self.oecd_data = None
        self.worldbank_data = None
        self.fra_data = None
        self.cge_forest_data = None
        self.exogenous_change_structure = None
        self.start_year = None
        self.end_year = None
        self.year_for_avg = None

    def readin_model_data(self):
        """
        Read in projection data from CGE for disaggregation. Processed data are specific to the linked CGE and the
        project. Add specific if-statements in the following to account for project specific TiMBA-CGE-linkages.
        :return: Project and CGE model specific return (see in function for details)
        """
        self.Logger.info(f'Read in TiMBA results {self.input_path_timba}.')
        src_path_1 = f'{self.sfile}\\data\\input\\{self.input_path_timba}.pkl'
        src_path_2 = f'{self.sfile}\\data\\input\\{self.input_world}.pkl'

        try:
            with open(src_path_1, "rb") as pkl_file:
                timba_data = pickle.load(pkl_file)
        except pickle.UnpicklingError:
            with gzip.open(src_path_1, "rb") as pkl_file:
                timba_data = pickle.load(pkl_file)

        try:
            with open(src_path_2, "rb") as pkl_file:
                timba_input = pickle.load(pkl_file)
        except pickle.UnpicklingError:
            with gzip.open(src_path_2, "rb") as pkl_file:
                timba_input = pickle.load(pkl_file)

        cge_data = {}
        if self.linked_CGE == 'DART-BIO':
            # For DART-BIO-TiMBA-linkage GDP and GDPcap projections are disaggregated.
            self.Logger.info(f'Read in {self.linked_CGE}_{self.project} for GDP.')
            dartbio_gdp_data = pd.read_csv(f'{self.sfile}\\data\\input\\{self.input_path_CGE}.csv')
            cge_data['gdp'] = dartbio_gdp_data
            self.Logger.info(f'Read in {self.linked_CGE}_{self.input_path_CGE} for POP.')
            dartbio_pop_data = pd.ExcelFile(f'{self.sfile}\\data\\input\\dartbio_data_pop.xlsx')
            dartbio_pop_data = dartbio_pop_data.parse('pop in million')
            cge_data['pop'] = dartbio_pop_data

        else:
            self.Logger.info(f'Disaggregation procedure for other CGE models than DART-BIO are not available yet.')

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

        region_key_timba = pd.ExcelFile(f'{self.sfile}\\data\\input\\m_Country.xlsx')
        region_key_timba = region_key_timba.parse('m_Country')
        region_key_timba = region_key_timba[['GFPM_CountryCode', 'GTAP10', f'{self.linked_CGE}_{self.project}',
                                             'ISO-Code']]

        if self.linked_CGE == 'DART-BIO':

            oecd_data_collector = {}
            oecd_data = pd.ExcelFile(f'{self.sfile}\\data\\input\\oecd_data.xlsx')
            oecd_gdp_data = oecd_data.parse('GDP_OECD')
            oecd_pop_data = oecd_data.parse('Pop_OECD_mio')
            oecd_data_collector['gdp'] = oecd_gdp_data
            oecd_data_collector['pop'] = oecd_pop_data

            worldbank_data_collector = {}
            worldbank_data = pd.ExcelFile(f'{self.sfile}\\data\\input\\worldbank_data.xlsx')
            worldbank_gdp_data = worldbank_data.parse('worldbank_GDP')
            worldbank_gdp_data.columns = worldbank_gdp_data.loc[3]
            worldbank_gdp_data = worldbank_gdp_data.iloc[4:, :].reset_index(drop=True)
            years_for_average = list(range(start_year - 1, start_year + 2))  # 3-years average
            col_selection = ['Country Name', 'Country Code'] + years_for_average
            worldbank_gdp_data = worldbank_gdp_data[col_selection]
            worldbank_gdp_data = worldbank_gdp_data.dropna()
            worldbank_pop_data = worldbank_data.parse('worldbank_Pop')
            worldbank_pop_data = worldbank_pop_data[col_selection]
            worldbank_pop_data = worldbank_pop_data.dropna()

            worldbank_data_collector['gdp'] = worldbank_gdp_data
            worldbank_data_collector['pop'] = worldbank_pop_data

            region_oecd_worldbank = pd.ExcelFile(f'{self.sfile}\\data\\input\\worldbank_oecd_countries.xlsx')
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

        if self.linked_CGE == 'MAGNET':

            cge_forest_data = pd.ExcelFile(f"{self.sfile}\\data\\input\\forestland_magnet_reference_scenario.xlsx")
            cge_forest_data = cge_forest_data.parse('iter_0')

            fra_forest_data = pd.read_csv(f"{self.sfile}\\data\\input\\fra_data.csv")

            self.cge_forest_data = cge_forest_data
            self.fra_data = fra_forest_data

        self.exogenous_change_structure = exogenous_change_structure
        self.start_year = start_year
        self.end_year = end_year
        self.commodity_key = commodity_key
        self.region_key_timba = region_key_timba

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

    def calc_forest_weights(self):
        """
        Calculates country-specific weights for each CGE region based on forest data provided by the forest resource
        assessment.
        """
        fra_data = self.fra_data[["ISO", "FRA_forest_area_km2"]]
        geo_data = self.region_key_timba

        cge_region = f"{self.linked_CGE}_{self.project}"

        geo_data = geo_data[geo_data["GFPM_CountryCode"] != "--"].reset_index(drop=True)
        forest_weights = geo_data.merge(fra_data, left_on="ISO-Code", right_on="ISO", how="left")
        forest_weights = forest_weights.fillna(0)

        forest_data_agg = forest_weights.groupby([cge_region]
                                                 )["FRA_forest_area_km2"].sum(numeric_only=True).reset_index()
        forest_weights["forest_area_cge_region_km2"] = pd.Series(dtype="float64")

        for region in forest_data_agg[cge_region].unique():
            region_index = forest_weights[forest_weights[cge_region] == region].index
            region_forest_data = float(forest_data_agg[forest_data_agg[cge_region] == region]["FRA_forest_area_km2"])
            forest_weights.loc[region_index, "forest_area_cge_region_km2"] = region_forest_data

        forest_weights["forest_weights"] = (forest_weights["FRA_forest_area_km2"] /
                                            forest_weights["forest_area_cge_region_km2"])

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
            temp_disagg_gdp = pd.DataFrame(disagg_gdp_data[str(year)] * disagg_gdp_data['gdp_weights'] * 1000000000
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

    def disagg_forest(self):
        pass

    def calc_gdp_per_capita(self):
        """
        Calculate GDP per capita with disaggregated projected GDP data from CGE and Population data from OECD (not
        changing in the CGE projections).
        :return: Calculated data for GDP per capita
        """
        self.Logger.info(f'Calculate GDP per capita using disaggregated data of GDP from '
                         f'{self.linked_CGE}_{self.project} and data of Pop from OECD.')
        gdp_per_capita = self.disagg_gdp[['Country Name', 'ISO-Code', 'GFPM_CountryCode', 'OECD_Ccodes',
                                          f'{self.linked_CGE}_{self.project}']]
        year_list = list(range(self.start_year, self.end_year + 1))
        for year in year_list:
            temp_gdp_per_capita = self.disagg_gdp[year] / self.disagg_pop[year]
            gdp_per_capita = pd.concat([gdp_per_capita, temp_gdp_per_capita], axis=1)

        return gdp_per_capita

    def calc_growth_rate(self, target_parameter: pd.DataFrame):
        """
        Calculate annual growth rate of economic variables (GDP and GDP per capita) projected by linked CGE and
        disaggregated to TiMBA country level
        :param target_parameter: Parameter for which growth rates will be calculated
        :return: Calculated growth rate
        """
        self.Logger.info(f'Calculate growth rate for {target_parameter}.')
        growth_rate = target_parameter[['Country Name', 'ISO-Code', 'GFPM_CountryCode', 'OECD_Ccodes',
                                        f'{self.linked_CGE}_{self.project}', self.start_year]]

        year_period_min = self.start_year
        for key in self.exogenous_change_structure.keys():
            year_period_max = year_period_min + self.exogenous_change_structure[key][1]
            periodic_growth_rate = pd.DataFrame((target_parameter[year_period_max] - target_parameter[year_period_min])
                                                / target_parameter[year_period_min]
                                                ).rename(columns={0: f"{year_period_max}"})
            annual_growth_rate = (1 + periodic_growth_rate) ** (1 / self.exogenous_change_structure[key][1]) - 1
            growth_rate = pd.concat([growth_rate, annual_growth_rate], axis=1)
            year_period_min = year_period_max

        return growth_rate

    def update_exogChange(self):
        """
        Updates exogChange-sheet in specified World-file for TiMBA with:
        - New annual growth rates for GDP (for demand and supply)
        - New annual growth rates for GDP per capita (for forest)
        Updated World input file is saved in Output.
        """
        self.Logger.info(f"Update World-file (ExogChange-sheet) with disaggregate Data.")
        world_to_update = pd.ExcelFile(f'{self.sfile}\\data\\input\\{self.input_world}.xlsx')
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
            index_demand = temp_ExogChange[temp_ExogChange[filter_col] == 'D'].index
            index_supply = temp_ExogChange[(temp_ExogChange[filter_col] == 'S') &
                                           (temp_ExogChange['Unnamed: 9'] != -1)].index
            index_forest = temp_ExogChange[temp_ExogChange[filter_col] == 'F'].index

            reformated_growth_rate_gdp = self.region_key_timba.merge(
                self.growth_rate_gdp[['GFPM_CountryCode', f'{year}']],
                left_on='GFPM_CountryCode',
                right_on='GFPM_CountryCode', how='left')
            reformated_growth_rate_gdp = reformated_growth_rate_gdp[['GFPM_CountryCode', f'{year}']].fillna(0)
            reformated_growth_rate_gdp = reformated_growth_rate_gdp[
                reformated_growth_rate_gdp['GFPM_CountryCode'] != '--'].reset_index(drop=True)
            reformated_growth_rate_gdp_demand = temp_ExogChange[
                temp_ExogChange[filter_col] == 'D'].merge(reformated_growth_rate_gdp,
                                                          left_on='Unnamed: 1',
                                                          right_on='GFPM_CountryCode',
                                                          how='left')

            reformated_growth_rate_gdp_supply = temp_ExogChange[
                (temp_ExogChange[filter_col] == 'S') &
                (temp_ExogChange['Unnamed: 9'] != -1)].merge(reformated_growth_rate_gdp,
                                                             left_on='Unnamed: 1',
                                                             right_on='GFPM_CountryCode',
                                                             how='left')

            reformated_growth_rate_gdp_cap = self.region_key_timba.merge(
                self.growth_rate_gdp_cap[['GFPM_CountryCode', f'{year}']], left_on='GFPM_CountryCode',
                right_on='GFPM_CountryCode', how='left')
            reformated_growth_rate_gdp_cap = reformated_growth_rate_gdp_cap[['GFPM_CountryCode', f'{year}']].fillna(0)
            reformated_growth_rate_gdp_cap = reformated_growth_rate_gdp_cap[
                reformated_growth_rate_gdp_cap['GFPM_CountryCode'] != '--'].reset_index(drop=True)

            temp_ExogChange.loc[index_demand, 'Unnamed: 9'] = reformated_growth_rate_gdp_demand.set_index(
                index_demand)[f'{year}']
            temp_ExogChange.loc[index_supply, 'Unnamed: 9'] = reformated_growth_rate_gdp_supply.set_index(
                index_supply)[f'{year}']
            temp_ExogChange.loc[index_forest, 'Unnamed: 9'] = reformated_growth_rate_gdp_cap.set_index(
                index_forest)[f'{year}']

            ExoChange_data_updated = pd.concat([ExoChange_data_updated, temp_ExogChange], axis=0)

        new_ExogChange = pd.concat([ExogChange_description, ExoChange_data_updated], axis=0).reset_index(drop=True)

        return new_ExogChange

    def update_World(self):
        self.Logger.info(f'Update {self.project} World with new ExogChange')
        output_folder = f'{self.sfile}\\data\\output\\'
        input_folder = f'{self.sfile}\\data\\input\\'
        time_stamp = dt.datetime.now().strftime("%Y%m%d")

        separator = '_'
        updated_world_name = self.input_world.split(separator)[1:]
        updated_world_name = f'{time_stamp}_Updated_{separator.join(updated_world_name)}'

        shutil.copy2(src=f'{input_folder}{self.input_world}.xlsx',
                     dst=f'{output_folder}{updated_world_name}.xlsx')

        wb = load_workbook(f'{output_folder}{updated_world_name}.xlsx')
        if 'ExogChange' in wb.sheetnames:
            wb.remove(wb['ExogChange'])
        wb.save(f'{output_folder}{updated_world_name}.xlsx')

        self.Logger.info(f'Save updated world')
        options = {'strings_to_formulas': False,
                   'strings_to_urls': False}

        with pd.ExcelWriter(f'{output_folder}{updated_world_name}.xlsx', engine='openpyxl',
                            mode='a', if_sheet_exists='replace') as writer:
            self.new_exogChange.to_excel(writer, sheet_name='ExogChange', index=False)

    def main_disaggregation_pipeline(self):
        Pipeline_Disagg = DisaggregateCGEResults(
            current_scenario=self.current_scenario,
            input_path_timba=self.input_path_timba,
            input_path_CGE=self.input_path_CGE,
            input_world=self.input_world,
            link_typ=self.link_typ,
            linked_CGE=self.linked_CGE,
            project=self.project
        )

        DisaggregateCGEResults.readin_help_data(Pipeline_Disagg)

        if self.linked_CGE == 'DART-BIO':
            Pipeline_Disagg.worldbank_gdp_weights = Pipeline_Disagg.calc_worldbank_gdp_weights()
            Pipeline_Disagg.worldbank_pop_weights = Pipeline_Disagg.calc_worldbank_pop_weights()

            Pipeline_Disagg.disagg_gdp = Pipeline_Disagg.disagg_gdp()
            Pipeline_Disagg.disagg_pop = Pipeline_Disagg.disagg_pop()

            Pipeline_Disagg.disagg_gdp_cap = Pipeline_Disagg.calc_gdp_per_capita()

            Pipeline_Disagg.growth_rate_gdp = Pipeline_Disagg.calc_growth_rate(
                target_parameter=Pipeline_Disagg.disagg_gdp)
            Pipeline_Disagg.growth_rate_gdp_cap = Pipeline_Disagg.calc_growth_rate(
                target_parameter=Pipeline_Disagg.disagg_gdp_cap)

            Pipeline_Disagg.new_exogChange = Pipeline_Disagg.update_exogChange()
            Pipeline_Disagg.update_World()

        elif self.linked_CGE == 'MAGNET':
            Pipeline_Disagg.forest_weights = Pipeline_Disagg.calc_forest_weights()
            Pipeline_Disagg.disagg_forest_data = Pipeline_Disagg.disagg_forest()

        else:
            Pipeline_Disagg.Logger.info(f'Disaggregation for {self.linked_CGE} is yet not implemented.')

        Pipeline_Disagg.Logger.info(f'This link is unbreakable.')
