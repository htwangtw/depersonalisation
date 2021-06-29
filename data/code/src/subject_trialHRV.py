import glob, os
from pathlib import Path

import numpy as np
import pandas as pd

import seaborn as sns
import matplotlib.pyplot as plt

from scipy.stats import zscore
from scipy import interpolate, signal

from tftb.processing import smoothed_pseudo_wigner_ville as spwvd

# misc
import warnings

home = str(Path.home())
p = Path(home + "/projects/critchley_depersonalisation")
participants = pd.read_csv(p / "data" / "participants.tsv", sep="\t")
ID_list = participants.query("task_heartbeat_trialHRV > 0").participant_id.tolist()

spike_fs = 1010


def calculate_ibi(peaks, frequency=100):
    """
    peak: a list of binary events
    list length == recording time
    """
    t = np.arange(0, len(peaks)) / frequency
    p_time = t[peaks == 1]
    ibi = np.diff(p_time)
    return ibi


frequency_bands = {
    "vlf": ["Very low frequency", (0.003, 0.04), "b"],
    "lf": ["Low frequency", (0.04, 0.15), "g"],
    "hf": ["High frequency", (0.15, 0.4), "r"],
}

for subject in ID_list[0:1]:
    print(subject)
    event_path = (
        p / "data" / subject / "func" / f"{subject}_task-heartbeat_run-1_events.tsv"
    )
    physio_path = (
        p / "data" / subject / "func" / f"{subject}_task-heartbeat_run-1_physio.tsv.gz"
    )
    df = pd.read_csv(event_path, sep="\t")
    df_physio = pd.read_csv(physio_path, sep="\t", compression="gzip")

    # trial trigger time
    total_trials = df.shape[0]
    total_sync = df_physio["stim"].sum()

    # assert total_sync == (total_trials + 1), "{}: weird num of trials".format(subject)
    time = np.array(df_physio.index.tolist()) / spike_fs  # unit in second
    bin_stim = df_physio["stim"].values.astype("bool")

    # calculate IBI of the whole serie
    full_ibi = calculate_ibi(df_physio.cardiac_event.values, frequency=spike_fs)
    ibi_timestamp = np.cumsum(full_ibi)

    # detect outlier (>2.5 sd) and repalce with nan
    keep_idx = zscore(full_ibi) < 2.5

    # interpolate nan
    f = interpolate.interp1d(
        ibi_timestamp[keep_idx], full_ibi[keep_idx], "cubic", fill_value="extrapolate"
    )
    full_ibi_inter = f(ibi_timestamp)

    # resample rr interval to 4 hz
    fs = 4
    time = np.cumsum(full_ibi_inter)
    f = interpolate.interp1d(time, full_ibi_inter, "cubic")
    t = np.arange(time[0], time[-1], 1 / fs)
    rr = f(t)
    rr -= rr.mean()  # detrend

    # power spectrum density spwvd
    nfft = 1
    while nfft < nperseg:
        nfft *= 2
    freq = fs / 2 * np.linspace(0, 1, nfft / 4)
    twin = 4
    fwin = 7
    twindow = signal.hamming(2 ** twin + 1)
    fwindow = signal.hamming(2 ** fwin + 1)
    tfr = spwvd(rr, t, int(nfft / 4), twindow, fwindow)
    psd = tfr ** 2

    # Detrend the first 10s to avoid the edge effect
    detrend_idx = np.where(t > 10)[0][0]
    psd[:, :detrend_idx] = 0

    # extract relevant frequency band
    for f in ["lf", "hf"]:
        lb = frequency_bands[f][1][0]
        ub = frequency_bands[f][1][1]
        idx_freq = np.logical_and(freq >= lb, freq < ub)
        amptitude = np.trapz(y=psd[idx_freq, :], dx=np.diff(freq)[0], axis=0)
        plt.plot(t, amptitude)

    hrv_stats = pd.DataFrame(
        None,
        columns=["lf_power", "hf_power", "rmssd", "n_peak", "bpm", "qc"],
        index=range(0, total_sync - 1),
    )

    for i in range(1, total_sync):  # the first on set was the 6th volume of the scanner

        t_start = time[bin_stim][i]
        # The behavioural spreadsheet starts from the first behavioural trial
        df_idx = i - 1
        dur = df.loc[df_idx, "duration"]
        t_end = t_start + dur

        # Create a window between start and end of heart monitoring in ibi
        ibi_start = np.where(ibi_timestamp > t_start)[0][0]
        ibi_end = np.where(ibi_timestamp < t_end)[0][-1]

        ibi = full_ibi_inter[ibi_start : ibi_end + 1]
        n_peak = len(ibi)
        rmssd = np.mean(np.diff(ibi * 1000) ** 2) ** 0.5  # HRV in milliseconds
        bpm = n_peak / dur * 60

        hrv_stats.loc[df_idx, "rmssd"] = rmssd
        hrv_stats.loc[df_idx, "n_peak"] = n_peak
        hrv_stats.loc[df_idx, "bpm"] = bpm
        if rmssd > 270:  # flag unusual trials
            flag = 1
        elif np.isnan(rmssd):
            flag = 1
        else:
            flag = 0
        hrv_stats.loc[df_idx, "qc"] = flag

        # power spectrum measure
        hrv_stats.loc[df_idx, "lf_amplitude"] = lf
        hrv_stats.loc[df_idx, "hf_amplitude"] = hf

    # impute flagged trials with median
    if hrv_stats["qc"].sum() > 0:
        val = hrv_stats.loc[:, "lf_power":"bpm"].values.astype(float)
        lst_qc = hrv_stats.qc.tolist()
        val[np.array(lst_qc) == 1, :] = np.nan
        median = np.nanmedian(val, axis=0)
        val[np.array(lst_qc) == 1, :] = median
        hrv_stats.loc[:, "lf_power":"bpm"] = val

        print("{} unusual trials: {}".format(sum(lst_qc), subject))
        with open("./bad_quality_spike_csv.txt", "a") as f:
            f.write(subject + "\n")
    hrv_stats = pd.concat([df, hrv_stats], axis=1)
    hrv_stats.to_csv(
        p
        / "scratch"
        / "trial_HRV"
        / f"{subject}_task-heartbeat_run-1_desc-HRV_events.tsv",
        sep="\t",
    )
