"""
03_optimal_zones.py
=====================
Extraction of optimal solar zones (GHI >= threshold), vectorization,
area calculation, and intersection with commune boundaries.

Prerequisite:
    Run 01_reproject_clip.py first. It produces the clipped raster used here.

Improvement over the initial version:
    Vectorization (rasterio.features.shapes) is performed directly in memory
    (raster.values + raster.rio.transform()), without writing temporary .tif
    files to disk.

Inputs:
    outputs/maps/ghi_reunion_clip.tif   (from step 01)
    data/vectors/REU_adm2.shp           (commune boundaries)

Outputs:
    outputs/maps/Optimal_Solar_Zones.png
    outputs/maps/optimal_zones.gpkg
    outputs/maps/commune_centroids.gpkg
    outputs/tables/optimal_solar_zones_area.csv

Usage:
    python scripts/03_optimal_zones.py --threshold 5.0
"""

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rioxarray
from matplotlib import colormaps
from matplotlib.patches import FancyBboxPatch
from matplotlib_scalebar.scalebar import ScaleBar
from rasterio.features import shapes

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_VECTORS = ROOT / "data" / "vectors"
OUTPUT_MAPS = ROOT / "outputs" / "maps"
OUTPUT_TABLES = ROOT / "outputs" / "tables"

COMMUNES_FILENAME = "REU_adm2.shp"
COMMUNE_NAME_FIELD = "NAME_2"
TARGET_CRS = "EPSG:2975"

DEFAULT_GHI_THRESHOLD = 5.0  # kWh/m²/day
MIN_POLYGON_AREA_M2 = 1000   # filter small polygons (vectorization noise)


# ---------------------------------------------------------------------------
# Load raster
# ---------------------------------------------------------------------------
def load_clipped_raster():
    clipped_path = OUTPUT_MAPS / "ghi_reunion_clip.tif"
    if not clipped_path.exists():
        sys.exit(
            f"Missing raster: {clipped_path}\n"
            f"Run: python scripts/01_reproject_clip.py"
        )
    return rioxarray.open_rasterio(clipped_path, masked=True).squeeze()


# ---------------------------------------------------------------------------
# Load communes
# ---------------------------------------------------------------------------
def load_communes():
    communes_path = DATA_VECTORS / COMMUNES_FILENAME
    if not communes_path.exists():
        sys.exit(f"Missing vector file: {communes_path}")

    # Using pyogrio avoids Fiona/GDAL XML parser issues on Windows
    communes = gpd.read_file(communes_path, engine="pyogrio")

    if communes.crs is None or str(communes.crs).upper() != TARGET_CRS:
        communes = communes.to_crs(TARGET_CRS)

    return communes


# ---------------------------------------------------------------------------
# Compute area statistics
# ---------------------------------------------------------------------------
def compute_area_stats(raster_clip, mask_ghi):
    res_x, res_y = raster_clip.rio.resolution()
    pixel_area_m2 = abs(res_x * res_y)

    zone_area_km2 = (np.count_nonzero(mask_ghi) * pixel_area_m2) / 1e6
    total_area_km2 = (raster_clip.count().item() * pixel_area_m2) / 1e6
    percent_zone = (zone_area_km2 / total_area_km2) * 100

    return zone_area_km2, total_area_km2, percent_zone


# ---------------------------------------------------------------------------
# Vectorization
# ---------------------------------------------------------------------------
def vectorize_zone(ghi_zone, mask_ghi):
    """Vectorize the filtered raster directly in memory (no temporary .tif)."""
    data = ghi_zone.values.astype("float32")
    transform = ghi_zone.rio.transform()
    mask_arr = mask_ghi.values

    results = (
        {"properties": {"value": v}, "geometry": geom}
        for geom, v in shapes(data, mask=mask_arr, transform=transform)
    )

    gdf_zone = gpd.GeoDataFrame.from_features(results, crs=ghi_zone.rio.crs)
    gdf_zone = gdf_zone[gdf_zone.area > MIN_POLYGON_AREA_M2]

    return gdf_zone


# ---------------------------------------------------------------------------
# Plot map
# ---------------------------------------------------------------------------
def plot_optimal_zones_map(
    ghi_zone, boundary, communes, communes_points,
    zone_area_km2, percent_zone, threshold, output_png: Path
):
    custom_cmap = colormaps["YlOrRd"].copy()
    custom_cmap.set_bad(color="white")

    fig, ax = plt.subplots(figsize=(10, 8))

    im = ghi_zone.plot(
        cmap=custom_cmap,
        add_colorbar=True,
        vmin=threshold,
        vmax=threshold + 1,
        ax=ax,
        zorder=2,
    )

    communes.boundary.plot(ax=ax, color="lightgray", linewidth=0.3, zorder=3)
    boundary.boundary.plot(ax=ax, color="black", linewidth=1)

    cbar = im.colorbar
    cbar.set_label("GHI (kWh/m²/day)", fontsize=10, fontweight="bold")

    communes_points.plot(
        ax=ax,
        color="blue",
        alpha=0.6,
        markersize=60,
        edgecolor="white",
        zorder=3,
    )

    for _, row in communes_points.iterrows():
        ax.text(
            row.geometry.x,
            row.geometry.y,
            row[COMMUNE_NAME_FIELD],
            fontsize=6,
            ha="center",
            va="center",
            fontweight="bold",
            color="navy",
            path_effects=[pe.withStroke(linewidth=1.5, foreground="white")],
            zorder=4,
        )

    ax.set_xlabel("Longitude (m)", fontsize=12, fontweight="bold", color="darkred")
    ax.set_ylabel("Latitude (m)", fontsize=12, fontweight="bold", color="darkred")
    ax.tick_params(labelsize=10)

    ax.set_title(
        f"Optimal Solar Cooking Zones (≥ {threshold:.0f} kWh/m²/day)",
        fontsize=14,
        fontweight="bold",
    )

    stats_text = (
        f"Area ≥ {threshold:.0f} kWh/m²/day: {zone_area_km2:.1f} km²\n"
        f"({percent_zone:.1f} % of Réunion Island)"
    )

    box_x, box_y = 0.5, 0.5
    bbox = FancyBboxPatch(
        (box_x - 0.17, box_y - 0.03),
        width=0.35,
        height=0.07,
        boxstyle="round,pad=0.02",
        ec="black",
        fc="white",
        alpha=0.7,
        transform=ax.transAxes,
    )
    ax.add_patch(bbox)

    ax.text(
        box_x,
        box_y,
        stats_text,
        transform=ax.transAxes,
        ha="center",
        va="center",
        fontsize=8,
        fontweight="bold",
    )

    # Metadata including author
    ax.text(
        1,
        -0.05,
        "Author: Lenz Arly Chery\nCRS: RGR92 UTM Zone 40S\nSource: Global Solar Atlas",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=7.5,
        color="gray",
        fontweight="bold",
        style="italic",
        bbox=dict(facecolor="white", alpha=0.5, boxstyle="round,pad=0.3"),
    )

    ax.annotate(
        "N",
        xy=(0.95, 0.88),
        xytext=(0.95, 0.78),
        arrowprops=dict(facecolor="black", width=2, headwidth=8),
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
        xycoords="axes fraction",
    )

    scalebar = ScaleBar(
        1,
        units="m",
        dimension="si-length",
        location="lower left",
        scale_loc="bottom",
        font_properties={"size": 8},
    )
    ax.add_artist(scalebar)

    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()

    ax.set_xticks(np.arange(np.floor(xmin / 10000) * 10000, xmax, 10000))
    ax.set_yticks(np.arange(np.floor(ymin / 10000) * 10000, ymax, 10000))

    ax.ticklabel_format(style="plain")
    ax.tick_params(axis="both", labelsize=9)
    ax.tick_params(top=True, right=True, direction="in", length=5, width=1)

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(1.2)
        spine.set_color("black")

    OUTPUT_MAPS.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_png, dpi=300, bbox_inches="tight")
    print(f"Map exported -> {output_png}")
    plt.show()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Extraction of optimal solar zones.")
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_GHI_THRESHOLD,
        help=f"GHI threshold in kWh/m²/day (default: {DEFAULT_GHI_THRESHOLD})",
    )
    args = parser.parse_args()
    threshold = args.threshold

    OUTPUT_MAPS.mkdir(parents=True, exist_ok=True)
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)

    raster_clip = load_clipped_raster()
    communes = load_communes()

    boundary = gpd.read_file(
        OUTPUT_MAPS / "reunion_boundary.gpkg",
        engine="pyogrio",
    )

    mask_ghi = raster_clip >= threshold
    ghi_zone = raster_clip.where(mask_ghi)

    zone_area_km2, total_area_km2, percent_zone = compute_area_stats(
        raster_clip, mask_ghi
    )

    print(
        f"Area >= {threshold} kWh/m²/day: "
        f"{zone_area_km2:.2f} km² ({percent_zone:.2f} %)"
    )

    pd.DataFrame(
        [
            {
                "area_km2": zone_area_km2,
                "total_area_km2": total_area_km2,
                "percent_reunion": percent_zone,
                "ghi_threshold_kwh_m2_day": threshold,
            }
        ]
    ).to_csv(OUTPUT_TABLES / "optimal_solar_zones_area.csv", index=False)

    print(f"Statistics exported -> {OUTPUT_TABLES / 'optimal_solar_zones_area.csv'}")

    gdf_zone = vectorize_zone(ghi_zone, mask_ghi)

    gdf_zone.to_file(
        OUTPUT_MAPS / "optimal_zones.gpkg",
        driver="GPKG",
        engine="pyogrio",
    )

    print(f"Optimal zones exported -> {OUTPUT_MAPS / 'optimal_zones.gpkg'}")

    communes_intersect = gpd.overlay(communes, gdf_zone, how="intersection")
    communes_unique = communes_intersect.dissolve(by=COMMUNE_NAME_FIELD).reset_index()

    communes_points = communes_unique.copy()
    communes_points["geometry"] = communes_points.centroid

    communes_points.to_file(
        OUTPUT_MAPS / "commune_centroids.gpkg",
        driver="GPKG",
        engine="pyogrio",
    )

    print(f"Centroids exported -> {OUTPUT_MAPS / 'commune_centroids.gpkg'}")

    plot_optimal_zones_map(
        ghi_zone,
        boundary,
        communes,
        communes_points,
        zone_area_km2,
        percent_zone,
        threshold,
        OUTPUT_MAPS / "Optimal_Solar_Zones.png",
    )


if __name__ == "__main__":
    main()
