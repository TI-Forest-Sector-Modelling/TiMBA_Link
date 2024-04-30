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
         self.start_year, self.end_year) = DisaggregateCGEResults.readin_help_data(self)

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
                    exogenous_change_structure, start_year, end_year)

        else:
            self.Logger.info(f'Disaggregation procedure for other CGE models than DART-BIO are not available yet.')


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
