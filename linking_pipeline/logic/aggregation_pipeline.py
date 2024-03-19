# -----------------------------------------------------
# GFPMpt_linking_pipeline - aggregation_pipeline (Tomke Honkomp (TH) - Thuenen-Institut)
# GFPMpt-output aggregation to selected CGE (spatial and sectoral aggregation)
# Status: 03.2024
# Last update: 03.2024
# -----------------------------------------------------

# imports
import pandas as pd
import numpy as np
import os
from pathlib import Path
import datetime as dt
from linking_pipeline.helper_functions.base_logger import get_logger


class AggregateGFPMptResults(object):
    def __init__(self,
                 current_scenario: str,
                 input_path_gfpmpt: str,
                 link_typ: str,
                 linked_CGE: str,
                 project: str
                 ):
        self.sfile = os.path.dirname(Path(__file__).resolve().parents[0])
        self.Logger = get_logger(user_path=None, aggregation_flag=True)
        self.current_scenario = current_scenario
        self.current_dt = dt.datetime.now().strftime("%Y%m%d")
        self.input_path_gfpmpt = input_path_gfpmpt
        self.link_typ = link_typ
        self.linked_CGE = linked_CGE
        self.project = project
        self.gfpmpt_data = AggregateGFPMptResults.readin_model_data(self)
        (self.region_key,
         self.commodity_key,
         self.exogenous_change_structure) = AggregateGFPMptResults.readin_help_data(self)

    def readin_model_data(self):
        """
        Read in GFPMpt-data for production (ManufactureCost and Supply)
        :return pd.DataFrame: GFPMpt-data
        """
        self.Logger.info(f"Read in GFPMpt results {self.input_path_gfpmpt}.")
        import pickle
        src_path = f'{self.sfile}\\data\\input\\{self.input_path_gfpmpt}.pkl'
        with open(src_path, "rb") as pkl_file:
            gfpmpt_data = pickle.load(pkl_file)
        return gfpmpt_data

    def readin_help_data(self):
        """
        Read in help data used for the aggregation to DART-BIO-sectors (commodity_key) and to DART-BIO-regions
        (region_key). Exogenous_change_structure stores information about the number of periods and the length of each
         period
        :return: help data in different types (pd.DataFrame and dict)
        """
        self.Logger.info(f"Read in help data.")
        # todo move to a central place and use for all scripts as Enum class
        com_info_16 = {"GFPMpt_Comcode": [78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 90, 91, 92, 93],
                       "GFPMpt_Comgroup": ["TR", "S", "F", "TR", "TR", "S", "WBP", "WBP", "WBP", "MP", "CP", "TPP",
                                           "TPP", "TPP", "TPP"],
                       "GTAP-Sector": ["FRS", "LUM", "BIOE", "FRS", "FRS", "LUM", "LUM", "LUM", "LUM", "PPP", "PPP",
                                       "PPP", "PPP", "PPP", "PPP"]}
        com_info_14 = {"GFPMpt_Comcode": [80, 81, 82, 83, 84, 85, 86, 87, 88, 90, 91, 92, 93],
                       "GFPMpt_Comgroup": ["F", "TR", "TR", "S", "WBP", "WBP", "WBP", "MP", "CP", "TPP",
                                           "TPP", "TPP", "TPP"],
                       "GTAP-Sector": ["BIOE", "FRS", "FRS", "LUM", "LUM", "LUM", "LUM", "PPP", "PPP",
                                       "PPP", "PPP", "PPP", "PPP"]}

        gfpmpt_commodities = self.gfpmpt_data['data_periods']['CommodityCode'].unique()

        if len(gfpmpt_commodities) == 16:
            commodity_key = pd.DataFrame.from_dict(com_info_16)
        if len(gfpmpt_commodities) == 14:
            commodity_key = pd.DataFrame.from_dict(com_info_14)

        region_key = pd.ExcelFile(f'{self.sfile}\\data\\input\\m_Country.xlsx')
        region_key = region_key.parse('m_Country')
        region_key = region_key[['GFPM_CountryCode', 'GTAP10', f'{self.linked_CGE}_{self.project}']]

        exogenous_change_data = self.gfpmpt_data['data_periods'][
            ['Period', 'year']].drop_duplicates().reset_index(drop=True)

        exogenous_change_structure = {}
        year_prev = exogenous_change_data['year'][0]
        for period in exogenous_change_data['Period'][1:]:
            index = exogenous_change_data[exogenous_change_data['Period'] == period]['year'].index[0]
            year = exogenous_change_data[exogenous_change_data['Period'] == period]['year'][index]
            period_len = year - year_prev
            exogenous_change_structure[f'Period_{period}'] = [year_prev, period_len]
            year_prev = year

        """exogenous_change_structure = {
            "Period_1": 4,
            "Period_2": 5,
            "Period_3": 5,
            "Period_4": 5}"""

        return region_key, commodity_key, exogenous_change_structure

    def agg_production_data(self):
        """
        Aggregate GFPMpt-data for production to DART-BIO-level in three steps.
        1. step: Aggregate GFPMpt-data for production by summing up supply and manufacturecost (production_data)
        2. step: Aggregate GFPMpt-data for production to DART-BIO-regions (region_production_data)
        3. step: Aggregate GFPMpt-data for production to DART-BIO-sectors (sector_production_data)
        :return: Aggregated production data to DART-BIO-level (region and sector)
        """
        self.Logger.info(f"Aggregate GFPMpt-data for production to {self.linked_CGE} (region and sector).")
        production_data = self.gfpmpt_data['data_periods']
        production_data = production_data[(production_data['domain'] == 'Supply') |
                                          (production_data['domain'] == 'ManufactureCost')]
        production_data = production_data.groupby(["RegionCode", "CommodityCode", "year"]
                                                  )["quantity"].sum().reset_index()

        production_data = production_data.merge(self.region_key, left_on="RegionCode", right_on="GFPM_CountryCode",
                                                how="left").dropna()

        region_production_data = production_data.groupby([f"{self.linked_CGE}_{self.project}", "CommodityCode", "year"
                                                          ])["quantity"].sum().reset_index()
        region_production_data = region_production_data.merge(self.commodity_key, left_on="CommodityCode",
                                                              right_on="GFPMpt_Comcode", how="left")
        sector_production_data = region_production_data.groupby([f"{self.linked_CGE}_{self.project}", "GTAP-Sector",
                                                                 "year"])["quantity"].sum().reset_index()
        return sector_production_data

    def agg_price_data(self):
        """
        Aggregate GFPMpt-data for product prices to DART-BIO-level in five steps. Aggregated prices are weighted using
        aggregated values and quantity.
        1. step: Aggregate GFPMpt-data for production and for price by summing up supply and manufacturecost
        (production_data and price_data)
        2. step: Calculate values (production quantity * prices)
        3. step: Aggregate GFPMpt-data for production and for values to DART-BIO-regions (region_production_data and
        region_value_data)
        4. step: Aggregate GFPMpt-data for production and for values to DART-BIO-sectors (sector_production_data and
        sector_value_data)
        5. step: Aggregate GFPMpt-data for prices as weighted prices using aggregated values and production.
        :return pd.DataFrame: Aggregated and weighted price data to DART-BIO-level (region and sector)
        """
        self.Logger.info(f"Aggregate GFPMpt-data for price to DART-BIO-level (region and sector).")
        price_data = self.gfpmpt_data.groupby(["RegionCode", "CommodityCode", "Year"]
                                              )["price"].sum().reset_index()
        production_data = self.gfpmpt_data.groupby(["RegionCode", "CommodityCode", "Year"]
                                                   )["quantity"].sum().reset_index()

        price_data = price_data.merge(self.region_key, left_on="RegionCode", right_on="GFPM_CountryCode",
                                      how="left").dropna()
        production_data = production_data.merge(self.region_key, left_on="RegionCode", right_on="GFPM_CountryCode",
                                                how="left").dropna()

        value_data = pd.concat([production_data[["RegionCode", "CommodityCode", "Year", "DART-BIO-Region"]],
                                pd.DataFrame(production_data["quantity"] * price_data["price"])],
                               axis=1).rename(columns={0: "value"})

        region_production_data = production_data.groupby(["DART-BIO-Region", "CommodityCode", "Year"
                                                          ])["quantity"].sum().reset_index()
        region_value_data = value_data.groupby(["DART-BIO-Region", "CommodityCode", "Year"
                                                ])["value"].sum().reset_index()

        region_production_data = region_production_data.merge(self.commodity_key, left_on="CommodityCode",
                                                              right_on="GFPMpt_Comcode",
                                                              how="left")

        region_value_data = region_value_data.merge(self.commodity_key, left_on="CommodityCode",
                                                    right_on="GFPMpt_Comcode",
                                                    how="left")

        sector_value_data = region_value_data.groupby(["DART-BIO-Region", "DART-BIO-Sector", "Year"
                                                       ])["value"].sum().reset_index()
        sector_production_data = region_production_data.groupby(["DART-BIO-Region", "DART-BIO-Sector", "Year"]
                                                                )["quantity"].sum().reset_index()

        sector_price_data = pd.DataFrame(sector_value_data["value"] / sector_production_data["quantity"]).rename(
            columns={0: "price"})

        sector_price_data = pd.concat([sector_production_data[["DART-BIO-Region", "DART-BIO-Sector", "Year"]],
                                       sector_price_data], axis=1)

        return sector_price_data

    def agg_value_data(self):
        """
        Aggregate GFPMpt-data for values to DART-BIO-level in three steps.
        1. step: Aggregate GFPMpt-data for production and for price by summing up supply and manufacturecost
        (production_data and price_data)
        2. step: Calculate values (production quantity * prices)
        2. step: Aggregate GFPMpt-data for values to DART-BIO-regions (region_value_data)
        3. step: Aggregate GFPMpt-data for values to DART-BIO-sectors (sector_value_data)
        :return: Aggregated value data to DART-BIO-level (region and sector)
        """
        self.Logger.info(f"Aggregate GFPMpt-data for value to DART-BIO-level (region and sector).")
        price_data = self.gfpmpt_data.groupby(["RegionCode", "CommodityCode", "Year"]
                                              )["price"].sum().reset_index()
        production_data = self.gfpmpt_data.groupby(["RegionCode", "CommodityCode", "Year"]
                                                   )["quantity"].sum().reset_index()

        price_data = price_data.merge(self.region_key, left_on="RegionCode", right_on="GFPM_CountryCode",
                                      how="left").dropna()
        production_data = production_data.merge(self.region_key, left_on="RegionCode", right_on="GFPM_CountryCode",
                                                how="left").dropna()

        value_data = pd.concat([production_data[["RegionCode", "CommodityCode", "Year", "DART-BIO-Region"]],
                                pd.DataFrame(production_data["quantity"] * price_data["price"])],
                               axis=1).rename(columns={0: "value"})
        region_value_data = value_data.groupby(["DART-BIO-Region", "CommodityCode", "Year"
                                                ])["value"].sum().reset_index()
        region_value_data = region_value_data.merge(self.commodity_key, left_on="CommodityCode",
                                                    right_on="GFPMpt_Comcode",
                                                    how="left")

        sector_value_data = region_value_data.groupby(["DART-BIO-Region", "DART-BIO-Sector", "Year"
                                                       ])["value"].sum().reset_index()

        return sector_value_data

    def reformate_gfpmpt_data(self, target_data: pd.DataFrame, col_name: str, start_year: int):
        """
        Reformate GFPMpt-data to save aggregated data for each considered year in a separate column.
        :param target_data: Data which will be reformated
        :param col_name: Column name of the aggregated data which will be saved in a separate column
        :param start_year: Year from which data will be reformated
        :return pd.DataFrame: Reformated target_data
        """
        self.Logger.info(f"Reformate GFPMpt-Data to prepare growth rate calculations.")
        reformated_data = target_data[
            target_data["Year"] == start_year][["DART-BIO-Region", "DART-BIO-Sector", f"{col_name}"]
        ].reset_index(drop=True).rename(columns={f"{col_name}": start_year})

        year = start_year
        for key in self.exogenous_change_structure.keys():
            year += self.exogenous_change_structure[key]
            temp_reformated_data = pd.DataFrame(target_data[target_data["Year"] == year][f"{col_name}"]).reset_index(
                drop=True).rename(columns={f"{col_name}": year})
            reformated_data = pd.concat([reformated_data, temp_reformated_data], axis=1)

        return reformated_data

    def calc_growth_rate(self, target_data, start_year: int, end_year: int, flag_no_intermediate_periods: bool):
        """
        Caluclate growth rate for target_data considering start_year and end_year.
        :param target_data: Data for which growth rates will be calculated
        :param start_year: Year from which growth rates will be calculated (for BioSDG-project = 2011)
        :param end_year: Year until which growth rates will be calculated
        :param flag_no_intermediate_periods: flag allowing to chose if growth rates will be calculated for each period
        between start_year and end_year (flag = False) or solely considering start_year and end_year (flag = True).
        For the linkage DART-BIO-GFPMpt only the final value (in 2030) is linked. Therefore flag has to be True
        :return pd.DataFrame: Growth rates for target_data with chosen options
        """
        self.Logger.info(f"Calculate growth rate {target_data}.")
        growth_rate = target_data[["DART-BIO-Region", "DART-BIO-Sector", start_year]]
        if flag_no_intermediate_periods:
            temp_growth_rate = pd.DataFrame((target_data[end_year] - target_data[start_year]) /
                                            target_data[start_year]).rename(columns={0: end_year})
            growth_rate = pd.concat([growth_rate, temp_growth_rate], axis=1)

        else:
            year = start_year
            for key in self.exogenous_change_structure.keys():
                previous_year = year
                year += self.exogenous_change_structure[key]
                temp_growth_rate = pd.DataFrame((target_data[year] - target_data[previous_year]) /
                                                target_data[previous_year]).rename(columns={0: year})
                growth_rate = pd.concat([growth_rate, temp_growth_rate], axis=1)

        return growth_rate

    def generate_output_file(self, end_year: int):
        """
        Generate Excel-Output-file storing all aggregated GFPMpt-data and calculated growth rates.
        """
        self.Logger.info(f"Save aggregated GFPMpt-data in Excel-file.")
        # Excel-Writer
        writer_agg_data = pd.ExcelWriter(
            f'%s\\output\\{self.current_dt}_agg_data_{self.current_scenario}.xlsx' % self.sfile,
            engine="xlsxwriter")

        # Generate index-sheet (necessary for readin-process of DART-BIO, if GFPMpt is linked with other CGE models,
        # following part can be removed or adapted to the new linked model)

        index_info = {
            "": ["", "", "", "rdim", "cdim"],
            1: ["par", "rel_quantities", "rel_quantities!B2", 2, 0],
            2: ["par", "rel_prices", "rel_prices!B2", 2, 0],
            3: ["par", "rel_values", "rel_values!B2", 2, 0],
            4: ["par", "abs_quantities",  "abs_quantities!B1", 2, 1],
            5: ["par", "abs_prices", "abs_prices!B1", 2, 1],
            6: ["par", "abs_values", "abs_values!B1", 2, 1]
        }
        index_info = pd.DataFrame.from_dict(data=index_info, orient="index").rename(
            columns={0: "Type", 1: "Name", 2: "Location", 3: "Row", 4: "Column"})
        index_info.to_excel(writer_agg_data, sheet_name="index", index=False)
        # can be remove until here

        # Generate info-sheet
        output_info = {
            "Title": ["Aggregated pytiGFPM-Results for production quantities and prices", ],
            "Input": [f"{self.input_path_gfpmpt}", ],
            "Scenario": [f"{self.current_scenario}", ],
            "Date": [f"{self.current_dt}", ],
            "abs_quantities": ["Absolute projected production quantities (DART-BIO-Aggregates)", "[Tsd. m³ or t]"],
            "rel_quantities": ["Relative changes in projected production quantities (DART-BIO-Aggregates)",
                               "[yearly %-changes]"],
            "abs_prices": ["Absolute projected prices (DART-BIO-Aggregates)", "[monetary unit/volume unit]"],
            "rel_prices": ["Relative changes in projected prices (DART-BIO-Aggregates)", "[yearly %-changes]"],
            "abs_values": ["Absolute projected values (DART-BIO-Aggregates)", "[monetary unit]"],
            "rel_values": ["Relative changes in projected values (DART-BIO-Aggregates)", "[yearly %-changes]"]
        }
        output_info = pd.DataFrame.from_dict(data=output_info, orient="index").rename(columns={0: "Data_info", 1: "Units"})
        output_info.to_excel(writer_agg_data, sheet_name="Data_info")

        self.agg_production_data.to_excel(writer_agg_data, sheet_name="abs_quantities")
        self.growth_rate_production_data[["DART-BIO-Region",
                                          "DART-BIO-Sector",
                                          end_year]].to_excel(writer_agg_data, sheet_name="rel_quantities")

        self.agg_price_data.to_excel(writer_agg_data, sheet_name="abs_prices")
        self.growth_rate_price_data[["DART-BIO-Region",
                                     "DART-BIO-Sector",
                                     end_year]].to_excel(writer_agg_data, sheet_name="rel_prices")

        self.agg_value_data.to_excel(writer_agg_data, sheet_name="abs_values")
        self.growth_rate_value_data[["DART-BIO-Region",
                                     "DART-BIO-Sector",
                                     end_year]].to_excel(writer_agg_data, sheet_name="rel_values")
        writer_agg_data.save()


if __name__ == '__main__':
    Pipeline_Agg = AggregateGFPMptResults(current_scenario='linkage_pipeline_test',
                                          input_path_gfpmpt='DataContainer_Sc_20240227_Updated_World_2015_only_SSP2',
                                          link_typ='continous',  # Alternatives: 'continous', 'end_point'
                                          linked_CGE='MAGNET',  # Alternatives: 'DART-BIO', 'MAGNET'
                                          project='CarbonLeak'    # Alternatives: 'BioSDG', 'CarbonLeak', 'BEPASO'
                                          # Note: linked_CGE and project must be harmonized (e.g., DART-BIO + BioSDG)
                                          )
    # Utilization notice adapt AggregationGFPMForest() to readin new input files:
    # input_path_gfpmt corresponds to the file name of the result-output file form GFPMpt

    Pipeline_Agg.agg_production_data = Pipeline_Agg.agg_production_data()
    Pipeline_Agg.agg_price_data = Pipeline_Agg.agg_price_data()
    Pipeline_Agg.agg_value_data = Pipeline_Agg.agg_value_data()

    Pipeline_Agg.agg_production_data = Pipeline_Agg.reformate_gfpmpt_data(target_data=Pipeline_Agg.agg_production_data,
                                                                          col_name="quantity",
                                                                          start_year=2011)
    Pipeline_Agg.agg_price_data = Pipeline_Agg.reformate_gfpmpt_data(target_data=Pipeline_Agg.agg_price_data,
                                                                     col_name="price",
                                                                     start_year=2011)
    Pipeline_Agg.agg_value_data = Pipeline_Agg.reformate_gfpmpt_data(target_data=Pipeline_Agg.agg_value_data,
                                                                     col_name="value",
                                                                     start_year=2011)
    Pipeline_Agg.growth_rate_price_data = Pipeline_Agg.calc_growth_rate(
        target_data=Pipeline_Agg.agg_price_data,
        start_year=2011,
        end_year=2030,
        flag_no_intermediate_periods=True)
    Pipeline_Agg.growth_rate_value_data = Pipeline_Agg.calc_growth_rate(
        target_data=Pipeline_Agg.agg_value_data,
        start_year=2011,
        end_year=2030,
        flag_no_intermediate_periods=True)
    Pipeline_Agg.growth_rate_production_data = Pipeline_Agg.calc_growth_rate(
        target_data=Pipeline_Agg.agg_production_data,
        start_year=2011,
        end_year=2030,
        flag_no_intermediate_periods=True)

    Pipeline_Agg.generate_output_file(end_year=2030)
