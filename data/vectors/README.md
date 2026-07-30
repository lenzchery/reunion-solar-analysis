\# Administrative boundaries — Reunion Island (GADM v2.8)



\## Description



This folder contains the administrative boundaries used in this project for

spatial analysis over \*\*Reunion Island (France)\*\*.



The dataset corresponds to the commune-level administrative divisions

(second-level administrative units) provided by the \*\*Global Administrative

Areas database (GADM), version 2.8\*\*.



These boundaries are used in the solar resource assessment workflow to:



\- define the study area

\- clip raster datasets (Global Horizontal Irradiation — GHI)

\- perform spatial statistics

\- generate thematic maps





\## Data availability



The original shapefile is \*\*not included in this repository\*\*.



This is intentional and follows the redistribution conditions of the

\*\*GADM v2.8 dataset\*\*.



Although GADM data are available for academic and non-commercial research,

the original files cannot be redistributed through third-party repositories

such as GitHub.



Users must download the dataset directly from the official source.





\## Download



Official dataset:



\*\*Stanford Digital Repository — GADM v2.8\*\*



https://purl.stanford.edu/pn417fx4462





After downloading, place the files in:



```text

data/vectors/

```



Required files:



```text

REU\_adm2.shp

REU\_adm2.dbf

REU\_adm2.shx

REU\_adm2.prj

REU\_adm2.xml

```





\## Citation



If this dataset is used, please cite:



Hijmans, R. J. (2015).  

\*Second-level Administrative Divisions, Reunion, 2015.\*  

Global Administrative Areas (GADM) version 2.8.  

University of California, Berkeley, Museum of Vertebrate Zoology;  

International Rice Research Institute.  

Stanford Digital Repository.



https://purl.stanford.edu/pn417fx4462





\## Usage in this project



The administrative boundaries are used for the processing of Global Horizontal

Irradiation (GHI) data and solar potential mapping.



Main workflow:



```text

GADM boundaries

&#x20;      |

&#x20;      v

Réunion Island mask extraction

&#x20;      |

&#x20;      v

Raster clipping

&#x20;      |

&#x20;      v

Spatial analysis

&#x20;      |

&#x20;      v

Map production

```





\## Processing environment



The vector data can be processed with:



\- QGIS

\- Python geospatial libraries:

&#x20; - GeoPandas

&#x20; - Shapely

&#x20; - Rasterio

&#x20; - Rioxarray





Example:



```python

import geopandas as gpd



gdf = gpd.read\_file(

&#x20;   "data/vectors/REU\_adm2.shp"

)



print(gdf.head())

```





\## Reproducibility note



Datasets with redistribution restrictions are not included in this repository.



Only documentation and processing scripts are versioned.



This approach ensures:



\- legal compliance

\- transparent data provenance

\- reproducibility of the workflow

\- long-term project maintenance

