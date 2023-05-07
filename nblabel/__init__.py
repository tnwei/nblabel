import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype
import traitlets
import bqplot
import ipywidgets as ipy
from collections import OrderedDict
from typing import Any, Text


def label(
    df: pd.DataFrame,
    x_col: Any = "x",
    y_col: Any = "y",
    label_col_name: Text = "selected",
    title: Text = "nblabeller",
):
    if label_col_name is None:
        label_col_name = "selected"

    if x_col is None:
        x_col = "x"

    if y_col is None:
        y_col = "y"

    assert x_col in df.columns, f"x_col: {x_col} not in df!"
    assert y_col in df.columns, f"y_col: {y_col} not in df!"

    if label_col_name in df.columns:
        # Whole col dtype is not bool, but np.dtype("bool")
        assert df[label_col_name].dtype is np.dtype("bool"), (
            f"Column {label_col_name} dtype should be bool, but is {df[label_col_name].dtype}. "
            + "Use another label_col_name instead"
        )
    else:
        df.loc[:, label_col_name] = False

    scales = {}

    # Check and decide what axes are best
    if is_datetime64_any_dtype(df[x_col]):
        scales["x"] = bqplot.DateScale()
    else:
        scales["x"] = bqplot.LinearScale()

    # Same goes for y axis!
    if is_datetime64_any_dtype(df[y_col]):
        scales["y"] = bqplot.DateScale()
    else:
        scales["y"] = bqplot.LinearScale()

    scatter = bqplot.Scatter(
        x=df.loc[df[label_col_name] == False, x_col],
        y=df.loc[df[label_col_name] == False, y_col],
        scales=scales,
        colors=["gray"],
        # For some reason, opacity doesn't work
        # TODO troubleshoot
        opacity=np.array([0.05] * len(df.loc[df[label_col_name] == False])),
        # Don't need legend formatting if colors are clear
        # display_legend=True,
        # name="Not selected",
        # labels=["Not selected"] * len(df.loc[df["selected"] == False])
    )

    selected_scatter = bqplot.Scatter(
        x=df.loc[df[label_col_name] == True, x_col],
        y=df.loc[df[label_col_name] == True, y_col],
        scales=scales,
        colors=["orange"],
        opacity=[1],
        # Don't need legend formatting if colors are clear
        # display_legend=True,
        # name="Selected",
        # labels=["Selected"] * len(df.loc[df["selected"] == True])
    )

    sel = bqplot.interacts.BrushSelector(
        x_scale=scales["x"],
        y_scale=scales["y"],
        # marks required so that the mark itself can have
        # .selected attribute
        marks=[scatter, selected_scatter],
    )

    # Inspired by this fine piece of code
    # https://github.com/bqplot/bqplot/issues/316#issuecomment-318619629
    pz_x = bqplot.interacts.PanZoom(scales={"x": [scales["x"]]})
    pz_y = bqplot.interacts.PanZoom(scales={"y": [scales["y"]]})
    pz_xy = bqplot.interacts.PanZoom(
        scales={
            "x": [scales["x"]],
            "y": [scales["y"]],
        }
    )

    interacts = ipy.ToggleButtons(
        options=OrderedDict(
            [
                ("Selector", sel),
                ("xy ", pz_xy),
                ("x ", pz_x),
                ("y ", pz_y),
            ]
        ),
        icons=["hand-pointer-o", "arrows", "arrows-h", "arrows-v"],
        tooltips=[
            "Select",
            "Zoom/pan in x & y",
            "Zoom/pan in x only",
            "Zoom/pan in y only",
        ],
    )
    interacts.style.button_width = "100px"

    # bqplot requires the axis label to be string, while a pandas col can be int
    # enforcing str conversion here
    x_ax = bqplot.Axis(
        label=x_col if isinstance(x_col, str) else str(x_col), scale=scales["x"]
    )
    x_ay = bqplot.Axis(
        label=y_col if isinstance(y_col, str) else str(y_col),
        scale=scales["y"],
        orientation="vertical",
    )

    # For some reason, Tooltips don't show up
    # TODO troubleshoot
    scatter.tooltip = bqplot.Tooltip(
        fields=["x", "y"], labels=["x", "y"], formats=["", ".2f"]
    )

    selected_scatter.tooltip = bqplot.Tooltip(
        fields=["x", "y"],
        labels=["x", "y"],
    )

    # Pass the Selector instance to the Figure
    fig = bqplot.Figure(
        marks=[scatter, selected_scatter],
        axes=[x_ax, x_ay],
        title=title,
        interaction=interacts.value,
    )

    def update_toggle_selector(*args):
        if sel.brushing is True:
            pass
        else:
            # Update the manual "selected" toggle
            idxs_to_toggle = scatter.selected
            if idxs_to_toggle is not None:
                idxs_to_toggle_globalized = df[df[label_col_name] == False].index[
                    idxs_to_toggle
                ]
                df.loc[idxs_to_toggle_globalized, label_col_name] = True

            # Update the manual "selected" toggle
            idxs_to_toggle = selected_scatter.selected
            if idxs_to_toggle is not None:
                idxs_to_toggle_globalized = df[df[label_col_name] == True].index[
                    idxs_to_toggle
                ]
                df.loc[idxs_to_toggle_globalized, label_col_name] = False

            # Refresh xy's
            # Tips from https://bqplot.readthedocs.io/en/latest/usage/updating-plots/ for hold_sync()
            with scatter.hold_sync():
                scatter.x = df.loc[df[label_col_name] == False, x_col]
                scatter.y = df.loc[df[label_col_name] == False, y_col]

            with selected_scatter.hold_sync():
                selected_scatter.x = df.loc[df[label_col_name] == True, x_col]
                selected_scatter.y = df.loc[df[label_col_name] == True, y_col]

    reset_zoom_btn = ipy.Button(
        description="Reset zoom",
        disabled=False,
        button_style="",  # 'success', 'info', 'warning', 'danger' or ''
        tooltip="Reset zoom",
        icon="arrows-alt",
    )

    def perform_zoom_reset(*args):
        # Reset the x and y axes on the figure
        fig.axes[0].scale.min = None
        fig.axes[1].scale.min = None
        fig.axes[0].scale.max = None
        fig.axes[1].scale.max = None

    reset_zoom_btn.on_click(perform_zoom_reset)
    reset_zoom_btn.layout.width = "120px"

    def get_counts():
        val_counts = df[label_col_name].value_counts()
        if True in val_counts.index:
            true_counts = val_counts.loc[True]
        else:
            true_counts = 0

        if False in val_counts.index:
            false_counts = val_counts.loc[False]
        else:
            false_counts = 0

        return f"""
        Num pts selected: {true_counts} <br>
        Num pts unselected: {false_counts}
        """

    html_div = ipy.HTML(get_counts())

    def currently_selected(*args):
        html_div.value = get_counts()

    sel.observe(currently_selected, "selected")

    # Instead of using a dropdown, use buttons
    # dropdown.observe(update_tool, "value")
    traitlets.link((interacts, "value"), (fig, "interaction"))

    sel.observe(update_toggle_selector, "brushing")

    return ipy.VBox(
        [fig, interacts, reset_zoom_btn, html_div],
    )
