"""
01_reproject_clip.py

Preprocessing step for the solar potential analysis workflow.

This script:
- loads the Global Solar Atlas GHI raster;
- assigns the correct CRS and handles NoData values;
- creates the La Réunion island boundary by dissolving municipal polygons;
- clips the raster using the island boundary;
- exports raster and vector outputs for further analysis.

Workflow improvement:
The island boundary is generated directly from REU_adm2 municipal polygons.
This avoids the use of an additional REGION.shp file and ensures spatial
consistency throughout the workflow.

Inputs:
    data/raster/GHI_Reunion.tif
    data/vectors/REU_adm2.shp

Outputs:
    outputs/maps/ghi_reunion_clip.tif
    outputs/maps/reunion_boundary.gpkg

Usage:
    python scripts/01_reproject_clip.py
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import rioxarray


# Project configuration
ROOT = Path(__file__).resolve().parents[1]

DATA_RASTER = ROOT / "data" / "raster"
DATA_VECTORS = ROOT / "data" / "vectors"
OUTPUT_MAPS = ROOT / "outputs" / "maps"

RASTER_FILENAME = "GHI_Reunion.tif"
COMMUNES_FILENAME = "REU_adm2.shp"

NODATA_VALUE = 1.17549e-38
TARGET_CRS = "EPSG:2975"  # RGR92 / UTM zone 40S (La Réunion)



def load_ghi_raster(raster_path, target_crs=TARGET_CRS):
    """Load GHI raster, remove NoData values and assign CRS."""

    raster = rioxarray.open_rasterio(
        raster_path,
        masked=True
    ).squeeze()

    raster = raster.where(
        raster != NODATA_VALUE,
        np.nan
    )

    raster = raster.rio.write_crs(
        target_crs,
        inplace=True
    )

    return raster


def load_island_boundary(communes_path, target_crs=TARGET_CRS):
    """Create a single island polygon from municipal boundaries."""

    communes = gpd.read_file(communes_path)

    if communes.crs is None or str(communes.crs).upper() != target_crs:
        communes = communes.to_crs(target_crs)

    # Dissolve all municipalities into one island polygon
    if hasattr(communes, "union_all"):
        boundary = communes.union_all()
    else:
        boundary = communes.unary_union

    return gpd.GeoDataFrame(
        geometry=[boundary],
        crs=communes.crs
    )



def main():

    OUTPUT_MAPS.mkdir(
        parents=True,
        exist_ok=True
    )

    raster_path = DATA_RASTER / RASTER_FILENAME
    communes_path = DATA_VECTORS / COMMUNES_FILENAME

    if not raster_path.exists():
        raise FileNotFoundError(
            f"Raster not found: {raster_path}"
        )

    if not communes_path.exists():
        raise FileNotFoundError(
            f"Vector layer not found: {communes_path}"
        )

    # Load input data
    raster = load_ghi_raster(raster_path)
    boundary_gdf = load_island_boundary(communes_path)

    # Clip raster using island boundary
    raster_clip = raster.rio.clip(
        boundary_gdf.geometry,
        boundary_gdf.crs
    )

    # Export raster
    clipped_path = OUTPUT_MAPS / "ghi_reunion_clip.tif"

    raster_clip.rio.to_raster(
        clipped_path
    )

    print(f"Clipped raster exported -> {clipped_path}")

    # Export boundary using Pyogrio
    boundary_path = OUTPUT_MAPS / "reunion_boundary.gpkg"

    boundary_gdf.to_file(
        boundary_path,
        driver="GPKG",
        engine="pyogrio"
    )

    print(f"Island boundary exported -> {boundary_path}")

    # Validate outputs
    assert clipped_path.exists(), "Output raster was not created"
    assert boundary_path.exists(), "Output GeoPackage was not created"

    print("Pipeline step 1 completed successfully")



if __name__ == "__main__":
    main()