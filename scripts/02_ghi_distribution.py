"""
02_ghi_distribution.py
========================
Descriptive statistics and spatial distribution map of Global Horizontal
Irradiance (GHI) over Réunion Island (daily average, Global Solar Atlas,
1999–2018).

Prerequisite:
    Run 01_reproject_clip.py first. It produces the clipped raster used here.

Inputs:
    outputs/maps/ghi_reunion_clip.tif   (from step 01)
    data/vectors/REU_adm2.shp           (communal boundaries)

Outputs:
    outputs/maps/Final_GHI_Distribution_Map.png
    outputs/tables/ghi_statistics.csv

Usage:
    python scripts/02_ghi_distribution.py
"""

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rioxarray
from matplotlib import colormaps
from matplotlib_scalebar.scalebar import ScaleBar

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_VECTORS = ROOT / "data" / "vectors"
OUTPUT_MAPS = ROOT / "outputs" / "maps"
OUTPUT_TABLES = ROOT / "outputs" / "tables"

COMMUNES_FILENAME = "REU_adm2.shp"
COMMUNE_NAME_FIELD = "NAME_2"
TARGET_CRS = "EPSG:2975"  # RGR92 / UTM 40S

VMIN, VMAX = 1.4, 6.0  # Display range for GHI (kWh/m²/day)


# ---------------------------------------------------------------------------
# Load raster
# ---------------------------------------------------------------------------
def load_clipped_raster():
    """Load the clipped and reprojected GHI raster produced in step 01."""
    clipped_path = OUTPUT_MAPS / "ghi_reunion_clip.tif"
    if not clipped_path.exists():
        sys.exit(
            f"Missing raster: {clipped_path}\n"
            f"Run: python scripts/01_reproject_clip.py"
        )
    return rioxarray.open_rasterio(clipped_path, masked=True).squeeze()


# ---------------------------------------------------------------------------
# Load communes (vector)
# ---------------------------------------------------------------------------
def load_communes():
    """Load commune boundaries using pyogrio (safer than Fiona on Windows)."""
    communes_path = DATA_VECTORS / COMMUNES_FILENAME
    if not communes_path.exists():
        sys.exit(f"Missing vector file: {communes_path}")

    # Using engine="pyogrio" avoids Fiona/GDAL XML parser issues on Windows
    communes = gpd.read_file(communes_path, engine="pyogrio")

    if communes.crs is None or str(communes.crs).upper() != TARGET_CRS:
        communes = communes.to_crs(TARGET_CRS)

    return communes


# ---------------------------------------------------------------------------
# Compute statistics
# ---------------------------------------------------------------------------
def compute_statistics(raster) -> dict:
    """Compute descriptive GHI statistics for the entire island."""
    return {
        "ghi_min_kwh_m2_day": float(raster.min()),
        "ghi_max_kwh_m2_day": float(raster.max()),
        "ghi_mean_kwh_m2_day": float(raster.mean()),
        "ghi_median_kwh_m2_day": float(raster.median()),
    }


def save_statistics(stats: dict, output_csv: Path):
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([stats]).to_csv(output_csv, index=False)
    print(f"GHI statistics exported -> {output_csv}")


# ---------------------------------------------------------------------------
# Plot map
# ---------------------------------------------------------------------------
def plot_ghi_map(raster, communes, output_png: Path):
    """Generate the final spatial distribution map of GHI."""
    custom_cmap = colormaps["YlOrRd"].copy()
    custom_cmap.set_bad(color="white")

    fig, ax = plt.subplots(figsize=(10, 8))

    im = raster.plot(
        cmap=custom_cmap,
        add_colorbar=False,
        vmin=VMIN,
        vmax=VMAX,
        ax=ax,
    )

    communes.boundary.plot(ax=ax, color="black", linewidth=0.8)

    # Add commune labels
    for _, row in communes.iterrows():
        x, y = row.geometry.centroid.x, row.geometry.centroid.y
        ax.text(
            x, y,
            row[COMMUNE_NAME_FIELD],
            fontsize=6,
            color="blue",
            ha="center",
            va="center",
        )

    plt.colorbar(im, label="GHI (kWh/m²/day)", ax=ax)

    ax.set_xlabel("Easting (m)", fontsize=10, fontweight="bold", color="darkred")
    ax.set_ylabel("Northing (m)", fontsize=10, fontweight="bold", color="darkred")
    ax.set_title(
        "Spatial distribution of Global Horizontal Irradiance (GHI)\n"
        "Reunion Island — Daily average (1999–2018)",
        fontweight="bold",
    )

    # Metadata box
    ax.text(
        1, -0.05,
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

    # North arrow
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

    # Scale bar
    scalebar = ScaleBar(
        1,
        units="m",
        dimension="si-length",
        location="lower left",
        scale_loc="bottom",
        font_properties={"size": 8},
    )
    ax.add_artist(scalebar)

    # Grid ticks every 10 km
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    ax.set_xticks(np.arange(np.floor(xmin / 10000) * 10000, xmax, 10000))
    ax.set_yticks(np.arange(np.floor(ymin / 10000) * 10000, ymax, 10000))
    ax.ticklabel_format(style="plain")
    ax.tick_params(axis="both", labelsize=9)
    ax.tick_params(top=True, right=True, direction="in", length=5, width=1)

    # Frame
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
    raster = load_clipped_raster()
    communes = load_communes()

    stats = compute_statistics(raster)
    save_statistics(stats, OUTPUT_TABLES / "ghi_statistics.csv")
    print(stats)

    plot_ghi_map(raster, communes, OUTPUT_MAPS / "Final_GHI_Distribution_Map.png")


if __name__ == "__main__":
    main()
