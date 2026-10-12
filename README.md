![TiMBA_Link](https://github.com/TI-Forest-Sector-Modelling/TiMBA_Link/blob/main/TiMBA_Link_logo_v1.png?raw=true)

# TiMBA_Link

![GitHub Release](https://img.shields.io/github/v/release/TI-Forest-Sector-Modelling/TiMBA_Link)
[![License](https://img.shields.io/github/license/TI-Forest-Sector-Modelling/TiMBA_Link)](https://github.com/TI-Forest-Sector-Modelling/TiMBA_Link/blob/main/COPYING)

--------------

<!-- TOC -->
- [Description](#description)
- [Citation](#citation)
- [Installation](#installation)
- [Usage](#usage)
- [Data processing](#data-processing)
  - [Data aggregation](#data-aggregation)
  - [Data disaggregation](#data-disaggregation) 
- [Support](#support)
- [Project status and Roadmap](#project-status-and-roadmap)
- [Contributing](#contributing)
- [Authors](#authors-and-acknowledgment)
- [License](#license)
<!-- TOC -->

--------------

## Description
This project is an add-on application to the [Timber market Model for policy-Based Analysis](https://github.com/TI-Forest-Sector-Modelling/TiMBA) (TiMBA).
As part of TiMBA-ecosystem (see [Figure 1](https://github.com/TI-Forest-Sector-Modelling/TiMBA_Additional_Information/blob/main/images/TiMBA_planned_workflow.png)),
the application automates the linkage between TiMBA and other models to enhance the representation of key dimensions (e.g., socioeconomic and biophysical components) beyond TiMBA's original focus. 
In turn, linking with TiMBA enables a more detailed representation of forest-related market and resource dynamics in other modelling frameworks, such as computable general equilibrium (CGE) ([Delzeit et al., 2020](https://doi.org/10.21642/JGEA.050105AF)). 
An improved representation of forest sector dynamics is essential for addressing research questions related to climate change ([Pan et al. 2011](https://doi.org/10.1126/science.1201609), [2024](https://doi.org/10.1038/s41586-024-07602-x)),
the bioeconomy ([Pfeiffer et al. 2026](https://doi.org/10.1007/s10113-025-02502-w)), and biodiversity ([Betts et al. 2017](https://doi.org/10.1038/nature23285)).
This so-called *soft linkage* is operationalised through the exchange of selected variables, which are endogenously determined within one of the linked models ([Delzeit et al. 2020](https://jgea.org/ojs/index.php/jgea/article/view/93)).


While the project has been developed to link TiMBA with different CGE models (e.g., [DART-BIO](https://www.kielinstitut.de/institute/research-centers/global-transformation/global-commons-and-climate-policy/dynamic-applied-regional-trade-model-dart/dart-bio/), [MAGNET](https://www.magnet-model.org/), [CGEBox](https://www.ilr1.uni-bonn.de/en/research/research-groups/economic-modeling-of-agricultural-systems/cgebox)),
the framework is designed to be extensible and can be adapted to link with other model types, such as forest growth models.

In its current form, the project allows to harmonize the geographical and sectoral resolution of TiMBA with different CGE models.
For the harmonization, the pipeline downscales CGE model data (e.g., gross domestic product (GDP), population, or land use) to TiMBA's resolution. In turn,
projections of key figures from TiMBA are upscaled to the CGE's resolution, including:
- Production for forest-related sectors to [GTAP](https://www.gtap.agecon.purdue.edu/) sectoral aggregation
- Forest area and stock developments
- Harvest activities
- Carbon stocks
- Technology developments.

Technical details about data downscaling and upscaling are provided in the section [Data processing](#data-processing).  

Future extensions of the project will aim to link TiMBA with other economic or biophysical models by expanding the set of processable model
variables and incorporating further downscaling and upscaling approaches to handle new data formats, such as remote sensing data.
These developments are planned within ongoing and future research projects (see [Roadmap](#project-status-and-roadmap)).


![TiMBA_software_workflow](https://github.com/TI-Forest-Sector-Modelling/TiMBA_Additional_Information/raw/main/images/TiMBA_planned_workflow.png)

**Figure 1:** Software workflow of TiMBA, including the scenario input generator

## Citation
We are glad that you are using TiMBA_Link in your research. Please cite the software in any related publications (articles,
working papers, presentations, etc.) as follows:

Honkomp (2026) TiMBA_Link v1.0.0

## Installation
The project can be directly be installed via **GitHub** using the following steps. An installation via **PyPI** will be made available as soon as possible.

1. Clone the repository
Begin by cloning the repository to your local machine using the following command: 
    >git clone https://github.com/TI-Forest-Sector-Modelling/TiMBA_Link.git
   > 
2. Switch to the project's directory  
Navigate into the project's project folder on your local machine.
   >cd TIMBA_Link
   >
3. Create a virtual environment  
It is recommended to set up a virtual environment for TiMBA_Link to manage dependencies. The package is tested for 
   Python versions up to 3.11. With a newer Python version, we can not guarantee the full functionality of the package.
   Select the correct Python interpreter.   
   Show installed versions: 
   >py -0  
   >
   - If you have installed multiple versions of Python, activate the correct version using the py-Launcher.
   >py -3.11 -m venv venv 
   > 
   - If you are using only a single version of Python on your computer:
   >python -m venv venv
   >
4. Activate the virtual environment  
Enable the virtual environment to isolate the project's dependencies. 
   >venv\Scripts\activate

5. Install the project in the editable mode  
   >pip install -e .

    If the following error occurs: "ERROR: File "setup.py" or "setup.cfg" not found."
    you might need to update the pip version you use with: 
    >python.exe -m pip install --upgrade pip

## Usage
TiMBA_Link automates the bidirectional soft linkage between TiMBA and the selected CGE model. Users can interact with the pipeline
by changing parameters in `default_parameters.py`. An CLI-based entry point will be made available in the future.
Reflecting the pipeline structure, TiMBA_Link parameters are organized in three dictionaries:

- **project_parameters**:
holds parameters defined for the entier project (shared for all three pipelines), including:

|     Parameter name      |                            Parameter description                             |                                                           Available options                                                            | Data Type |
|:-----------------------:|:----------------------------------------------------------------------------:|:--------------------------------------------------------------------------------------------------------------------------------------:|:---------:|
|      `CURRENT_SC`       |      The current scenario name (used for documentation and file naming)      |                                                                                                                                        |    str    |
|       `LINK_TYPE`       |                   The type of link applied in the pipeline                   |         `continuous` or `end_point` (Technical details of both options are prodived under [Data processing](#data-processing))         |    str    |
|      `LINKED_CGE`       |                               Linked CGE name                                |               `MAGNET` or `DART-BIO` (Other CGE can be add flexibily by integrating its regional and product structure)                |    str    |
|        `PROJECT`        |                                 Project name                                 |                       `BioSDG` or `CarbonLeak` (Any new scientific or non-scientific project name can be added)                        |    str    |
|       `ITER_NUM`        | Number of the current iteration (can be ignored if monodirectional linkages) |                                                               Any number                                                               |    int    |
|  `AGGREGATION_SWITCH`   |                  Switch activating the aggregation pipeline                  |                                                           `True` or `False`                                                            |   bool    |
| `DISAGGREGATION_SWITCH` |                Switch activating the disaggregation pipeline                 |                                                           `True` or `False`                                                            |   bool    |
|  `CALIBRATION_SWITCH`   |        Switch activating the calibration pipeline (not published yet)        |                                                           `True` or `False`                                                            |   bool    |

- **aggregation_parameters**:
holds parameters defined for the aggregation pipeline (if `AGGREGATION_SWITCH` is activated), including:

|     Parameter name     |                             Parameter description                             |                                                   Available options                                                   | Data Type |
|:----------------------:|:-----------------------------------------------------------------------------:|:---------------------------------------------------------------------------------------------------------------------:|:---------:|
|     `INPUT_TIMBA`      |                 pkl-output file from TiMBA (main application)                 |                                                 Any output file name                                                  |    str    |
| `DOMAINS_TO_AGGREGATE` | Domains of TiMBA to be aggregated, saved, and passed over to the linked model | `production` (production data),<br/> `forest` (forest data),<br/> `carbon` (carbon data),<br/> `io` (technology data) |   list    |

- **disaggregation_parameters**:
holds parameters defined for the disaggregation pipeline (if `DISAGGREGATION_SWITCH` is activated), including:

|     Parameter name      |             Parameter description             |                                Available options                                 | Data Type |
|:-----------------------:|:---------------------------------------------:|:--------------------------------------------------------------------------------:|:---------:|
| `INPUT_TIMBA_TO_UPDATE` | xlsx-intput file for TiMBA (main application) |                               Any input file name                                |    str    |
|     `INPUT_GDP_CGE`     |         GDP data from the linked CGE          |                               Any input file name                                |    str    |
|   `INPUT_FOREST_CGE`    |        Forest data from the linked CGE        |                               Any input file name                                |    str    |
|      `LINKED_VAR`       |  Variables linked between TiMBA and the CGE   | `gdp` (GDP data),<br/> `gdp_cap` (GDPcap data),<br/> `forest_area` (forest data) |   list    |
|      `UPDATE_FILE`      |         GDP data from the linked CGE          |       `xlsx` (update xlsx-input file),<br/> `pkl` (update pkl-input file)        |    str    |

- **calibration_parameters**:
are currently not in use.

The format of all files provided to the pipeline must match the format of the default datasets provided with the project. Without matching data format, data processing steps will fail.

Reflecting the pipeline structure, TiMBA_Link is supplied with following input data:
```bash
`- data
  `-- input
    `-- cge_data
      |-- default_cge_FOREST.csv  # contains default forest development data aggregated in CGE-regions 
      |-- default_cge_GDP.csv  # contains default gross domestic product development data aggregated in CGE-regions (based on SSP2v3)
      |-- default_cge_POP.csv  # contains default population development data aggregated in CGE-regions (based on SSP2v3)
    `-- supportive_data
      |-- country_concordance.xlsx  # contains the concordance table of TiMBA's countries and CGE's regions (must be adapted if new CGE models are integrated) 
      |-- worldbank_data.xlsx  # contains a copy of the worldbank data in the latest available version (May 2026) (https://data.worldbank.org/indicator/NY.GDP.MKTP.CD)
      |-- fra_data.xlsx  # contains a copy of the forest resources assessment data in the latest available version (May 2026) (https://fra-data.fao.org/assessments/fra/2025)
      |-- worldbank_oecd_countries.xlsx  # contains the concordance table between country codes of the world bank and the OECD
    `-- timba_data
      |-- default_timba_scenario_input.xlsx  # contains a default version of the input file for TiMBA with SSP2v3 data for GDP and population (which is used in the disaggregation pipeline)
      |-- default_timba_scenario_output.pkl  # contains the output of TiMBA for the default input file (which is used in the aggregation pipeline)
```

Output of TiMBA_Link is structured as following:
```bash
`-data
  `--output
    `--aggregation
      |--<YYYMMDD>_agg_carbon_data_default_timba_scenario_output.xlsx  # contains carbon data (generated if `DOMAINS_TO_AGGREGATE` contains "carbon")
      |--<YYYMMDD>_agg_forest_data_default_timba_scenario_output.xlsx  # contains forest data (generated if `DOMAINS_TO_AGGREGATE` contains "forest")
      |--<YYYMMDD>_agg_io_data_default_timba_scenario_output.xlsx  # contains technology data (generated if `DOMAINS_TO_AGGREGATE` contains "io")
      |--<YYYMMDD>_agg_production_data_default_timba_scenario_output.xlsx  # contains production data (generated if `DOMAINS_TO_AGGREGATE` contains "production")
    `--disaggregation
      |--<YYYMMDD>_default_timba_scenario_input.xlsx  # contains the new TiMBA input updated with linked CGE data (details about the file's structure in provided in the TiMBA GitHub repository)
```

For aggregation-related xlsx-files, the excel-sheet "Metadata" provides an exhaustive overview about all generated data.

## Data processing
Data processing steps related to the disaggregation and aggregation are gathered in `logic\aggregation_pipeline.py` and `logic\disaggregation_pipeline.py`, respectively.
TiMBA_Link allows to different ways for soft-linking TiMBA with the selected model, which can be selected in **project_parameters**:
 - "continous": This mode mimics changes of linked variables for all modelled periods and allows the harmonization of developments between both models across the full simulation horizon.
 - "end_point": This mode mimics changes of linked variables between the start and end year, ignoring intermediate periods. This allows to harmonize the overall trend
between both models while reducing computational burden associated with period-specific, uneven growth rates.

As TiMBA and the linked models commonly rely on different input data sources and calibration procedures, harmonising the absolute values of the exchanged variables is challenging.
Instead, TiMBA_Link allows to link relative changes in exchanged variables. This provides necessary flexibility for each model to operate.

### Data aggregation
The aggregation pipeline upscales TiMBA results for products and countries to GTAP sectors and regions according to the concordance tables.
Concordance information about regions and countries is provided in `supportive_data\country_concordance.xlsx`. Concordance information about products
and sectors is provided in `parameters\defines.py`. TiMBA data are aggregated to the CGE level by summing the national and product-level results within each corresponding region and sector.
The outputs of the data aggregation are saved in the folder `output\aggregation` as detailed in [Usage](#usage).

### Data disaggregation
The disaggregation pipeline downscales CGE results for GDP, population, and land use from regional level to the country level.

To downscale socioeconomic data (e.g., GDP and population), TiMBA_Link calculates country-specific weights using World Bank data.
These datasets are manually supplemented with additional national data to ensure coverage all countries included in TiMBA. 
Following countries were anually added for World Bank data (2025): CUB, COK, GUF, MTQ, ANT, PRK, REU, and VGB.
Country-specific weights are calculated using a three-year average of socioeconomic data centred on the start year of provided TiMBA input
(e.g., for a start year of 2020, socioeconomic data of 2019, 2020, and 2021 are used). Users should verify that 
required socioeconomic data are included in the project when changing the start year.
The sum of weights for all countries composing one regions is equal to 1. For single-country regions (e.g., USA) the weight is equal to 1 and can 
be used for verifying the calculation steps. The weight calculation assumes that the distribution of GDP and population across countries within 
a region will not significantly change in the future.

To downscale land use data (e.g., forest area changes), TiMBA_Link calculates country-specific weights using data of forest resources assessment (FRA).
The pipeline allows to downscale forest area changes to the country level while accounting for forst type and FRA-based splitting.
Forest type splitting allows to downscale CGE region data while accounting for managed and unmanaged forests. If forest type splitting is activated,
regional CGE data are disaggregated using only managed forest data. If forest type splitting is deactivated, the total forest area is used for disaggregation.
FRA-based splitting allows to compute country-specific forest weigths by including (=True) or excluding (=False) country without data.
With the default settings, forest area changes are disaggregated without forest type and FRA-based splitting. These settings can be changed
in `aggregation_pipeline.py`.
The forest weight calculation assumes that the repartition of forest area across countries within a region will not significantly
change in the future.

Results of the data disaggregation are saved in the folder `output\disaggregation` as detailed in [Usage](#usage).

## Support
A continuous update of the project to newer Python and package versions is planned but will depend on available time
capacities. 

## Project status and Roadmap
The project is active and is continously extended when time resources are available.
Extensions of the project to automate linkages between TiMBA with other models, including other CGEs but also
forest growth and spatial explicit models, are targeted and will depend on future research projects.

## Contributing
External contributions, additions and suggestion to further develop or improve the project are welcome. To check, discuss
and include your contributions, you can contact us directly via GitHub by creating issues, or by writing an Email to:

tomke.honkomp@thuenen.de or wf-timba@thuenen.de

## Authors and acknowledgment
The project has been initiated and written by [Tomke Honkomp](https://www.thuenen.de/en/fachinstitute/waldwirtschaft/personal/wissenschaftliches-personal/tomke-honkomp-msc) ([ORCID](https://orcid.org/0000-0002-6719-0190), [GitHub](https://github.com/tomkeH)).
The project uses data processed and model results generated by the TI-FSM team based at the Thuenen Institute of Forestry.

## License
Licensed under the GNU AGPL, Version 3.0.

Copyright ©, 2026, Thuenen Institute, Tomke Honkomp, wf-timba@thuenen.de 

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program. If not, see https://www.gnu.org/licenses/agpl-3.0.txt.
