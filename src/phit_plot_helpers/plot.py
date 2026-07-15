from typing import Protocol, runtime_checkable
from loguru import logger
import numpy as np
import plotnine as gg
import pandas as pd


@runtime_checkable
class PandasCompliant(Protocol):
    def to_pandas(self) -> pd.DataFrame: ...


def range_comparison(
    smaller_than_comparator: pd.Series,
    larger_than_comparator: pd.Series,
    reverse: bool = False,
    **kwargs,
) -> pd.Series:
    """given 2 series that are boolean mask for larger and smaller, return a single series that creates a rank

    -1, 0, 1 are used as classifications of less than, equal to and greater than respectively.

    the result is manually cast to a Series, you may need to use **kwargs to feed through index, dtypes etc.
    """
    comp = np.where(smaller_than_comparator, -1, np.where(larger_than_comparator, 1, 0))
    if reverse:
        comp = comp * -1
    return pd.Series(comp, **kwargs)


def range_comparison_by_item(
    min: pd.Series,
    max: pd.Series,
    comparator_min: pd.Series,
    comparator_max: pd.Series,
    reverse: bool = False,
) -> pd.Series:
    """given a the series, return a series representing the comparason of a potentially overlapping range.

    If the range overlaps, the comparison is neither smaller or larger.

    -1, 0, 1 are used as classifications of less than, equal to and greater than respectively.

    if
    """
    return range_comparison(
        smaller_than_comparator=max < comparator_min.item(),
        larger_than_comparator=min > comparator_max.item(),
        reverse=reverse,
    )


COLORS = {
    "Worse": "#B50401",
    "Similar": "#F7BF00",
    "Better": "#99CF48",
    "Not Compared": "darkgrey",
}


SHAPES = {"Worse": "v", "Similar": "s", "Better": "^", "Not Compared": "D"}


def guard_against_duplicates(df: pd.DataFrame, *primary_key: str):
    if df.empty:
        raise ValueError("DataFrame is empty")
    subset = df.drop_duplicates([*primary_key])
    if len(df) != len(subset):
        raise ValueError(f"DataFrame contains duplicates in {[*primary_key]}")


def transform_for_barplot(
    plot_data: pd.DataFrame | PandasCompliant,
    comparator_data: pd.DataFrame | PandasCompliant,
    x: str = "Area Name",
    y: str = "Value",
    y_min: str = "Lower CI 95.0 limit",
    y_max: str = "Upper CI 95.0 limit",
    comparator_lable: str = "Compared to England",
    lower_is_better: bool = False,
) -> pd.DataFrame:
    """Create a single combined DataFrame from plot_data and comparator_data.

    plot_data contains a single measure of health for a single point in time and multiple areas
    (eg. multiple counties in the same region).

    comparator_data contains a single measure of health for a single point in time and a single comparator area,
    usually a parent area for the areas defined in plot_data (eg, england).

    The data format is checked, and the cmap informs the values imported into the calculated field.
    This allows the same cmap to be passed to multiple functions and ensure consistency.
    The resulting DataFrame is sorted, with the comparator at the top, and the plot_data ordered by best to worst.
    while all the other areas will be RAG rated.


    Params:
        plot_data: A pandas DataFrame containing multiple records to be compared. The required columns can be adjusted
                   as key word arguments.
        comparator_data: A pandas DataFrame containing a single record. Should keep the same data schema as plot_data.
        x: The name of the column in the data that will be represented on the x-axis.
                Defaults to `name`.
        y: The name of the column in the data that will be represented on the y-axis.
                Defaults to `value`.
        y_min: The name of the column in the data that represents the lower confidence interval for the error bars.
                Defaults to `LCI`.
        y_max: The name of the column in the data that represents the upper confidence interval for the error bars.
                Defaults to `UCI`.
        comparator_lable: The lable that should be applied for the comparator.
                Defaults to `Compared to England`,
        lower_is_better: If lower is better, lower scores will be green (better) instead of red (worse). eg:
                prevalence of illness `x` - lower prevalence is probably better
                uptake of screening programme `y` - lower uptake is probably worse
                Defaults to `False`
    """
    if isinstance(plot_data, PandasCompliant):
        plot_data = plot_data.to_pandas()
    if isinstance(comparator_data, PandasCompliant):
        comparator_data = comparator_data.to_pandas()
    cols = [x, y, y_min, y_max]

    # check columns exist as required
    try:
        df: pd.DataFrame = plot_data[cols]
        comp = comparator_data[cols]
        assert len(comp) == 1
    except KeyError as e:
        raise ValueError("data schema is malconfigured", e)
    except AssertionError as e:
        raise ValueError("comparator data should contain only one record", e)

    # create new column for comparator_lable
    try:
        df[comparator_lable] = range_comparison(
            plot_data[y_min] < comparator_data[y_max].item(),
            plot_data[y_max] > comparator_data[y_max].item(),
            lower_is_better,
        ).replace({-1: "Worse", 0: "Similar", 1: "Better"})
        comp[comparator_lable] = "Not Compared"
    except ValueError as e:
        raise ValueError("data contents are malconfigured", e)

    # concatenate and sort data
    final_df: pd.DataFrame = pd.concat(
        [comp, df.sort_values(by=[y], ascending=lower_is_better)]
    )
    guard_against_duplicates(final_df, x)
    return final_df


def transform_for_lineplot(
    plot_data: pd.DataFrame | PandasCompliant,
    comparator_column: str,
    main_area: str,
    comparator_area: str,
    x: str = "Time period",
    x_sortable: str = "Time period Sortable",
    y: str = "Value",
    y_min: str = "Lower CI 95.0 limit",
    y_max: str = "Upper CI 95.0 limit",
    comparator_lable: str = "Compared To England",
    lower_is_better: bool = False,
) -> pd.DataFrame:
    """Create a single combined DataFrame from plot_data including only the main_area and comparator_area.

    plot_data contains a single measure of health for multiple points in time and multiple areas
    plot data is filtered to include only the main_area and comparator_area

    The data format is checked
    The resulting DataFrame is sorted, with the comparator at the top, and the plot_data ordered by time period.
    """
    if isinstance(plot_data, PandasCompliant):
        plot_data = plot_data.to_pandas()

    cols = [comparator_column, x, x_sortable, y, y_min, y_max]

    # check columns exist as required
    try:
        df: pd.DataFrame = plot_data[cols]
        main_df: pd.DataFrame = (
            df[df[comparator_column] == main_area]
            .drop_duplicates()
            .set_index(x_sortable, drop=False)
            .sort_index()
        )
        comp_df: pd.DataFrame = (
            df[df[comparator_column] == comparator_area]
            .drop_duplicates()
            .set_index(x_sortable, drop=False)
            .sort_index()
        )
        guard_against_duplicates(main_df, x_sortable)
        guard_against_duplicates(comp_df, x_sortable)
    except KeyError as e:
        raise ValueError("data schema is malconfigured", e)

    # create new column for comparator_lable
    try:
        main_df[comparator_lable] = (
            range_comparison(
                main_df[y_max] < comp_df[y_min],
                main_df[y_min] < comp_df[y_max],
                lower_is_better,
                index=main_df.index,
            )
            .replace({-1: "Worse", 0: "Similar", 1: "Better"})
            .fillna("Not Compared")
        )
        comp_df[comparator_lable] = "Not Compared"
    except ValueError as e:
        raise ValueError("data contents are malconfigured", e)

    # concatenate data and remove extra index
    final_df: pd.DataFrame = pd.concat([main_df, comp_df]).reset_index(drop=True)
    return final_df


def lineplot(
    df: pd.DataFrame | PandasCompliant,
    comparator_column: str,
    main_area: str,
    comparator_area: str,
    plot_title: str,
    plot_subtitle: str,
    plot_caption: str,
    x: str = "Time period",
    x_sortable: str = "Time period Sortable",
    y: str = "Value",
    y_min: str = "Lower CI 95.0 limit",
    y_max: str = "Upper CI 95.0 limit",
    x_lable: str | None = "Year",
    y_lable: str | None = "Age standardised rate (per 100,000)",
    comparator_lable: str = "Compared To England",
    lower_is_better: bool = False,
):
    plot_data = transform_for_lineplot(
        df,
        comparator_column,
        main_area,
        comparator_area,
        x,
        x_sortable,
        y,
        y_min,
        y_max,
        comparator_lable,
        lower_is_better,
    )

    plot = (
        gg.ggplot(plot_data, gg.aes(x=x, y=y))
        + gg.geom_line(
            gg.aes(
                group=comparator_column,
                colour=comparator_column,
                linetype=comparator_column,
            ),
            size=1,
            show_legend=True,
        )
        + gg.geom_point(
            gg.aes(shape=comparator_lable, fill=comparator_lable),
            size=3,
            show_legend=True,
        )
        + gg.geom_errorbar(
            gg.aes(ymin=y_min, ymax=y_max, colour=comparator_column), width=0.3
        )
        + gg.labs(
            x=x_lable,
            y=y_lable,
            title=plot_title,
            subtitle=plot_subtitle,
            caption=plot_caption,
        )
        + gg.scale_shape_manual(
            name=comparator_lable, values=SHAPES, breaks=list(SHAPES.keys())[::-1]
        )
        + gg.scale_fill_manual(
            name=comparator_lable, values=COLORS, breaks=list(COLORS.keys())[::-1]
        )
        + gg.scale_color_manual(
            name=comparator_column,
            values={main_area: "#0062A2", comparator_area: "darkgrey"},
            breaks=[comparator_area, main_area],
        )
        + gg.scale_linetype_manual(
            name=comparator_column,
            values={main_area: "solid", comparator_area: "dashed"},
            breaks=[comparator_area, main_area],
        )
        + gg.theme_minimal()
        + gg.theme(
            axis_line_x=gg.element_line(colour="black", linewidth=0.5),
            axis_line_y=gg.element_line(colour="black", linewidth=0.5),
            axis_ticks_x=gg.element_line(colour="black"),
            axis_ticks_y=gg.element_line(colour="black"),
            axis_text_x=gg.element_text(rotation=45),
        )
    )
    return plot


def barplot(
    plot_data: pd.DataFrame | PandasCompliant,
    comparator_data: pd.DataFrame | PandasCompliant,
    plot_title: str,
    plot_subtitle: str,
    plot_caption: str,
    point_shift: float | int = -40,
    x: str = "Area Name",
    y: str = "Value",
    y_min: str = "Lower CI 95.0 limit",
    y_max: str = "Upper CI 95.0 limit",
    x_lable: str | None = None,
    y_lable: str | None = "Age standardised rate (per 100,000)",
    comparator_lable: str = "Compared to England",
    lower_is_better: bool = False,
) -> gg.ggplot:
    """Create a RAG rated bar chart which compares plot_data to comparator_data.

    plot_data contains a single measure of health for a single point in time and multiple areas
    (eg. multiple counties in the same region).

    comparator_data contains a single measure of health for a single point in time and a single comparator area,
    usually a parent area for the areas defined in plot_data (eg, england).

    The resulting plot shows the data from both in the same chart. The comparator area is shaded in grey,
    while all the other areas will be RAG rated. Data is ordered with the comparator at the top,
    and subsequently ordered according to whether lower is better, with the best areas being at the top of the chart.


    Params:
        plot_data: A pandas DataFrame containing multiple records to be compared. The required columns can be adjusted
                   as key word arguments.
        comparator_data: A pandas DataFrame containing a single record. Should keep the same data schema as plot_data.
        plot_title: Title of the plot.
        plot_subtitle: Sub-title of the plot.
        plot_caption: Caption describing the plot.
        point_shift: Shift the icons by an ammount.
                Defaults to -40, may require tweaking through experimentation.
        x: The name of the column in the data that will be represented on the x-axis.
                Defaults to `name`.
        y: The name of the column in the data that will be represented on the y-axis.
                Defaults to `value`.
        y_min: The name of the column in the data that represents the lower confidence interval for the error bars.
                Defaults to `LCI`.
        y_max: The name of the column in the data that represents the upper confidence interval for the error bars.
                Defaults to `UCI`.
        x_lable: The lable that should be applied to the x axis.
                Defaults to None as the `name` column generally represents a named area.
        y_lable: The lable that should be applied to the y axis, generally descriptive of the numeric measure for  the `value` column.
                Defaults to `Age standardised rate (per 100,000)`.
        comparator_lable: The lable that should be applied for the comparator.
                Defaults to `Compared to England`,
        lower_is_better: If lower is better, lower scores will be green (better) instead of red (worse). eg:
                prevalence of illness `x` - lower prevalence is probably better
                uptake of screening programme `y` - lower uptake is probably worse
                Defaults to `False`
    """
    vis_data = transform_for_barplot(
        plot_data=plot_data,
        comparator_data=comparator_data,
        x=x,
        y=y,
        y_min=y_min,
        y_max=y_max,
        comparator_lable=comparator_lable,
        lower_is_better=lower_is_better,
    )

    # define plot
    plot = (
        gg.ggplot(vis_data, gg.aes(x=x, y=y))
        + gg.geom_col(
            gg.aes(fill=comparator_lable),
            show_legend=False,
        )
        + gg.geom_point(
            gg.aes(
                x,
                point_shift,
                shape=comparator_lable,
                fill=comparator_lable,
            ),
            size=2.5,
            show_legend=True,
        )
        + gg.geom_errorbar(gg.aes(ymin=y_min, ymax=y_max), width=0.3, colour="black")
        + gg.scale_x_discrete(limits=vis_data[x].to_list()[::-1])
        + gg.scale_shape_manual(
            name=comparator_lable, values=SHAPES, breaks=list(SHAPES.keys())[::-1]
        )
        + gg.scale_fill_manual(
            name=comparator_lable, values=COLORS, breaks=list(COLORS.keys())[::-1]
        )
        + gg.labs(
            x=x_lable,
            y=y_lable,
            title=plot_title,
            subtitle=plot_subtitle,
            caption=plot_caption,
        )
        + gg.theme_minimal()
        + gg.coord_flip()
    )
    return plot
