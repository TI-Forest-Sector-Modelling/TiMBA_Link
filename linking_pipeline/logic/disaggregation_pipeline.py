# -----------------------------------------------------
# GFPMpt_linking_pipeline - disaggregation_pipeline (Tomke Honkomp (TH) - Thuenen-Institut)
# GCE-output disaggregation to GFPMpt (spatial and sectoral disaggregation)
# Status: 04.2024
# Last update: 04.2024
# -----------------------------------------------------

# imports
import pandas as pd
import numpy as np
import os
from pathlib import Path
import datetime as dt
from linking_pipeline.helper_functions.base_logger import get_logger
from linking_pipeline.parameters.defines import Constants, ProductStructures


class DisaggregateCGEResults(object):
    def __init__(self,
                 current_scenario: str,
                 input_path_gfpmpt: str,
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
        self.input_path_gfpmpt = input_path_gfpmpt
        self.input_path_CGE = input_path_CGE
        self.input_world = input_world
        self.link_typ = link_typ
        self.linked_CGE = linked_CGE
        self.project = project
        self.cge_data, self.gfpmpt_data = DisaggregateCGEResults.readin_model_data(self)
        (self.region_key, self.commodity_key, self.oecd_data, self.worldbank_data, self.exogenous_change_structure,
         self.start_year, self.end_year, self.year_for_avg) = DisaggregateCGEResults.readin_help_data(self)

    def readin_model_data(self):
        """
        Read in projection data from CGE for disaggregation. Processed data are specific to the linked CGE and the
        project. Add specific if-statements in the following to account for project specific GFPMpt-CGE-linkages.
        :return: Project and CGE model specific return (see in function for details)
        """

        self.Logger.info(f'Read in GFPMpt results {self.input_path_gfpmpt}.')
        import pickle
        src_path = f'{self.sfile}\\data\\input\\{self.input_path_gfpmpt}.pkl'
        with open(src_path, "rb") as pkl_file:
            gfpmpt_data = pickle.load(pkl_file)

        cge_data = {}
        if self.linked_CGE == 'DART-BIO':
            # For DART-BIO-GFPM-linkage GDP and GDPcap projections are disaggregated.
            self.Logger.info(f'Read in {self.linked_CGE}_{self.project} for GDP.')
            dartbio_gdp_data = pd.read_csv(f'{self.sfile}\\data\\input\\{self.input_path_CGE}.csv')
            cge_data['gdp'] = dartbio_gdp_data
            self.Logger.info(f'Read in {self.linked_CGE}_{self.input_path_CGE} for POP.')
            dartbio_pop_data = pd.ExcelFile(f'{self.sfile}\\data\\input\\dartbio_data_pop.xlsx')
            dartbio_pop_data = dartbio_pop_data.parse('pop in million')
            cge_data['pop'] = dartbio_pop_data

        else:
            self.Logger.info(f'Disaggregation procedure for other CGE models than DART-BIO are not available yet.')

        return cge_data, gfpmpt_data

    def readin_help_data(self):
        """
        Read in help data to disaggregate CGE data to product- and country-structure of GFPMpt.
        :return: Project and CGE model specific return (see in function for details)
        """
        self.Logger.info(f"Read in help data.")

        exogenous_change_data = self.gfpmpt_data['data_periods'][
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

        gfpmpt_commodities = self.gfpmpt_data['data_periods']['CommodityCode'].unique()

        if len(gfpmpt_commodities) == 14:
            commodity_key = pd.DataFrame.from_dict(ProductStructures.com_info_14.value)
        if len(gfpmpt_commodities) == 16:
            if self.project == 'BioSDG':
                commodity_key = pd.DataFrame.from_dict(ProductStructures.com_info_16_biosdg.value)
            else:
                commodity_key = pd.DataFrame.from_dict(ProductStructures.com_info_16.value)

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

            region_key = pd.ExcelFile(f'{self.sfile}\\data\\input\\m_Country.xlsx')
            region_key = region_key.parse('m_Country')
            region_key = region_key[['GFPM_CountryCode', 'GTAP10', f'{self.linked_CGE}_{self.project}', 'ISO-Code']]

            region_oecd_worldbank = pd.ExcelFile(f'{self.sfile}\\data\\input\\worldbank_oecd_countries.xlsx')
            region_oecd_worldbank = region_oecd_worldbank.parse('Country_codes').dropna()

            region_key_test = region_key.merge(region_oecd_worldbank, left_on="ISO-Code", right_on="Worldbank_Ccodes",
                                               how="left").dropna().reset_index(drop=True)
            region_key_test = region_key_test[['GFPM_CountryCode', 'GTAP10', f'{self.linked_CGE}_{self.project}',
                                               'ISO-Code', 'OECD_Ccodes']]

            return (region_key_test, commodity_key, oecd_data_collector, worldbank_data_collector,
                    exogenous_change_structure, start_year, end_year, years_for_average)

        else:
            self.Logger.info(f'Disaggregation procedure for other CGE models than DART-BIO are not available yet.')

    def calc_worldbank_gdp_weights(self):
        """
        Calculates GDP weights based on 3-years average of GDP data from Worldbank to disaggregate CGE data of GDP to
        country level of GFPMpt. Disaggregation of GDP data assumes that GDP shares of countries in each CGE region is
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
        data of population to country level of GFPMpt. Disaggregation of population data assumes that GDP shares of
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

    def main_disaggregation_pipeline(self):
        Pipeline_Disagg = DisaggregateCGEResults(
            current_scenario=self.current_scenario,
            input_path_gfpmpt=self.input_path_gfpmpt,
            input_path_CGE=self.input_path_CGE,
            input_world=self.input_world,
            link_typ=self.link_typ,
            linked_CGE=self.linked_CGE,
            project=self.project
        )

        Pipeline_Disagg.worldbank_gdp_weights = Pipeline_Disagg.calc_worldbank_gdp_weights()
        Pipeline_Disagg.worldbank_pop_weights = Pipeline_Disagg.calc_worldbank_pop_weights()

        Pipeline_Disagg.disagg_gdp = Pipeline_Disagg.disagg_gdp()
        Pipeline_Disagg.disagg_pop = Pipeline_Disagg.disagg_pop()


        Pipeline_Disagg.Logger.info(f'This link is unbreakable.')
