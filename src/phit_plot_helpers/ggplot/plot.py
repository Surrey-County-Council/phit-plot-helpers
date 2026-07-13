from dataclasses import dataclass, asdict
import numpy as np
import plotnine as gg
import pandas as pd


def range_comparison(
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
    smaller_than_comparator = max < comparator_min.item()
    larger_than_comparator = min > comparator_max.item()
    comp = np.where(smaller_than_comparator, -1, np.where(larger_than_comparator, 1, 0))
    if reverse:
        comp = comp * -1
    return pd.Series(comp)


@dataclass
class RagCmap:
    worse: tuple[int, str, int] = -1, "#B50401", 24
    similar: tuple[int, str, int] = 0, "#F7BF00", 22
    better: tuple[int, str, int] = 1, "#99CF48", 23
    not_compared: tuple[None, str, int] = None, "darkgrey", 21

    def as_color_key(self) -> dict[str, str]:
        return {k: v[1] for k, v in asdict(self).items()}

    def as_sorting_key(self) -> dict[int, str]:
        return {v[0]: k for k, v in asdict(self).items() if v[0] is not None}

    def as_comparator_lable(self) -> str:
        (x,) = (k for k, v in asdict(self).items() if v[0] is None)
        return x

    def as_shape_key(self) -> dict[str, int]:
        return {k: v[2] for k, v in asdict(self).items()}

    def lables(self) -> list[str]:
        return [k.capitalize() for k in asdict(self).keys()]


def transform_for_barplot(
    plot_data: pd.DataFrame,
    comparator_data: pd.DataFrame,
    x: str = "name",
    y: str = "value",
    y_min: str = "LCI",
    y_max: str = "UCI",
    comparator_lable: str = "Compared to England",
    lower_is_better: bool = False,
    cmap: RagCmap | None = None,
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
        cmap: Allows customization of the colours used.
                Defaults to our pre-defined colours set in `RagCmap`
    """
    if cmap is None:
        cmap = RagCmap()
    cols = [x, y, y_min, y_max]

    # check columns exist as required
    try:
        df: pd.DataFrame = plot_data[cols]
        comp = comparator_data[cols]
    except KeyError as e:
        raise KeyError("data schema is malconfigured", e)

    # create new column for comparator_lable
    try:
        comp[comparator_lable] = cmap.as_comparator_lable()
        df[comparator_lable] = range_comparison(
            plot_data[y_min],
            plot_data[y_max],
            comparator_data[y_min],
            comparator_data[y_max],
            lower_is_better,
        ).replace(cmap.as_sorting_key())
    except ValueError as e:
        raise ValueError("data contents are malconfigured", e)

    # concatenate and sort data
    return pd.concat([comp, df.sort_values(by=[y], ascending=lower_is_better)])


def barplot(
    plot_data: pd.DataFrame,
    comparator_data: pd.DataFrame,
    plot_title: str,
    plot_subtitle: str,
    plot_caption: str,
    point_shift: float | int = -40,
    x: str = "name",
    y: str = "value",
    y_min: str = "LCI",
    y_max: str = "UCI",
    x_lable: str | None = None,
    y_lable: str | None = "Age standardised rate (per 100,000)",
    comparator_lable: str = "Compared to England",
    lower_is_better: bool = False,
    cmap: RagCmap | None = None,
) -> gg.ggplot:
    """Create a RAG rated bar chart which compares plot_data to comparator_data.

    plot_data contains a single measure of health for a single point in time and multiple areas
    (eg. multiple counties in the same region).

    comparator_data contains a single measure of health for a single point in time and a single comparator area,
    usually a parent area for the areas defined in plot_data (eg, england).

    The resulting plot shows the data from both in the same chart. The comparator area is shaded in grey,
    while all the other areas will be RAG rated.


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
        cmap: Allows customization of the colours used.
                Defaults to our pre-defined colours set in `RagCmap`
    """
    if cmap is None:
        cmap = RagCmap()
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
        + gg.geom_col(gg.aes(fill=comparator_lable), show_legend=False)
        + gg.geom_point(
            gg.aes(x, point_shift, shape=comparator_lable, fill=comparator_lable),
            size=2.5,
            show_legend=True,
        )
        + gg.geom_errorbar(gg.aes(ymin=y_min, ymax=y_max), width=0.3, colour="black")
        + gg.scale_y_continuous(expand=(0.04, 0.05))
        + gg.labs(
            x=x_lable,
            y=y_lable,
            title=plot_title,
            subtitle=plot_subtitle,
            caption=plot_caption,
        )
        + gg.scale_shape_manual(
            name=comparator_lable,
            values=cmap.as_shape_key(),
            labels=cmap.lables(),
            drop=False,
        )
        + gg.scale_fill_manual(
            name=comparator_lable,
            values=cmap.as_color_key(),
            labels=cmap.lables(),
            drop=False,
        )
        + gg.theme_minimal()
    )
    return plot
