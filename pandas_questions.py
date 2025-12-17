"""Plotting referendum results in pandas.

In short, we want to make beautiful map to report results of a referendum.
In some way, we would like to depict results with something similar to the maps
that you can find here:
https://github.com/x-datascience-datacamp/datacamp-assignment-pandas/blob/main/example_map.png

To do that, you will load the data as pandas.DataFrame, merge the info and
aggregate them by regions and finally plot them on a map using `geopandas`.
"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

path = (
    "/data/"
)


def load_data():
    """Load data from the CSV files referundum/regions/departments."""
    referendum = pd.read_csv(path + "referendum.csv", sep=";")
    regions = pd.read_csv(path +  "regions.csv")
    departments = pd.read_csv(path + "departments.csv")

    return referendum, regions, departments


def merge_regions_and_departments(regions, departments):
    """Merge regions and departments in one DataFrame.

    The columns in the final DataFrame should be:
    ['code_reg', 'name_reg', 'code_dep', 'name_dep']
    """
    reg = regions[["code", "name"]]
    reg.columns = ["code_reg", "name_reg"]

    dep = departments[["region_code", "code", "name"]]
    dep.columns = ["code_reg", "code_dep", "name_dep"]

    reg = reg.merge(dep, on="code_reg", how="left")

    return reg[["code_reg", "name_reg", "code_dep", "name_dep"]]


def merge_referendum_and_areas(referendum, regions_and_departments):
    """Merge referendum and regions_and_departments in one DataFrame.

    You can drop the lines relative to DOM-TOM-COM departments, and the
    french living abroad, which all have a code that contains `Z`.
    """
    reg_and_dep = regions_and_departments.copy()
    ref = referendum.copy()

    ref["Department code"] = ref["Department code"].astype(str)
    ref["bool"] = ref["Department code"].apply(
        lambda x: 1 if "Z" in x else 0
    )
    ref = ref[ref["bool"] == 0].drop("bool", axis=1)

    ref["Department code"] = ref["Department code"].apply(
        lambda x: "0" + x if len(x) == 1 else x
    )

    return reg_and_dep.merge(
        ref,
        left_on="code_dep",
        right_on="Department code",
        how="right",
    )


def compute_referendum_result_by_regions(referendum_and_areas):
    """Return a table with the absolute count for each region.

    The return DataFrame should be indexed by `code_reg` and have columns:
    ['name_reg', 'Registered', 'Abstentions', 'Null', 'Choice A', 'Choice B']
    """
    result = (
        referendum_and_areas[
            [
                "code_reg",
                "name_reg",
                "Registered",
                "Abstentions",
                "Null",
                "Choice A",
                "Choice B",
            ]
        ]
        .groupby("code_reg", as_index=True)
        .agg(
            {
                "name_reg": "first",
                "Registered": "sum",
                "Abstentions": "sum",
                "Null": "sum",
                "Choice A": "sum",
                "Choice B": "sum",
            }
        )
    )

    return result


def plot_referendum_map(referendum_result_by_regions):
    """Plot a map with the results from the referendum."""
    gdf_regions = gpd.read_file(path + "regions.geojson")
    gdf_regions["code"] = gdf_regions["code"].astype(str)

    results = referendum_result_by_regions.reset_index().copy()
    results["code_reg"] = results["code_reg"].astype(str)

    gdf = gdf_regions.merge(
        results,
        left_on="code",
        right_on="code_reg",
        how="left",
    )
    gdf = gdf.to_crs(epsg=2154)

    expressed = gdf["Choice A"] + gdf["Choice B"]
    gdf["ratio"] = gdf["Choice A"] / expressed

    fig, ax = plt.subplots(1, 1, figsize=(8, 7))

    gdf.plot(
        column="ratio",
        ax=ax,
        cmap="RdBu_r",
        legend=True,
        linewidth=0.6,
        edgecolor="white",
        legend_kwds={
            "label": "Share of Choice A among expressed ballots",
            "shrink": 0.75,
        },
    )

    ax.set_aspect("equal")
    ax.set_title("Referendum results by region", fontsize=14)
    ax.set_axis_off()

    return gdf


if __name__ == "__main__":
    referendum, df_reg, df_dep = load_data()

    regions_and_departments = merge_regions_and_departments(
        df_reg,
        df_dep,
    )
    referendum_and_areas = merge_referendum_and_areas(
        referendum,
        regions_and_departments,
    )
    referendum_results = compute_referendum_result_by_regions(
        referendum_and_areas,
    )

    print(referendum_results.reset_index())
    plot_referendum_map(referendum_results)
    plt.show()
