"""
Doc string
"""
import math
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

from scipy import interpolate, signal
from scipy.stats import zscore

import nibabel as nb

from tftb.processing import smoothed_pseudo_wigner_ville as spwvd


frequency_bands = {
    "vlf": ["Very low frequency", (0.003, 0.04), "b"],
    "lf": ["Low frequency", (0.04, 0.15), "g"],
    "hf": ["High frequency", (0.15, 0.4), "r"],
}


class ProcessIBI:
    def __init__(self, peaks, frequency):
        self.peaks, self.frequency = peaks, frequency

    def calculate_ibi(self):
        """
        peak: a list of binary events
        list length == recording time
        """
        t = np.arange(0, len(self.peaks)) / self.frequency
        p_time = t[self.peaks == 1]
        self.raw_ibi = np.diff(p_time)

    def outlier_ibi(self, sd=2.5, n=2):
        """
        remove outlier
        detect outlier (>2.5 sd) and interpolate the signal
        n : int
            n occurence of this procedure
        """
        self.ibi = self.raw_ibi.copy()
        for i in range(n):
            # detect outlier (> 3 sd) and repalce with nan
            keep_idx = np.abs(zscore(self.ibi)) < sd
            self.time = np.cumsum(self.ibi)
            # interpolate nan
            f = interpolate.interp1d(
                self.time[keep_idx],
                self.ibi[keep_idx],
                "cubic",
                fill_value="extrapolate",
            )
            self.ibi = f(self.time)  # update

    def plot_ibi(self):
        fig = plt.figure(figsize=(10, 4))
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(self.time, self.raw_ibi, label="Original")
        ax.plot(self.time, self.ibi, label="After outlier detection")
        ax.set_title("Inter-beat interval")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("IBI (s)")
        ax.legend()
        return fig


class ContinuousHRV(ProcessIBI):
    def __init__(self, peaks, frequency):
        super(ContinuousHRV, self).__init__(peaks, frequency)

    def resample(self, fs=4):
        """
        resample ibi to certain frequency with
        spline, 3rd order interpolation function
        """
        self.resample_fs = fs
        time = np.cumsum(self.ibi)  # in seconds
        # detrend
        detrend_ibi = signal.detrend(self.ibi, type="linear")
        detrend_ibi -= detrend_ibi.mean()

        # interpolate function (spline, 3rd order)
        f = interpolate.interp1d(
            self.time, detrend_ibi, "cubic", fill_value="extrapolate"
        )
        sampling_time = 1 / self.resample_fs
        self.resample_time = np.arange(0, self.time[-1], sampling_time)
        self.ibi_resampled = f(self.resample_time)

        # remove mean
        self.ibi_resampled -= self.ibi_resampled.mean()

    def spwvd_power(self, tres=None, fres=None):
        """
        tres :
            desired time resolution in seconds
        fres :
            desired frequency resolution in hz
        """
        l = len(self.ibi_resampled)
        nfft = 2 ** _nextpower2(l)  # Next power of 2 from length of signal
        nfreqbin = int(nfft / 4)  # number of frequency bins
        print(nfreqbin)
        self.freq = (self.resample_fs / 2) * np.linspace(
            0, 1, nfreqbin
        )  # normalised frequency 1 is fs / 2

        if all(r is None for r in [tres, fres]):
            print("default")
            # from this paper https://doi.org/10.1016/S1566-0702(00)00211-3
            tres, fres = 4, 7
            twin_sample = 2 ** tres
            fwin_sample = 2 ** fres
        else:
            # smoothing window size in the number of samples
            delta_freq = np.diff(self.freq)[0]
            delta_time = np.diff(self.resample_time)[0]
            twin_sample = int(tres / delta_time)
            fwin_sample = int(fres / delta_freq)
            print(f"time smoothing window {twin_sample}, frequency smoothing window {fwin_sample}")

        # must be odd number
        self.twin_sample = round_up_to_odd(twin_sample)
        self.fwin_sample = round_up_to_odd(fwin_sample)

        # create smoothing window
        twindow = signal.hamming(self.twin_sample)
        fwindow = signal.hamming(self.fwin_sample)

        # power spectrum density spwvd
        self.trf = spwvd(
            self.ibi_resampled, self.resample_time, nfreqbin, twindow, fwindow
        )
        self.psd = self.trf ** 2

    def power_ampt(self):
        """
        group signal by frequency band along time
        """
        # extract power amptitude in high and low frequency band
        power = []
        for f in frequency_bands.keys():
            lb = frequency_bands[f][1][0]
            ub = frequency_bands[f][1][1]
            idx_freq = np.logical_and(self.freq >= lb, self.freq < ub)
            print(idx_freq.shape)
            print(self.psd[idx_freq, :].shape)
            dx = np.diff(self.freq)[0]
            amptitude = np.trapz(y=self.psd[idx_freq, :], dx=dx, axis=0)
            power.append(amptitude)
        self.vlf = power[0]
        self.lf = power[1]
        self.hf = power[2]

    def plot_spectrum(self):
        # plot power specturm density
        fig_psd = plt.figure(figsize=(10, 4))
        ax = fig_psd.add_subplot(1, 1, 1)
        ax.set_title("Time-frequency decomposition")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Frequency(Hz)")
        idx_freq = np.logical_and(self.freq >= 0, self.freq <= 0.4)
        cut_psd = self.psd[idx_freq, :]
        i = ax.pcolormesh(
            self.resample_time, self.freq[idx_freq], cut_psd, vmax=cut_psd.max() * 0.5
        )
        fig_psd.colorbar(i)
        return fig_psd

    def plot_HRV(self):
        # continuous HRV
        fig_hrv = plt.figure(figsize=(10, 4))
        ax = fig_hrv.add_subplot(1, 1, 1)
        ax.plot(self.resample_time, self.lf, label="LF-HRV", c="k", alpha=0.3)
        ax.plot(self.resample_time, self.hf, label="HF-HRV", c="r")
        ax.set_title("Continuous HRV")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Power")
        ax.legend()
        return fig_hrv


def _nextpower2(x):
    return 0 if x == 0 else math.ceil(math.log2(x))


def round_up_to_odd(f):
    return int(np.ceil(f) // 2 * 2 + 1)
