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
from pathlib import Path
import datetime as dt
from linking_pipeline.helper_functions.base_logger import get_logger
from linking_pipeline.parameters.defines import Constants, ProductStructures


class AggregateTiMBAResults(object):
    def __init__(self,
                 current_scenario: str,
                 input_path_timba: str,
                 link_typ: str,
                 linked_CGE: str,
                 project: str
                 ):
        self.sfile = os.path.dirname(Path(__file__).resolve().parents[0])
        self.Logger = get_logger(user_path=None, aggregation_flag=True)
        self.current_scenario = current_scenario
        self.current_dt = dt.datetime.now().strftime("%Y%m%d")
        self.input_path_timba = input_path_timba
        self.link_typ = link_typ
        self.linked_CGE = linked_CGE
        self.project = project
        self.timba_data = AggregateTiMBAResults.readin_model_data(self)
        (self.region_key, self.commodity_key, self.exogenous_change_structure, self.start_year, self.end_year
         ) = AggregateTiMBAResults.readin_help_data(self)

    def readin_model_data(self):
        """
        Read in TiMBA data for production (ManufactureCost and Supply)
        :return pd.DataFrame: TiMBA data
        """
        self.Logger.info(f"Read in TiMBA results {self.input_path_timba}.")
        src_path = f'{self.sfile}\\data\\input\\{self.input_path_timba}.pkl'

        try:
            with open(src_path, "rb") as pkl_file:
                timba_data = pickle.load(pkl_file)
        except pickle.UnpicklingError:
            with gzip.open(src_path, "rb") as pkl_file:
                timba_data = pickle.load(pkl_file)

        return timba_data

    def readin_help_data(self):
        """
        Read in help data used for the aggregation to CGE-sectors (commodity_key) and to CGE-regions
        (region_key). Exogenous_change_structure stores information about the number of periods and the length of each
         period
        :return: help data in different types (pd.DataFrame and dict)
        """
        self.Logger.info(f"Read in help data.")
        timba_commodities = self.timba_data['data_periods']['CommodityCode'].unique()

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

        return region_key, commodity_key, exogenous_change_structure, start_year, end_year

    def aggregate_production_data(self, intermediate_aggregation: bool):
        """
        Aggregate TiMBA data for production to selected TiMBA level in three steps.
        1. step: Aggregate TiMBA data for production by summing up supply and manufacturecost (production_data)
        2. step: Aggregate TiMBA data for production to CGE regions (region_production_data)
        3. step: Aggregate TiMBA data for production to CGE sectors (sector_production_data)
        :param intermediate_aggregation: Flag controlling if intermediate aggregation is included in a separate column
        :return: Aggregated production data to CGE level (region and sector)
        """
        self.Logger.info(f"Aggregate TiMBA data for production to {self.linked_CGE} (region and sector).")
        timba_data = self.timba_data['data_periods']
        # TODO consider to include trade in calculations
        production_data = timba_data[(timba_data['domain'] == 'Supply') |
                                     (timba_data['domain'] == 'ManufactureCost')]
        production_data = production_data.groupby(["RegionCode", "CommodityCode", "year"]
                                                  )["quantity"].sum().reset_index()

        export_data = timba_data[timba_data['domain'] == 'TransportationExport']
        import_data = timba_data[timba_data['domain'] == 'TransportationImport']
        export_data = export_data.sort_values(by=['RegionCode', 'CommodityCode', 'year'],
                                              ascending=True).reset_index(drop=True)
        import_data = import_data.sort_values(by=['RegionCode', 'CommodityCode', 'year'],
                                              ascending=True).reset_index(drop=True)

        production_data['quantity'] = production_data['quantity'] + import_data['quantity'] - export_data['quantity']

        production_data = production_data.merge(self.region_key, left_on="RegionCode", right_on="GFPM_CountryCode",
                                                how="left").dropna()

        if intermediate_aggregation:
            production_data = production_data.merge(self.commodity_key, left_on='CommodityCode',
                                                    right_on='GFPMpt_Comcode', how='left')
            sector_production_data = production_data.groupby([f"{self.linked_CGE}_{self.project}", "GFPMpt_Comgroup",
                                                              "GTAP-Sector", "year"])["quantity"].sum().reset_index()

        else:
            region_production_data = production_data.groupby([f"{self.linked_CGE}_{self.project}", "CommodityCode",
                                                              "year"])["quantity"].sum().reset_index()
            region_production_data = region_production_data.merge(self.commodity_key, left_on="CommodityCode",
                                                                  right_on="GFPMpt_Comcode", how="left")
            sector_production_data = region_production_data.groupby([f"{self.linked_CGE}_{self.project}", "GTAP-Sector",
                                                                     "year"])["quantity"].sum().reset_index()
        return sector_production_data, production_data

    def share_energy_material_use(self):
        production_data = self.production_data
        production_data = production_data.sort_values(by=['year', 'RegionCode'], ascending=True).reset_index(drop=True)
        share_of_fuelwood = self.timba_data['Forest']['FuelwoodForest']
        production_data['quantity'] = production_data['quantity'] * share_of_fuelwood

        fuelwood_production_data = production_data[production_data['CommodityCode'] == 80].reset_index(drop=True)
        fuelwood_production_data = fuelwood_production_data.groupby([
            f'{self.linked_CGE}_{self.project}', 'CommodityCode', 'year'])['quantity'].sum().reset_index()

        region_production_data = production_data.groupby([f"{self.linked_CGE}_{self.project}", "CommodityCode",
                                                          "year"])["quantity"].sum().reset_index()

        region_production_data = region_production_data.merge(self.commodity_key, left_on="CommodityCode",
                                                              right_on="GFPMpt_Comcode", how="left")
        sector_production_data = region_production_data.groupby([f"{self.linked_CGE}_{self.project}", "GTAP-Sector",
                                                                 "year"])["quantity"].sum().reset_index()

        sector_production_data = sector_production_data[
            sector_production_data['GTAP-Sector'] == 'FRS'].reset_index(drop=True)

        info_data = fuelwood_production_data[[f'{self.linked_CGE}_{self.project}', 'year']]
        share_energy_use = fuelwood_production_data['quantity'] / sector_production_data['quantity']
        share_energy_use = pd.concat([info_data, share_energy_use], axis=1).rename(
            columns={'quantity': 'share_energy_use'})

        return share_energy_use

    def agg_price_data(self):
        """
        Aggregate TiMBA data for product prices to CGE level in five steps. Aggregated prices are weighted using
        aggregated values and quantity.
        1. step: Aggregate TiMBA data for production and for price by summing up supply and manufacturecost
        (production_data and price_data)
        2. step: Calculate values (production quantity * prices)
        3. step: Aggregate TiMBA data for production and for values to CGE regions (region_production_data and
        region_value_data)
        4. step: Aggregate TiMBA data for production and for values to CGE sectors (sector_production_data and
        sector_value_data)
        5. step: Aggregate TiMBA data for prices as weighted prices using aggregated values and production.
        :return pd.DataFrame: Aggregated and weighted price data to  CGE level (region and sector)
        """
        self.Logger.info(f'Aggregate TiMBA data for price to {self.linked_CGE} (region and sector).')
        production_data = self.timba_data['data_periods']
        production_data = production_data[(production_data['domain'] == 'Supply') |
                                          (production_data['domain'] == 'ManufactureCost')]

        price_data = production_data.groupby(['RegionCode', 'CommodityCode', 'year'])['price'].sum().reset_index()
        production_data = production_data.groupby(['RegionCode', 'CommodityCode', 'year']
                                                  )['quantity'].sum().reset_index()

        price_data = price_data.merge(self.region_key, left_on='RegionCode', right_on='GFPM_CountryCode',
                                      how='left').dropna()
        production_data = production_data.merge(self.region_key, left_on='RegionCode', right_on='GFPM_CountryCode',
                                                how='left').dropna()

        value_data = pd.concat([production_data[['RegionCode', 'CommodityCode', 'year',
                                                 f'{self.linked_CGE}_{self.project}']],
                                pd.DataFrame(production_data['quantity'] * price_data['price'])],
                               axis=1).rename(columns={0: 'value'})

        region_production_data = production_data.groupby([f'{self.linked_CGE}_{self.project}', 'CommodityCode', 'year'
                                                          ])['quantity'].sum().reset_index()
        region_value_data = value_data.groupby([f'{self.linked_CGE}_{self.project}', 'CommodityCode', 'year'
                                                ])['value'].sum().reset_index()

        region_production_data = region_production_data.merge(self.commodity_key, left_on='CommodityCode',
                                                              right_on='GFPMpt_Comcode',
                                                              how='left')

        region_value_data = region_value_data.merge(self.commodity_key, left_on='CommodityCode',
                                                    right_on='GFPMpt_Comcode',
                                                    how='left')

        sector_value_data = region_value_data.groupby([f'{self.linked_CGE}_{self.project}', 'GTAP-Sector', 'year'
                                                       ])['value'].sum().reset_index()
        sector_production_data = region_production_data.groupby([f'{self.linked_CGE}_{self.project}', 'GTAP-Sector',
                                                                 'year'])['quantity'].sum().reset_index()

        sector_price_data = pd.DataFrame(sector_value_data['value'] / sector_production_data['quantity']).rename(
            columns={0: 'price'})

        sector_price_data = pd.concat([sector_production_data[[f'{self.linked_CGE}_{self.project}', 'GTAP-Sector',
                                                               'year']], sector_price_data], axis=1)

        return sector_price_data

    def agg_value_data(self):
        """
        Aggregate TiMBA data for values to CGE level in three steps.
        1. step: Aggregate TiMBA data for production and for price by summing up supply and manufacturecost
        (production_data and price_data)
        2. step: Calculate values (production quantity * prices)
        2. step: Aggregate TiMBA data for values to CGE regions (region_value_data)
        3. step: Aggregate TiMBA data for values to CGE sectors (sector_value_data)
        :return: Aggregated value data to CGE level (region and sector)
        """
        self.Logger.info(f'Aggregate TiMBA data for value to {self.linked_CGE} (region and sector).')

        timba_data = self.timba_data['data_periods']
        timba_data = timba_data[(timba_data['domain'] == 'Supply') |
                                (timba_data['domain'] == 'ManufactureCost')]

        price_data = timba_data.groupby(['RegionCode', 'CommodityCode', 'year'])['price'].sum().reset_index()
        production_data = timba_data.groupby(['RegionCode', 'CommodityCode', 'year'])['quantity'].sum().reset_index()

        price_data = price_data.merge(self.region_key, left_on='RegionCode', right_on='GFPM_CountryCode',
                                      how='left').dropna()
        production_data = production_data.merge(self.region_key, left_on='RegionCode', right_on='GFPM_CountryCode',
                                                how='left').dropna()

        value_data = pd.concat([production_data[['RegionCode', 'CommodityCode', 'year',
                                                 f'{self.linked_CGE}_{self.project}']],
                                pd.DataFrame(production_data['quantity'] * price_data['price'])],
                               axis=1).rename(columns={0: 'value'})
        region_value_data = value_data.groupby([f'{self.linked_CGE}_{self.project}', 'CommodityCode', 'year'
                                                ])['value'].sum().reset_index()
        region_value_data = region_value_data.merge(self.commodity_key, left_on='CommodityCode',
                                                    right_on='GFPMpt_Comcode',
                                                    how='left')

        sector_value_data = region_value_data.groupby([f'{self.linked_CGE}_{self.project}', 'GTAP-Sector', 'year'
                                                       ])['value'].sum().reset_index()

        return sector_value_data

    def agg_forest_data(self):
        """
        Aggregate TiMBA data for forest stock and area to selected CGE level (regions)
        :return: Aggregated forest data to selected CGE level (regions)
        """
        self.Logger.info(f'Aggregate TiMBA data for forest to {self.linked_CGE} (region and sector).')

        forest_data = self.timba_data['Forest']
        period_data = self.timba_data['data_periods'][['Period', 'year']].drop_duplicates().reset_index(drop=True)
        forest_data = forest_data.merge(period_data, left_on='Period', right_on='Period', how='left')
        forest_data = forest_data[['RegionCode', 'Period', 'year', 'ForStock', 'ForArea']]
        forest_data = forest_data.merge(self.region_key, left_on='RegionCode', right_on='GFPM_CountryCode',
                                        how='left').dropna().drop_duplicates()

        region_forest_area = forest_data.groupby([f'{self.linked_CGE}_{self.project}', 'year']
                                                 )['ForArea'].sum().reset_index()
        region_forest_stock = forest_data.groupby([f'{self.linked_CGE}_{self.project}', 'year']
                                                  )['ForStock'].sum().reset_index()

        return region_forest_stock, region_forest_area

    def agg_harvest_data(self):
        """
        Aggregate TiMBA data for raw material from forest (= harvest) to selected CGE level (regions) using TiMBA
        parameter raw_material_from_forest to aggregate only supply originating from forests.
        :return: Aggregated harvest data to selected CGE level (regions)
        """
        self.Logger.info(f'Aggregate TiMBA data for harvest to {self.linked_CGE} (region and sector).')
        # todo add fuelwood from forest to forest df in TiMBA results to make calculations
        harvest_data = self.timba_data['data_periods']
        harvest_data = harvest_data[(harvest_data['domain'] == 'Supply') &
                                    (harvest_data['RegionCode'] != 'zy')].reset_index(drop=True)
        fuelwood_from_forest = self.timba_data['Forest']['FuelwoodForest']

        harvest_data.loc[:, 'quantity'] = harvest_data['quantity'] * fuelwood_from_forest
        harvest_data = harvest_data[harvest_data['CommodityCode'] < 83].reset_index(drop=True)

        harvest_data = harvest_data.groupby(['RegionCode', 'year'])['quantity'].sum().reset_index()
        harvest_data = harvest_data.merge(self.region_key, left_on='RegionCode', right_on='GFPM_CountryCode',
                                          how='left').dropna().reset_index(drop=True)
        region_harvest_data = harvest_data.groupby([f'{self.linked_CGE}_{self.project}', 'year']
                                                   )['quantity'].sum().reset_index()

        return region_harvest_data

    def calc_harvest_intensity(self):
        """
        Calculate harvest intensity as the ratio of harvest per forest area [Efm.ha-1] for each region of the selected
        CGE.
        :return pd.DataFrame: Harvest intensities for each region of the selected CGE
        """
        # todo add fuelwood from forest to forest df in GFPMpt results to make calculations
        agg_forest_area = self.agg_forest_area
        harvest_intensity = pd.DataFrame((self.agg_harvest_data['quantity'] * 1000) /
                                         (agg_forest_area['ForArea'] * 1000)
                                         ).rename(columns={0: 'harvest_intensity'})
        harvest_intensity = pd.concat([self.agg_harvest_data[[f'{self.linked_CGE}_{self.project}', 'year']],
                                       harvest_intensity], axis=1)

        return harvest_intensity

    def agg_carbon_data(self):
        """
        Aggregate TiMBA data for carbon to selected CGE level (regions)
        :return: Aggregated carbon data to selected CGE level (regions)
        """
        self.Logger.info(f'Aggregate TiMBA data for carbon to {self.linked_CGE} (region and sector).')

        carbon_data = self.timba_data['Carbon']
        period_data = self.timba_data['data_periods'][['Period', 'year']].drop_duplicates().reset_index(drop=True)
        carbon_data = carbon_data.merge(period_data, left_on='Period', right_on='Period', how='left')
        carbon_data = carbon_data.merge(self.region_key, left_on='RegionCode', right_on='GFPM_CountryCode',
                                        how='left').dropna().drop_duplicates()

        region_carbon_biomass = carbon_data.groupby([f'{self.linked_CGE}_{self.project}', 'year']
                                                    )['CarbonStockBiomass [MtCO2]'].sum().reset_index()
        region_carbon_hwp = carbon_data.groupby([f'{self.linked_CGE}_{self.project}', 'year']
                                                )['CarbonStockHWP [MtCO2]'].sum().reset_index()

        return region_carbon_biomass, region_carbon_hwp

    def calc_input_frs_lum(self, target_data: pd.DataFrame, start_year: int):
        """
        Calculate the input of frs (total roundwood production) in total amout of lum (sawnwood and wood-based panels)
        based on production data.
        :param target_data: aggregated TiMBA production data
        :param start_year: Year from which growth rates will be calculated (for BioSDG-project = 2011)
        :return pd.DataFrame: Input frs in lum
        """
        self.Logger.info(f"Calculate input of frs (TR)  in lum (WBP and S).")
        year = start_year
        df_io = pd.DataFrame(target_data[target_data['GFPMpt_Comgroup'] == 'S'].reset_index(
            drop=True)[f'{self.linked_CGE}_{self.project}'])
        df_io['Input_Output'] = ['frs in lum'] * len(df_io)
        for period_key in self.exogenous_change_structure.keys():
            period_length = self.exogenous_change_structure[period_key][1]

            lum_output = (target_data[target_data['GFPMpt_Comgroup'] == 'S'][year].reset_index(drop=True) +
                          target_data[target_data['GFPMpt_Comgroup'] == 'WBP'][year].reset_index(drop=True))

            frs_input = target_data[target_data['GFPMpt_Comgroup'] == 'TR'][year].reset_index(drop=True)
            # TODO remove 82 from calculation of io as commodity is not used for further processing, Provide information
            #  about share of fuelwood in FRS
            io = pd.DataFrame(lum_output / frs_input)
            df_io = pd.concat([df_io, io], axis=1)
            year += period_length

        return df_io

    def calc_input_frs_ppp(self, target_data: pd.DataFrame, start_year: int):
        """
        Calculate the input of frs (total roundwood production) in total amout of ppp (mechanical and chemical pulp)
        based on production data.
        :param target_data: aggregated TiMBA production data
        :param start_year: Year from which growth rates will be calculated (for BioSDG-project = 2011)
        :return pd.DataFrame: Input frs in lum
        """
        self.Logger.info(f"Calculate input of frs (TR)  in ppp (CP and MP).")
        year = start_year
        df_io = pd.DataFrame(
            target_data[target_data['GFPMpt_Comgroup'] == 'CP'].reset_index(
                drop=True)[f'{self.linked_CGE}_{self.project}'])
        df_io['Input_Output'] = ['frs in ppp'] * len(df_io)
        for period_key in self.exogenous_change_structure.keys():
            period_length = self.exogenous_change_structure[period_key][1]

            ppp_output = (target_data[target_data['GFPMpt_Comgroup'] == 'CP'][year].reset_index(drop=True) +
                          target_data[target_data['GFPMpt_Comgroup'] == 'MP'][year].reset_index(drop=True))

            frs_input = target_data[target_data['GFPMpt_Comgroup'] == 'TR'][year].reset_index(drop=True)
            # TODO remove 82 from calculation of io as commodity is not used for further processing, Provide information
            #  about share of fuelwood in FRS
            io = pd.DataFrame(ppp_output / frs_input)
            df_io = pd.concat([df_io, io], axis=1)
            year += period_length

        return df_io

    def calc_input_ppp_ppp(self, target_data: pd.DataFrame, start_year: int):
        """
        Calculate the input of frs (total roundwood production) in total amout of ppp (mechanical and chemical pulp)
        based on production data.
        :param target_data: aggregated TiMBA production data
        :param start_year: Year from which growth rates will be calculated (for BioSDG-project = 2011)
        :return pd.DataFrame: Input frs in lum
        """
        self.Logger.info(f"Calculate input of frs (TR)  in ppp (CP and MP).")
        year = start_year
        df_io = pd.DataFrame(
            target_data[target_data['GFPMpt_Comgroup'] == 'CP'].reset_index(
                drop=True)[f'{self.linked_CGE}_{self.project}'])
        df_io['Input_Output'] = ['frs in ppp'] * len(df_io)
        for period_key in self.exogenous_change_structure.keys():
            period_length = self.exogenous_change_structure[period_key][1]

            ppp_output = (target_data[target_data['GFPMpt_Comgroup'] == 'CP'][year].reset_index(drop=True) +
                          target_data[target_data['GFPMpt_Comgroup'] == 'MP'][year].reset_index(drop=True))

            frs_input = target_data[target_data['GFPMpt_Comgroup'] == 'TR'][year].reset_index(drop=True)
            # TODO remove 82 from calculation of io as commodity is not used for further processing, Provide information
            #  about share of fuelwood in FRS
            io = pd.DataFrame(ppp_output / frs_input)
            df_io = pd.concat([df_io, io], axis=1)
            year += period_length

        return df_io

    def process_io_data(self):
        """
        Compile data for Input-Output-coefficients and add region and sector information for aggregation to CGE.
        Production quantities are used for weightings.
        :return: Complied IO-data stored as a dataframe
        """

        period_info = self.timba_data['data_periods'][['Period', 'year']].drop_duplicates().reset_index(drop=True)
        io_data = self.timba_data['ManufactureCoeff']
        io_data = io_data.merge(period_info, left_on='Period', right_on='Period', how='left')
        io_data = io_data.merge(self.commodity_key,
                                left_on='InputCommodity',
                                right_on='GFPMpt_Comcode',
                                how='left').rename(columns={'GFPMpt_Comgroup': 'Input_Comgroup'})

        io_data = io_data.merge(self.commodity_key,
                                left_on='OutputCommodity',
                                right_on='GFPMpt_Comcode',
                                how='left').rename(columns={'GFPMpt_Comgroup': 'Output_Comgroup'})

        timba_data = self.timba_data['data_periods']
        production_data = timba_data[(timba_data['domain'] == 'Supply') |
                                     (timba_data['domain'] == 'ManufactureCost')]

        production_data = production_data.groupby(['RegionCode', 'CommodityCode', 'year']
                                                  )['quantity'].sum().reset_index()

        export_data = timba_data[timba_data['domain'] == 'TransportationExport']
        import_data = timba_data[timba_data['domain'] == 'TransportationImport']
        export_data = export_data.sort_values(by=['RegionCode', 'CommodityCode', 'year']).reset_index(drop=True)
        import_data = import_data.sort_values(by=['RegionCode', 'CommodityCode', 'year']).reset_index(drop=True)

        production_data['quantity'] = production_data['quantity'] + import_data['quantity'] - export_data['quantity']

        # TODO test with production data for InputCommodity
        """io_data = io_data.merge(production_data,
                                left_on=['RegionCode', 'year', 'InputCommodity'],
                                right_on=['RegionCode', 'year', 'CommodityCode'],
                                how='left')"""
        # TODO test with production data for OutputCommodity
        io_data = io_data.merge(production_data,
                                left_on=['RegionCode', 'year', 'OutputCommodity'],
                                right_on=['RegionCode', 'year', 'CommodityCode'],
                                how='left')

        io_data = io_data[['RegionCode', 'CommodityCode_x', 'Period', 'year', 'InputCommodity', 'OutputCommodity',
                           'Input_Comgroup', 'Output_Comgroup', 'ManuFakt', 'quantity']]

        io_data['quantity'].fillna(0, inplace=True)

        return io_data

    def calc_io_frs_lum(self, weighted_io: bool):
        """
        Calculates the Input-Output-coefficients (IOs) for FRS to produce LUM. IOs for each sector are calculated as the
        average of all composing products for each country. IOs for each CGE region is calculated as the average of all
        composing countries. Sector and region averages can be weighted with the production quantity to account for
        market relevance of each country and product.
        :param weighted_io: Flag to activate weighted averages for IO calculations.
        :return: Calculated IOs for FRS-LUM as a new dataframe
        """
        io_data = self.io_data
        io_frs_lum = io_data[(io_data['Input_Comgroup'] == 'TR') &
                             ([x in ['S', 'WBP'] for x in io_data['Output_Comgroup']])].reset_index(drop=True)
        io_frs_lum = io_frs_lum[io_frs_lum['ManuFakt'] != 0].reset_index(drop=True)
        io_frs_lum['weighted_ManuFakt'] = io_frs_lum['ManuFakt'] * io_frs_lum['quantity']
        io_frs_lum['input'] = ['FRS'] * len(io_frs_lum)
        io_frs_lum['output'] = ['LUM'] * len(io_frs_lum)

        if weighted_io:
            # Weighted averages for products to sectors
            sector_weight_mean = io_frs_lum.groupby(
                ['RegionCode', 'year', 'input', 'output'])['quantity'].sum().reset_index()
            sector_weighted_ManuFakt_mean = io_frs_lum.groupby(
                ['RegionCode', 'year', 'input', 'output'])['weighted_ManuFakt'].sum().reset_index()
            sector_weighted_io = sector_weighted_ManuFakt_mean['weighted_ManuFakt'] / sector_weight_mean['quantity']
            sector_weighted_io = pd.DataFrame(sector_weighted_io).rename(columns={0: 'ManuFakt'})
            io_info = sector_weight_mean[['RegionCode', 'year', 'input', 'output']]
            io_frs_lum = pd.concat([io_info, sector_weighted_io, sector_weight_mean['quantity']], axis=1)

            # Weighted averages for countries to regions
            io_frs_lum = io_frs_lum.merge(self.region_key,
                                          left_on='RegionCode',
                                          right_on='GFPM_CountryCode',
                                          how='left')
            io_frs_lum['weighted_ManuFakt'] = io_frs_lum['ManuFakt'] * io_frs_lum['quantity']
            region_weight_mean = io_frs_lum.groupby(
                [f'{self.linked_CGE}_{self.project}', 'year', 'input', 'output'])['quantity'].sum().reset_index()
            region_weighted_ManuFakt_mean = io_frs_lum.groupby(
                [f'{self.linked_CGE}_{self.project}', 'year', 'input', 'output'])['weighted_ManuFakt'].sum().reset_index()

            region_weighted_io = region_weighted_ManuFakt_mean['weighted_ManuFakt'] / region_weight_mean['quantity']
            region_weighted_io = pd.DataFrame(region_weighted_io).rename(columns={0: 'ManuFakt'})
            io_info = region_weight_mean[[f'{self.linked_CGE}_{self.project}', 'year', 'input', 'output']]
            io_frs_lum = pd.concat([io_info, region_weighted_io], axis=1)

        else:
            # Average IOs for sectors in each country
            io_frs_lum = io_frs_lum.groupby(['RegionCode', 'year', 'input', 'output'])['ManuFakt'].mean().reset_index()

            # Average IOs for sectors in each regions
            io_frs_lum = io_frs_lum.merge(self.region_key,
                                          left_on='RegionCode',
                                          right_on='GFPM_CountryCode',
                                          how='left')
            io_frs_lum = io_frs_lum.groupby([f'{self.linked_CGE}_{self.project}', 'input', 'output', 'year']).mean().reset_index()

        return io_frs_lum

    def calc_io_frs_ppp(self, weighted_io: bool):
        """
        Calculates the Input-Output-coefficients (IOs) for FRS to produce PPP. IOs for each sector are calculated as the
        average of all composing products for each country. IOs for each CGE region is calculated as the average of all
        composing countries. Sector and region averages can be weighted with the production quantity to account for
        market relevance of each country and product.
        :param weighted_io: Flag to activate weighted averages for IO calculations.
        :return: Calculated IOs for FRS-PPP as a new dataframe
        """
        io_data = self.io_data
        io_frs_ppp = io_data[(io_data['Input_Comgroup'] == 'TR') &
                             ([x in ['CP', 'MP'] for x in io_data['Output_Comgroup']])].reset_index(drop=True)
        io_frs_ppp = io_frs_ppp[io_frs_ppp['ManuFakt'] != 0].reset_index(drop=True)
        io_frs_ppp['weighted_ManuFakt'] = io_frs_ppp['ManuFakt'] * io_frs_ppp['quantity']
        io_frs_ppp['input'] = ['FRS'] * len(io_frs_ppp)
        io_frs_ppp['output'] = ['PPP'] * len(io_frs_ppp)

        if weighted_io:
            # Weighted averages for products to sectors
            sector_weight_mean = io_frs_ppp.groupby(
                ['RegionCode', 'year', 'input', 'output'])['quantity'].sum().reset_index()
            sector_weighted_ManuFakt_mean = io_frs_ppp.groupby(
                ['RegionCode', 'year', 'input', 'output'])['weighted_ManuFakt'].sum().reset_index()
            sector_weighted_io = sector_weighted_ManuFakt_mean['weighted_ManuFakt'] / sector_weight_mean['quantity']
            sector_weighted_io = pd.DataFrame(sector_weighted_io).rename(columns={0: 'ManuFakt'})
            io_info = sector_weight_mean[['RegionCode', 'year', 'input', 'output']]
            io_frs_ppp = pd.concat([io_info, sector_weighted_io, sector_weight_mean['quantity']], axis=1)

            # Weighted averages for countries to regions
            io_frs_ppp = io_frs_ppp.merge(self.region_key,
                                          left_on='RegionCode',
                                          right_on='GFPM_CountryCode',
                                          how='left')
            io_frs_ppp['weighted_ManuFakt'] = io_frs_ppp['ManuFakt'] * io_frs_ppp['quantity']
            region_weight_mean = io_frs_ppp.groupby(
                [f'{self.linked_CGE}_{self.project}', 'year', 'input', 'output'])['quantity'].sum().reset_index()
            region_weighted_ManuFakt_mean = io_frs_ppp.groupby(
                [f'{self.linked_CGE}_{self.project}', 'year', 'input', 'output'])['weighted_ManuFakt'].sum().reset_index()

            region_weighted_io = region_weighted_ManuFakt_mean['weighted_ManuFakt'] / region_weight_mean['quantity']
            region_weighted_io = pd.DataFrame(region_weighted_io).rename(columns={0: 'ManuFakt'})
            io_info = region_weight_mean[[f'{self.linked_CGE}_{self.project}', 'year', 'input', 'output']]
            io_frs_ppp = pd.concat([io_info, region_weighted_io], axis=1)

        else:
            # Average IOs for sectors in each country
            io_frs_ppp = io_frs_ppp.groupby(['RegionCode', 'year', 'input', 'output'])['ManuFakt'].mean().reset_index()

            # Average IOs for sectors in each regions
            io_frs_ppp = io_frs_ppp.merge(self.region_key,
                                          left_on='RegionCode',
                                          right_on='GFPM_CountryCode',
                                          how='left')

            io_frs_ppp = io_frs_ppp.groupby([f'{self.linked_CGE}_{self.project}', 'input', 'output', 'year']).mean().reset_index()

        return io_frs_ppp

    def calc_io_ppp_ppp(self, weighted_io: bool):
        """
        Calculates the Input-Output-coefficients (IOs) for PPP to produce PPP. IOs for each sector are calculated as the
        average of all composing products for each country. IOs for each CGE region is calculated as the average of all
        composing countries. Sector and region averages can be weighted with the production quantity to account for
        market relevance of each country and product.
        :param weighted_io: Flag to activate weighted averages for IO calculations.
        :return: Calculated IOs for PPP-PPP as a new dataframe
        """
        io_data = self.io_data
        io_ppp_ppp = io_data[([x in ['CP', 'MP', 'TPP'] for x in io_data['Input_Comgroup']]) &
                             (io_data['Output_Comgroup'] == 'TPP')].reset_index(drop=True)
        io_ppp_ppp = io_ppp_ppp[io_ppp_ppp['ManuFakt'] != 0].reset_index(drop=True)
        io_ppp_ppp['weighted_ManuFakt'] = io_ppp_ppp['ManuFakt'] * io_ppp_ppp['quantity']
        io_ppp_ppp['input'] = ['PPP'] * len(io_ppp_ppp)
        io_ppp_ppp['output'] = ['PPP'] * len(io_ppp_ppp)

        if weighted_io:
            # Weighted averages for products to sectors
            sector_weight_mean = io_ppp_ppp.groupby(
                ['RegionCode', 'year', 'input', 'output'])['quantity'].sum().reset_index()
            sector_weighted_ManuFakt_mean = io_ppp_ppp.groupby(
                ['RegionCode', 'year', 'input', 'output'])['weighted_ManuFakt'].sum().reset_index()
            sector_weighted_io = sector_weighted_ManuFakt_mean['weighted_ManuFakt'] / sector_weight_mean['quantity']
            sector_weighted_io = pd.DataFrame(sector_weighted_io).rename(columns={0: 'ManuFakt'})
            io_info = sector_weight_mean[['RegionCode', 'year', 'input', 'output']]
            io_ppp_ppp = pd.concat([io_info, sector_weighted_io, sector_weight_mean['quantity']], axis=1)

            # Weighted averages for countries to regions
            io_ppp_ppp = io_ppp_ppp.merge(self.region_key,
                                          left_on='RegionCode',
                                          right_on='GFPM_CountryCode',
                                          how='left')
            io_ppp_ppp['weighted_ManuFakt'] = io_ppp_ppp['ManuFakt'] * io_ppp_ppp['quantity']
            region_weight_mean = io_ppp_ppp.groupby(
                [f'{self.linked_CGE}_{self.project}', 'year', 'input', 'output'])['quantity'].sum().reset_index()
            region_weighted_ManuFakt_mean = io_ppp_ppp.groupby(
                [f'{self.linked_CGE}_{self.project}', 'year', 'input', 'output'])['weighted_ManuFakt'].sum().reset_index()

            region_weighted_io = region_weighted_ManuFakt_mean['weighted_ManuFakt'] / region_weight_mean['quantity']
            region_weighted_io = pd.DataFrame(region_weighted_io).rename(columns={0: 'ManuFakt'})
            io_info = region_weight_mean[[f'{self.linked_CGE}_{self.project}', 'year', 'input', 'output']]
            io_ppp_ppp = pd.concat([io_info, region_weighted_io], axis=1)

        else:
            # Average IOs for sectors in each country
            io_ppp_ppp = io_ppp_ppp.groupby(['RegionCode', 'year', 'input', 'output'])['ManuFakt'].mean().reset_index()

            # Average IOs for sectors in each regions
            io_ppp_ppp = io_ppp_ppp.merge(self.region_key,
                                          left_on='RegionCode',
                                          right_on='GFPM_CountryCode',
                                          how='left')

            io_ppp_ppp = io_ppp_ppp.groupby([f'{self.linked_CGE}_{self.project}', 'input', 'output', 'year']).mean().reset_index()

        return io_ppp_ppp

    def merge_io_data(self):
        io_data_merged = pd.concat([self.io_data_frs_lum,
                                    self.io_data_frs_ppp,
                                    self.io_data_ppp_ppp], axis=0).reset_index(drop=True)

        return io_data_merged

    def reformate_gfpmpt_data(self, target_data: pd.DataFrame, col_name: str, start_year: int):
        """
        Reformate TiMBA data to save aggregated data for each considered year in a separate column.
        :param target_data: Data which will be reformated
        :param col_name: Column name of the aggregated data which will be saved in a separate column
        :param start_year: Year from which data will be reformated
        :return pd.DataFrame: Reformated target_data
        """
        self.Logger.info(f'Reformate TiMBA Data to prepare growth rate calculations.')
        if 'GFPMpt_Comgroup' in target_data.columns:
            selected_col = [f'{self.linked_CGE}_{self.project}', 'GFPMpt_Comgroup', 'GTAP-Sector', f'{col_name}']

        elif ('GTAP-Sector' in target_data.columns) & ('GFPMpt_Comgroup' not in target_data.columns):
            selected_col = [f'{self.linked_CGE}_{self.project}', 'GTAP-Sector', f'{col_name}']

        elif ('input' in target_data.columns) & ('output' in target_data.columns):
            selected_col = [f'{self.linked_CGE}_{self.project}', 'input', 'output', f'{col_name}']

        else:
            selected_col = [f'{self.linked_CGE}_{self.project}', f'{col_name}']

        reformated_data = target_data[target_data['year'] == start_year][selected_col].reset_index(
            drop=True).rename(columns={f"{col_name}": start_year})

        year = start_year
        for key in self.exogenous_change_structure.keys():
            year += self.exogenous_change_structure[key][1]
            temp_reformated_data = pd.DataFrame(target_data[target_data['year'] == year][f'{col_name}']).reset_index(
                drop=True).rename(columns={f'{col_name}': year})
            reformated_data = pd.concat([reformated_data, temp_reformated_data], axis=1)

        return reformated_data

    def calc_growth_rate(self, target_data, start_year: int, end_year: int, link_type: bool):
        """
        Caluclate growth rate for target_data considering start_year and end_year.
        :param target_data: Data for which growth rates will be calculated
        :param start_year: Year from which growth rates will be calculated (for BioSDG-project = 2011)
        :param end_year: Year until which growth rates will be calculated
        :param link_type: flag allowing to chose if growth rates will be calculated for each period
        between start_year and end_year (flag = False) or solely considering start_year and end_year (flag = True).
        For the linkage DART-BIO-GFPMpt only the final value (in 2030) is linked. Therefore flag has to be True
        :return pd.DataFrame: Growth rates for target_data with chosen options
        """
        self.Logger.info(f'Calculate growth rate {target_data}.')
        if 'GTAP-Sector' in target_data.columns:
            selected_col = [f'{self.linked_CGE}_{self.project}', 'GTAP-Sector', start_year]
        elif ('input' in target_data.columns) & ('output' in target_data.columns):
            selected_col = [f'{self.linked_CGE}_{self.project}', 'input', 'output', start_year]
        else:
            selected_col = [f'{self.linked_CGE}_{self.project}', start_year]

        growth_rate = target_data[selected_col]
        if link_type == 'end_point':
            temp_growth_rate = pd.DataFrame((target_data[end_year] - target_data[start_year]) /
                                            target_data[start_year]).rename(columns={0: end_year})
            growth_rate = pd.concat([growth_rate, temp_growth_rate], axis=1)

        if link_type == 'continuous':
            year = start_year
            for key in self.exogenous_change_structure.keys():
                previous_year = year
                year += self.exogenous_change_structure[key][1]
                temp_growth_rate = pd.DataFrame((target_data[year] - target_data[previous_year]) /
                                                target_data[previous_year]).rename(columns={0: year})
                growth_rate = pd.concat([growth_rate, temp_growth_rate], axis=1)

        return growth_rate

    def generate_output_file_production(self, gams_readin_sheet: bool):
        """
        Generate Excel-Output-file storing all aggregated production related GFPMpt data and calculated growth rates.
        """
        self.Logger.info(f'Save aggregated production related TiMBA data in Excel-file.')
        # Excel-Writer
        writer_agg_data = pd.ExcelWriter(
            f'{self.sfile}\\data\\output\\{self.current_dt}_agg_production_data_{self.current_scenario}.xlsx',
            engine='xlsxwriter')

        if gams_readin_sheet:
            # Generate an index sheet for GAMS (necessary for readin-process of GAMS-based CGE, if GFPMpt is linked with
            # other CGE models, following part can be removed or adapted to the new linked model)
            index_info = {
                '': ['', '', '', 'rdim', 'cdim'],
                1: ['par', 'rel_quantities', 'rel_quantities!A2', 2, 0],
                2: ['par', 'rel_prices', 'rel_prices!A2', 2, 0],
                3: ['par', 'rel_values', 'rel_values!A2', 2, 0],
                4: ['par', 'rel_share_energy_use', 'rel_share_energy_use!A1', 1, 1],
                5: ['par', 'abs_quantities',  'abs_quantities!A1', 2, 1],
                6: ['par', 'abs_prices', 'abs_prices!A1', 2, 1],
                7: ['par', 'abs_values', 'abs_values!A1', 2, 1],
                8: ['par', 'abs_share_energy_use', 'abs_share_energy_use!A1', 1, 1]
            }
            index_info = pd.DataFrame.from_dict(data=index_info, orient='index').rename(
                columns={0: 'Type', 1: 'Name', 2: 'Location', 3: 'Row', 4: 'Column'})
            index_info.to_excel(writer_agg_data, sheet_name='index', index=False)

        # Generate info-sheet
        output_info = {
            'Title': ['Aggregated TiMBA results for production quantities, prices, and values', ],
            'Project': [f'{self.project}', ],
            'Linked CGE': [f'{self.linked_CGE}', ],
            'Input': [f'{self.input_path_timba}', ],
            'Scenario': [f'{self.current_scenario}', ],
            'Date': [f'{self.current_dt}', ],
            'abs_quantities': [f'Absolute projected production quantities', '[Tsd. m³ or t]'],
            'rel_quantities': [f'Relative changes in projected production quantities', '[yearly %-changes]'],
            'abs_prices': [f'Absolute projected prices', '[monetary unit/volume unit]'],
            'rel_prices': [f'Relative changes in projected prices', '[yearly %-changes]'],
            'abs_values': [f'Absolute projected values', '[monetary unit]'],
            'rel_values': [f'Relative changes in projected values', '[yearly %-changes]'],
            'abs_share_energy_use': [f'Absolute shares of FRS for energy use', '[%]'],
            'rel_share_energy_use': [f'Relative changes in shares of FRS for energy use', '[yearly %-changes]'],
        }
        output_info = pd.DataFrame.from_dict(data=output_info, orient='index').rename(columns={0: 'Metadata',
                                                                                               1: 'Units'})
        output_info.to_excel(writer_agg_data, sheet_name='Metadata')

        self.agg_production_data.to_excel(writer_agg_data, sheet_name='abs_quantities', index=False)
        self.growth_rate_production_data.to_excel(writer_agg_data, sheet_name='rel_quantities', index=False)

        self.agg_price_data.to_excel(writer_agg_data, sheet_name='abs_prices', index=False)
        self.growth_rate_price_data.to_excel(writer_agg_data, sheet_name='rel_prices', index=False)

        self.agg_value_data.to_excel(writer_agg_data, sheet_name='abs_values', index=False)
        self.growth_rate_value_data.to_excel(writer_agg_data, sheet_name='rel_values', index=False)

        self.share_energy_use.to_excel(writer_agg_data, sheet_name='abs_share_energy_use', index=False)
        self.growth_share_energy_use.to_excel(writer_agg_data, sheet_name='rel_share_energy_use', index=False)

        writer_agg_data.save()

    def generate_output_file_forest(self, gams_readin_sheet: bool):
        """
        Generate Excel-Output-file storing all aggregated forest related TiMBA data and calculated growth rates.
        """
        self.Logger.info(f'Save aggregated forest related TiMBA data in Excel-file.')

        # Excel-Writer
        writer_forest = pd.ExcelWriter(
            f'{self.sfile}\\data\\output\\{self.current_dt}_agg_forest_data_{self.current_scenario}.xlsx',
            engine='xlsxwriter')

        if gams_readin_sheet:
            # Generate an index sheet for GAMS (necessary for readin-process of GAMS-based CGE, if GFPMpt is linked with
            # other CGE models, following part can be removed or adapted to the new linked model)
            index_info = {
                '': ['', '', '', 'rdim', 'cdim'],
                1: ['par', 'rel_forest_area', 'rel_forest_area!A2', 1, 0],
                2: ['par', 'rel_harvest_intensity', 'rel_harvest_intensity!A2', 1, 0],

            }
            index_info = pd.DataFrame.from_dict(data=index_info, orient='index').rename(
                columns={0: 'Type', 1: 'Name', 2: 'Location', 3: 'Row', 4: 'Column'})
            index_info.to_excel(writer_forest, sheet_name='index', index=False)

        # Generate info-sheet
        data_info = {
            'Title': ['Aggregated TiMBA Results for forest development', ],
            'Project': [f'{self.project}', ],
            'Linked CGE': [f'{self.linked_CGE}', ],
            'Input': [f'{self.input_path_timba}', ],
            'Scenario': [f'{self.current_scenario}', ],
            'Date': [f'{self.current_dt}', ],
            'abs_forest_area': ['Absolute projected forest area', '[Tsd. ha]'],
            'rel_forest_area': ['Relative changes in projected forest area', '[yearly %-changes]'],
            'abs_forest_stock': ['Absolute projected forest stock', '[Mio. VFm]'],
            'rel_forest_stock': ['Relative changes in projected forest stock', '[yearly %-changes]'],
            'abs_harvest': ['Absolute projected harvest volumes', '[EFm]'],
            'rel_harvest': ['Relative changes in projected harvest volumes', '[yearly %-changes]'],
            'abs_harvest_intensity': ['Absolute projected harvest intensity', '[EFm/ha]'],
            'rel_harvest_intensity': ['Relative changes in projected harvest intensity', '[yearly %-changes]']
        }
        data_info = pd.DataFrame.from_dict(data=data_info, orient='index').rename(columns={0: 'Metadata', 1: 'Units'})
        data_info.to_excel(writer_forest, sheet_name='Metadata')

        self.agg_forest_area.to_excel(writer_forest, sheet_name='abs_forest_area', index=False)
        self.growth_forest_area.to_excel(writer_forest, sheet_name='rel_forest_area', index=False)
        self.agg_forest_stock.to_excel(writer_forest, sheet_name='abs_forest_stock', index=False)
        self.growth_forest_stock.to_excel(writer_forest, sheet_name='rel_forest_stock', index=False)
        self.agg_harvest_data.to_excel(writer_forest, sheet_name='abs_harvest', index=False)
        self.growth_harvest_data.to_excel(writer_forest, sheet_name='rel_harvest', index=False)
        self.agg_harvest_intensity.to_excel(writer_forest, sheet_name='abs_harvest_intensity', index=False)
        self.growth_harvest_intensity.to_excel(writer_forest, sheet_name='rel_harvest_intensity', index=False)
        writer_forest.save()

    def generate_output_file_carbon(self, gams_readin_sheet: bool):
        """
        Generate Excel-Output-file storing all aggregated carbon related TiMBA data and calculated growth rates.
        """
        self.Logger.info(f'Save aggregated carbon related TiMBA data in Excel-file.')
        # Excel-Writer
        writer_carbon_data = pd.ExcelWriter(
            f'{self.sfile}\\data\\output\\{self.current_dt}_agg_carbon_data_{self.current_scenario}.xlsx',
            engine='xlsxwriter')

        if gams_readin_sheet:
            # Generate an index sheet for GAMS (necessary for readin-process of GAMS-based CGE, if GFPMpt is linked with
            # other CGE models, following part can be removed or adapted to the new linked model)
            index_info = {
                '': ['', '', '', 'rdim', 'cdim'],
                1: ['par', 'rel_carbon_stock_biomass', 'rel_carbon_stock_biomass!A2', 1, 0],
                2: ['par', 'rel_carbon_stock_hwp', 'rel_carbon_stock_hwp!A2', 1, 0],

            }
            index_info = pd.DataFrame.from_dict(data=index_info, orient='index').rename(
                columns={0: 'Type', 1: 'Name', 2: 'Location', 3: 'Row', 4: 'Column'})
            index_info.to_excel(writer_carbon_data, sheet_name='index', index=False)

        # Generate info-sheet
        data_info = {
            'Title': ['Aggregated carbon stocks for biomass and HWP', ],
            'Project': [f'{self.project}', ],
            'Linked CGE': [f'{self.linked_CGE}', ],
            'Input': [f'{self.input_path_timba}', ],
            'Scenario': [f'{self.current_scenario}', ],
            'Date': [f'{self.current_dt}', ],
            'abs_carbon_stock_biomass': [f'Absolute carbon stocks in biomass (agb + bgb)', '[MtC]'],
            'rel_carbon_stock_biomass': [f'Relative changes in projected carbon stocks of biomass',
                                         '[yearly %-changes]'],
            'abs_carbon_stock_hwp': [f'Absolute carbon stocks in hwp', '[MtC]'],
            'rel_carbon_stock_hwp': [f'Relative changes in projected carbon stocks of hwp', '[yearly %-changes]'],
        }
        data_info = pd.DataFrame.from_dict(data=data_info, orient='index').rename(columns={0: 'Metadata', 1: 'Units'})
        data_info.to_excel(writer_carbon_data, sheet_name='Metadata')
        self.agg_carbon_biomass.to_excel(writer_carbon_data, sheet_name='abs_carbon_stock_biomass', index=False)
        self.growth_carbon_biomass.to_excel(writer_carbon_data, sheet_name='rel_carbon_stock_biomass', index=False)
        self.agg_carbon_hwp.to_excel(writer_carbon_data, sheet_name='abs_carbon_stock_hwp', index=False)
        self.growth_carbon_hwp.to_excel(writer_carbon_data, sheet_name='rel_carbon_stock_hwp', index=False)
        writer_carbon_data.save()

    def generate_output_file_io(self, gams_readin_sheet: bool):
        """
        Generate Excel-Output-file storing all aggregated IO-related TiMBA data and calculated growth rates.
        """
        self.Logger.info(f'Save aggregated io related TiMBA data in Excel-file.')
        # Excel-Writer
        writer_io_data = pd.ExcelWriter(
            f'{self.sfile}\\data\\output\\{self.current_dt}_agg_io_data_{self.current_scenario}.xlsx',
            engine='xlsxwriter')

        if gams_readin_sheet:
            # Generate an index sheet for GAMS (necessary for readin-process of GAMS-based CGE, if GFPMpt is linked with
            # other CGE models, following part can be removed or adapted to the new linked model)
            index_info = {
                '': ['', '', '', 'rdim', 'cdim'],
                1: ['par', 'rel_io_data', 'rel_io_data!A2', 3, 0],

            }
            index_info = pd.DataFrame.from_dict(data=index_info, orient='index').rename(
                columns={0: 'Type', 1: 'Name', 2: 'Location', 3: 'Row', 4: 'Column'})
            index_info.to_excel(writer_io_data, sheet_name='index', index=False)

        # Generate info-sheet
        data_info = {
            'Title': ['Aggregated input-output coefficients', ],
            'Project': [f'{self.project}', ],
            'Linked CGE': [f'{self.linked_CGE}', ],
            'Input': [f'{self.input_path_timba}', ],
            'Scenario': [f'{self.current_scenario}', ],
            'Date': [f'{self.current_dt}', ],
            'abs_io_data': [f'necessary input to produce one unit of output', 'non'],
            'rel_io_data': [f'Relative changes in input-output coefficients', '[yearly %-changes]'],
        }
        data_info = pd.DataFrame.from_dict(data=data_info, orient='index').rename(columns={0: 'Metadata', 1: 'Units'})
        data_info.to_excel(writer_io_data, sheet_name='Metadata')
        self.io_data_agg.to_excel(writer_io_data, sheet_name='abs_io_data', index=False)
        self.growth_io_data.to_excel(writer_io_data, sheet_name='rel_io_data', index=False)
        writer_io_data.save()

    def main_aggregation_pipeline(self, domains_to_aggregate: list):
        Pipeline_Agg = AggregateTiMBAResults(
            current_scenario=self.current_scenario,
            input_path_timba=self.input_path_timba,
            link_typ=self.link_typ,  # Alternatives: 'continuous', 'end_point'
            linked_CGE=self.linked_CGE,  # Alternatives: 'DART-BIO', 'MAGNET'
            project=self.project  # Alternatives: 'BioSDG', 'CarbonLeak', 'BEPASO'
            # Note: linked_CGE and project must be harmonized (e.g., DART-BIO + BioSDG)
            )

        if 'production' in domains_to_aggregate:
            (Pipeline_Agg.agg_production_data,
             Pipeline_Agg.production_data) = Pipeline_Agg.aggregate_production_data(intermediate_aggregation=False)
            Pipeline_Agg.agg_price_data = Pipeline_Agg.agg_price_data()
            Pipeline_Agg.agg_value_data = Pipeline_Agg.agg_value_data()
            Pipeline_Agg.share_energy_use = Pipeline_Agg.share_energy_material_use()

            Pipeline_Agg.agg_production_data = Pipeline_Agg.reformate_gfpmpt_data(
                target_data=Pipeline_Agg.agg_production_data,
                col_name='quantity',
                start_year=Pipeline_Agg.start_year)
            Pipeline_Agg.agg_price_data = Pipeline_Agg.reformate_gfpmpt_data(
                target_data=Pipeline_Agg.agg_price_data,
                col_name='price',
                start_year=Pipeline_Agg.start_year)
            Pipeline_Agg.agg_value_data = Pipeline_Agg.reformate_gfpmpt_data(
                target_data=Pipeline_Agg.agg_value_data,
                col_name='value',
                start_year=Pipeline_Agg.start_year)
            Pipeline_Agg.share_energy_use = Pipeline_Agg.reformate_gfpmpt_data(
                target_data=Pipeline_Agg.share_energy_use,
                col_name='share_energy_use',
                start_year=Pipeline_Agg.start_year)
            Pipeline_Agg.growth_rate_price_data = Pipeline_Agg.calc_growth_rate(
                target_data=Pipeline_Agg.agg_price_data,
                start_year=Pipeline_Agg.start_year,
                end_year=Pipeline_Agg.end_year,
                link_type=Pipeline_Agg.link_typ)
            Pipeline_Agg.growth_rate_value_data = Pipeline_Agg.calc_growth_rate(
                target_data=Pipeline_Agg.agg_value_data,
                start_year=Pipeline_Agg.start_year,
                end_year=Pipeline_Agg.end_year,
                link_type=Pipeline_Agg.link_typ)
            Pipeline_Agg.growth_rate_production_data = Pipeline_Agg.calc_growth_rate(
                target_data=Pipeline_Agg.agg_production_data,
                start_year=Pipeline_Agg.start_year,
                end_year=Pipeline_Agg.end_year,
                link_type=Pipeline_Agg.link_typ)
            Pipeline_Agg.growth_share_energy_use = Pipeline_Agg.calc_growth_rate(
                target_data=Pipeline_Agg.share_energy_use,
                start_year=Pipeline_Agg.start_year,
                end_year=Pipeline_Agg.end_year,
                link_type=Pipeline_Agg.link_typ)

            Pipeline_Agg.generate_output_file_production(gams_readin_sheet=True)

        if 'forest' in domains_to_aggregate:
            Pipeline_Agg.agg_forest_stock, Pipeline_Agg.agg_forest_area = Pipeline_Agg.agg_forest_data()
            Pipeline_Agg.agg_harvest_data = Pipeline_Agg.agg_harvest_data()
            Pipeline_Agg.agg_harvest_intensity = Pipeline_Agg.calc_harvest_intensity()
            Pipeline_Agg.agg_forest_stock = Pipeline_Agg.reformate_gfpmpt_data(
                target_data=Pipeline_Agg.agg_forest_stock,
                col_name='ForStock',
                start_year=Pipeline_Agg.start_year)
            Pipeline_Agg.agg_forest_area = Pipeline_Agg.reformate_gfpmpt_data(
                target_data=Pipeline_Agg.agg_forest_area,
                col_name='ForArea',
                start_year=Pipeline_Agg.start_year)
            Pipeline_Agg.agg_harvest_data = Pipeline_Agg.reformate_gfpmpt_data(
                target_data=Pipeline_Agg.agg_harvest_data,
                col_name='quantity',
                start_year=Pipeline_Agg.start_year)
            Pipeline_Agg.agg_harvest_intensity = Pipeline_Agg.reformate_gfpmpt_data(
                target_data=Pipeline_Agg.agg_harvest_intensity,
                col_name='harvest_intensity',
                start_year=Pipeline_Agg.start_year)
            Pipeline_Agg.growth_forest_stock = Pipeline_Agg.calc_growth_rate(
                target_data=Pipeline_Agg.agg_forest_stock,
                start_year=Pipeline_Agg.start_year,
                end_year=Pipeline_Agg.end_year,
                link_type=Pipeline_Agg.link_typ)
            Pipeline_Agg.growth_forest_area = Pipeline_Agg.calc_growth_rate(
                target_data=Pipeline_Agg.agg_forest_area,
                start_year=Pipeline_Agg.start_year,
                end_year=Pipeline_Agg.end_year,
                link_type=Pipeline_Agg.link_typ)
            Pipeline_Agg.growth_harvest_data = Pipeline_Agg.calc_growth_rate(
                target_data=Pipeline_Agg.agg_harvest_data,
                start_year=Pipeline_Agg.start_year,
                end_year=Pipeline_Agg.end_year,
                link_type=Pipeline_Agg.link_typ)
            Pipeline_Agg.growth_harvest_intensity = Pipeline_Agg.calc_growth_rate(
                target_data=Pipeline_Agg.agg_harvest_intensity,
                start_year=Pipeline_Agg.start_year,
                end_year=Pipeline_Agg.end_year,
                link_type=Pipeline_Agg.link_typ)
            Pipeline_Agg.generate_output_file_forest(gams_readin_sheet=True)

        if 'carbon' in domains_to_aggregate:
            Pipeline_Agg.agg_carbon_biomass, Pipeline_Agg.agg_carbon_hwp = Pipeline_Agg.agg_carbon_data()
            Pipeline_Agg.agg_carbon_biomass = Pipeline_Agg.reformate_gfpmpt_data(
                target_data=Pipeline_Agg.agg_carbon_biomass,
                col_name='CarbonStockBiomass [MtCO2]',
                start_year=Pipeline_Agg.start_year)
            Pipeline_Agg.agg_carbon_hwp = Pipeline_Agg.reformate_gfpmpt_data(
                target_data=Pipeline_Agg.agg_carbon_hwp,
                col_name='CarbonStockHWP [MtCO2]',
                start_year=Pipeline_Agg.start_year)
            Pipeline_Agg.growth_carbon_biomass = Pipeline_Agg.calc_growth_rate(
                target_data=Pipeline_Agg.agg_carbon_biomass,
                start_year=Pipeline_Agg.start_year,
                end_year=Pipeline_Agg.end_year,
                link_type=Pipeline_Agg.link_typ)
            Pipeline_Agg.growth_carbon_hwp = Pipeline_Agg.calc_growth_rate(
                target_data=Pipeline_Agg.agg_carbon_biomass,
                start_year=Pipeline_Agg.start_year,
                end_year=Pipeline_Agg.end_year,
                link_type=Pipeline_Agg.link_typ)
            Pipeline_Agg.generate_output_file_carbon(gams_readin_sheet=True)

        if 'io' in domains_to_aggregate:

            Pipeline_Agg.io_data = Pipeline_Agg.process_io_data()
            Pipeline_Agg.io_data_frs_lum = Pipeline_Agg.calc_io_frs_lum(weighted_io=True)
            Pipeline_Agg.io_data_frs_ppp = Pipeline_Agg.calc_io_frs_ppp(weighted_io=True)
            Pipeline_Agg.io_data_ppp_ppp = Pipeline_Agg.calc_io_ppp_ppp(weighted_io=True)
            Pipeline_Agg.io_data_agg = Pipeline_Agg.merge_io_data()

            Pipeline_Agg.io_data_agg = Pipeline_Agg.reformate_gfpmpt_data(
                target_data=Pipeline_Agg.io_data_agg,
                col_name='ManuFakt',
                start_year=Pipeline_Agg.start_year)

            Pipeline_Agg.growth_io_data = Pipeline_Agg.calc_growth_rate(target_data=Pipeline_Agg.io_data_agg,
                                                                        start_year=Pipeline_Agg.start_year,
                                                                        end_year=Pipeline_Agg.end_year,
                                                                        link_type=Pipeline_Agg.link_typ)

            Pipeline_Agg.generate_output_file_io(gams_readin_sheet=True)

            # Test calculations of IOs with quantities (Problem: calculations assume unique output group for each input.
            # This is not the case in TiMBA)
            """(Pipeline_Agg.interm_agg_production_data,
             Pipeline_Agg.production_data) = Pipeline_Agg.aggregate_production_data(
                intermediate_aggregation=True)
            Pipeline_Agg.io_frs_lum = Pipeline_Agg.calc_input_frs_lum(
                target_data=Pipeline_Agg.interm_agg_production_data,
                start_year=Pipeline_Agg.start_year)
            Pipeline_Agg.io_frs_ppp = Pipeline_Agg.calc_input_frs_ppp(
                target_data=Pipeline_Agg.interm_agg_production_data,
                start_year=Pipeline_Agg.start_year)
            Pipeline_Agg.io_ppp_ppp = Pipeline_Agg.calc_input_ppp_ppp(
                target=Pipeline_Agg.interm_agg_production_data,
                start_year=Pipeline_Agg.start_year)"""

        Pipeline_Agg.Logger.info(f'This link is unbreakable.')
