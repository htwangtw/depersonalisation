import warnings

import numpy as np
import pandas as pd
from scipy.ndimage import label
import neo.io


def group_peaks(ch_event):
    """
    The peak detection/stimulus event in spike returns floats between 0 and 5
    Here we group collections of peaks (value close to 5, but there are exceptions)
    and take the middle index as peak index
    """
    # make sure the input is 1D

    # round the event channel to the closest integer
    event_bin = (np.rint(ch_event)).astype(int)
    # initialize output
    output = np.zeros(event_bin.shape, dtype=int)

    # threshold - back ground is always 0
    threshold = 1
    # print(np.unique(event_bin))
    # label groups of sample that belong to the same peak
    peak_groups, n_groups = label(event_bin > threshold)

    # iterate through groups and take the mean as peak index
    # skip the first unique number (zero)
    # as zero means background
    for i in np.unique(peak_groups)[1:]:
        peak_group = np.where(peak_groups == i)
        output[np.rint(np.median(peak_group)).astype(int)] = 1
    return output


def read_smr(filename):
    """
    helper function to read signal from .smr file (Spike2)

    Need to be modified to read obitory smr files
    """
    with warnings.catch_warnings():  # avoid warning in Spike2IO
        warnings.simplefilter("ignore")
        reader = neo.io.Spike2IO(filename=filename, try_signal_grouping=False)
        segment = reader.read_segment()
    return segment
