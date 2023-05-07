import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype
import traitlets
import bqplot
import ipywidgets as ipy
from collections import OrderedDict
from typing import Any, Text, Optional
from __version import __version__

# Single source versioning
# Learnt from https://stackoverflow.com/a/7071358/13095028


def label(
    df: pd.DataFrame,
    x_col: Any = None,
    y_col: Any = None,
    labels=None,
    default_label=None,
    label_col_name: Text = "selected",
    title: Text = "nblabeller",
):
    if label_col_name is None:
        label_col_name = "selected"

    if x_col is None:
        x_col = "x"

    if y_col is None:
        y_col = "y"

    if labels is None:
        # bool threw errors somewhere in bqplot
        labels = ["false", "true"]

    assert len(labels) == len(set(labels)), "Duplicated values passed in `labels`!"

    if len(labels) > 10:
        raise ValueError(
            "Max number of labels supported is 10 at this point in time, currently have {len(labels) labels}"
        )

    if default_label is None:
        default_label = labels[0]

    assert x_col in df.columns, f"x_col: {x_col} not in df!"
    assert y_col in df.columns, f"y_col: {y_col} not in df!"

    assert default_label in labels

    label_class_dropdown = ipy.Dropdown(
        description="Label", options=labels, value=default_label
    )

    # Determine best dtype for the labels
    # https://www.geeksforgeeks.org/how-to-convert-to-best-data-types-automatically-in-pandas/
    best_dtype = pd.Series(labels).convert_dtypes().dtype

    if label_col_name in df.columns:
        pass
    else:
        df.loc[:, label_col_name] = pd.Series(
            [default_label] * len(df), dtype=best_dtype
        )

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

    # Configure color scale
    scales["color"] = bqplot.OrdinalColorScale(
        domain=labels,
        # CATEGORY10 only has 10! TODO expand later
        colors=bqplot.CATEGORY10[: len(labels)],
    )

    scatter = bqplot.Scatter(
        x=df[x_col],
        y=df[y_col],
        scales=scales,
        color=df[label_col_name],
        # For some reason, opacity doesn't work
        # TODO troubleshoot
        # opacity=np.array([0.05] * len(df.loc[df[label_col_name] == default_label])),
    )

    sel = bqplot.interacts.BrushSelector(
        x_scale=scales["x"],
        y_scale=scales["y"],
        # marks required so that the mark itself can have
        # .selected attribute
        marks=[scatter],
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
    # scatter.tooltip = bqplot.Tooltip(
    #     fields=["x", "y"], labels=["x", "y"], formats=["", ".2f"]
    # )

    # Pass the Selector instance to the Figure
    fig = bqplot.Figure(
        marks=[scatter],
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
                current_label_class = label_class_dropdown.value

                df.loc[idxs_to_toggle, label_col_name] = current_label_class
                # Refresh plot
                # Tips from https://bqplot.readthedocs.io/en/latest/usage/updating-plots/ for hold_sync()
                with scatter.hold_sync():
                    scatter.color = df["selected"].tolist()
            else:
                pass

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
        ans_string = ""
        for i in labels:
            if i in val_counts.index:
                class_counts = val_counts.loc[i]
            else:
                class_counts = 0

            ans_string += f"{i}: {class_counts}<br>"

        return ans_string

    html_div = ipy.HTML(get_counts())

    def currently_selected(*args):
        html_div.value = get_counts()

    sel.observe(currently_selected, "selected")
    traitlets.link((interacts, "value"), (fig, "interaction"))

    sel.observe(update_toggle_selector, "brushing")

    return ipy.VBox(
        [label_class_dropdown, fig, interacts, reset_zoom_btn, html_div],
    )
