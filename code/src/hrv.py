import numpy as np
import pandas as pd

import matplotlib.pyplot as plt 

from scipy import interpolate, signal
from scipy.stats import zscore

import nibabel as nb

from tftb.processing import smoothed_pseudo_wigner_ville as spwvd


frequency_bands = {'vlf': ['Very low frequency', (0.003, 0.04), 'b'],
                   'lf': ['Low frequency', (0.04, 0.15), 'g'],
                   'hf': ['High frequency', (0.15, 0.4), 'r']}
                   
class ProcessIBI:
    def __init__(self, peaks, freqency):
        self.peaks, self.frequency = peaks, freqency

    def calculate_ibi(self):
        '''
        peak: a list of binary events
        list length == recording time
        '''
        t = np.arange(0, len(self.peaks)) / self.frequency 
        p_time = t[self.peaks==1]
        self.raw_ibi = np.diff(p_time)

    def outlier_ibi(self, sd=2.5, n=2, plot=False):
        '''
        remove outlier
        detect outlier (>2.5 sd) and interpolate the signal
        n : int
            n occurence of this procedure
        '''
        self.ibi = self.raw_ibi.copy()
        for i in range(n):
            # detect outlier (> 3 sd) and repalce with nan
            keep_idx = np.abs(zscore(self.ibi)) < sd
            self.time = np.cumsum(self.ibi)
            # interpolate nan
            f = interpolate.interp1d(self.time[keep_idx], 
                                     self.ibi[keep_idx], 
                                     "cubic", fill_value="extrapolate")
            self.ibi = f(self.time)  # update

        if plot:
            fig_ibi = self.plot_ibi()
            fig_ibi.show()
            return fig_ibi

    def plot_ibi():
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
    def __init__(self, peaks, freqency):
        super(ContinuousHRV, self).__init__(peaks, freqency)
        self.raw_ibi = super().calculate_ibi()
        self.ibi = super().outlier_ibi()

    def resample(self, fs=4):
        '''
        resample ibi to certain frequency with 
        spline, 3rd order interpolation function
        '''
        self.resample_fs = fs
        time = np.cumsum(self.ibi) # in seconds 
        # detrend
        detrend_ibi = signal.detrend(self.ibi, type='linear')
        detrend_ibi -= detrend_ibi.mean()

        # interpolate function (spline, 3rd order)
        f = interpolate.interp1d(self.time, detrend_ibi, 
                                "cubic", 
                                fill_value="extrapolate")  
        sampling_time = 1 / self.resample_fs
        self.resample_time = np.arange(0, self.time[-1], sampling_time)
        self.ibi_resampled = f(self.resample_time) 

        # remove mean
        self.ibi_resampled -= self.ibi_resampled.mean()   

    def spwvd_power(self, tres=None, fres=None):
        '''
        tres : 
            desired time resolution in seconds 
        fres : 
            desired frequency resolution in hz
        '''
        l = len(self.ibi_resampled) 
        nfft = 2 ** _nextpower2(l) # Next power of 2 from length of signal
        nfreqbin = int(nfft / 4)  # number of frequency bins
        self.freq = (self.resample_fs / 2) * np.linspace(0, 1, nfreqbin) # normalised frequency 1 is fs / 2

        if all(r is None for r in [tres, fres]):
            print('default')
            # from this paper https://doi.org/10.1016/S1566-0702(00)00211-3
            twin_sample = 16
            fwin_sample = 128
        else:
            # smoothing window size in the number of samples 
            delta_freq = np.diff(freq)[0]
            twin_sample = int(self.resample_fs * tres)
            fwin_sample = int(fres / delta_freq)

        # must be odd number
        self.twin_sample = round_up_to_odd(twin_sample)
        self.fwin_sample = round_up_to_odd(fwin_sample)

        # create smoothing window
        twindow = signal.hamming(self.twin_sample)
        fwindow = signal.hamming(self.fwin_sample)

        # power spectrum density spwvd
        self.trf = spwvd(self.resample_rr, self.resample_time, 
                         nfreqbin, twindow, fwindow) 
        self.psd = self.trf ** 2   

    def power_ampt(self):
        """
        group signal by frequency band along time
        """
        # extract power amptitude in high and low frequency band
        self.vlf, self.lf, self.hf = np.nan, np.nan, np.nan
        for f, output in zip(frequency_bands.keys(), 
                             [self.vlf, self.lf, self.hf]):
            lb = frequency_bands[f][1][0]
            ub = frequency_bands[f][1][1]
            idx_freq = np.logical_and(self.freq >= lb, self.freq < ub)
            dx = np.diff(self.freq)[0]
            amptitude = np.trapz(y=self.psd[idx_freq, :], 
                                 dx=dx, axis=0) 
            output = amptitude

    def plot_spectrum():
        # plot power specturm density
        fig_psd = plt.figure(figsize=(10, 4))
        ax = fig_psd.add_subplot(1, 1, 1)
        ax.set_title("Time-frequency decomposition")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Frequency(Hz)")
        idx_freq = np.logical_and(self.freq >= 0, self.freq <= 0.4)
        cut_psd = self.psd[idx_freq, :]
        i = ax.pcolormesh(self.resample_time, 
                          self.freq[idx_freq], 
                          cut_psd, 
                          vmax=cut_psd.max() * 0.5) 
        fig_psd.colorbar(i)
        return fig_psd

    def plot_HRV():
        # continuous HRV
        fig_hrv = plt.figure(figsize=(10, 4))
        ax = fig_hrv.add_subplot(1, 1, 1)
        ax.plot(self.resample_time, self.lf, 
                label="LF-HRV", c='k', alpha=0.3)
        ax.plot(self.resample_time, self.hf, 
                label="HF-HRV", c='r')
        ax.set_title("Continuous HRV")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Power")
        ax.legend()
        return fig_hrv

# def prepro_rr(beats, spike_fs, graphs=False):
#     print('Calculate IBI')
#     # calculate IBI of the whole serie
#     orig_ibi = calculate_ibi(beats, frequency=spike_fs)    
#     print('Process IBI')
#     # detect outlier (abs(z)> 3) and interpolate
#     ibi = outlier_ibi(orig_ibi, sd=3, n=2)  # save this version
    
#     if sum(ibi > 1.5) + sum(ibi < 0.3) > 0:  
#         # use more agressive cut off for people with too many out of normal range
#         ibi = outlier_ibi(ibi, sd=2.5, n=2) # run again
    
#     print('Time frequency analysis...')
#     # power info
#     t_fs = 4
#     ibi_interp, t = resample_rr(ibi, fs=t_fs)  # upsample RR interval to 4 Hz
#     psd, freq = spwvd_power(ibi_interp, t)

#     # Detrend the first 10s to avoid the edge effect
#     detrend_idx = np.where(t > 10)[0][0]
#     psd[:, :detrend_idx] = 0

#     print('Extract power specturm...')
#     # Extract frequency bands
#     power = power_ampt(psd, freq, t)
    
#     if graphs:
#         # plot IBI
#         fig_ibi = plt.figure(figsize=(10, 4))
#         ax = fig_ibi.add_subplot(1, 1, 1)
#         ax.plot(np.cumsum(ibi), orig_ibi, label="Original")
#         ax.plot(np.cumsum(ibi), ibi, label="After outlier detection")
#         ax.set_title("Inter-beat interval")
#         ax.set_xlabel("Time (s)")
#         ax.set_ylabel("IBI (s)")
#         ax.legend()
#         plt.close()
        
#         # plot power specturm density
#         fig_psd = plt.figure(figsize=(10, 4))
#         ax = fig_psd.add_subplot(1, 1, 1)
#         ax.set_title("Time-frequency decomposition")
#         ax.set_xlabel("Time (s)")
#         ax.set_ylabel("Frequency(Hz)")
#         idx_freq = np.logical_and(freq >= 0, freq <= 0.4)
#         i = ax.pcolormesh(t, freq[idx_freq], psd[idx_freq, :], 
#                           vmax=psd[idx_freq, :].max() * 0.5) 
#         fig_psd.colorbar(i)
#         plt.close()
        
#         # continuous HRV
#         fig_hrv = plt.figure(figsize=(10, 4))
#         ax = fig_hrv.add_subplot(1, 1, 1)
#         ax.plot(t, power['lf'], 
#                 label="LF-HRV", c='k', alpha=0.3)
#         ax.plot(t, power['hf'], 
#                 label="HF-HRV", c='r')
#         ax.set_title("Continuous HRV")
#         ax.set_xlabel("Time (s)")
#         ax.set_ylabel("Power")
#         ax.legend()
#         plt.close()
#         return ibi, power['lf'], power['hf'], t, (fig_ibi, fig_psd, fig_hrv)
#     else:
#         return ibi, power['lf'], power['hf'], t


# def window_hrv(path, vol_path, tr, spike_fs, window_size=18):
#     def spike_quality(df_physio , n_vol, spike_fs, tr):
#         first_stim = df_physio[df_physio.stim == 1].index.tolist()[0]
#         first_stim /= spike_fs  # conver to sec
#         print(f'sixth volume logged at {first_stim} sec in spike file')
#         print(f'number of volume in prepro data: {n_vol}')
        
#         # check if trigger channel is empty
#         tr_onset = df_physio[df_physio.trigger == 1].index.tolist()
#         n_trigger = len(tr_onset) - 1  # final one is the offset of the final vol

#         if n_vol != n_trigger:
#             print('unusal total vol in spike recording')
#             print('starting spike trigger incorrect, align to vol 6')
#             tr_ref = 5
#             tr_onset = []
#             for i in range(n_vol + 1): 
#                 if i < tr_ref: 
#                     tr_onset.append( first_stim - tr  * (tr_ref - i) )
#                 else:
#                     tr_onset.append( first_stim + tr * (i - tr_ref) ) 
#         else:
#             print('align TR with spike trigger channel')
#             # find the actual trigger when the reference volume was logged
#             # assuming the reference was always delayed
#             tr_onset = np.array(tr_onset) / spike_fs
#             tr_ref = np.argwhere(tr_onset <= first_stim)[-1]
#             tr_ref = int(tr_ref)
#             tr_onset = tr_onset.tolist()
#             print(f'starting at vol number {tr_ref + 1}, total vol in spike recording: {n_trigger}')
#         return tr_ref, n_vol, tr_onset
#     df_physio = pd.read_csv(path, sep='\t', compression='gzip')
#     n_vol = nb.load(str(vol_path)).shape[-1]
#     tr_ref, n_vol, tr_onset = spike_quality(df_physio, vol_path, spike_fs, tr)
    
#     beats = df_physio.cardiac_event.values
#     (ibi, ibi_timestamp), (amptitudes, t) = prepro_rr(beats, spike_fs)
#     tr_ref, n_vol, tr_onset = spike_quality(df_physio, vol_path, spike_fs, tr)

#     for i in range(tr_ref, n_vol):  # start the calculation at the sixth vol
#         # use the stimulus channel identified vol on set 
#         # if the trigger channel is errous
#         tr_start = tr_onset[i]
#         tr_end = tr_start + tr
#         # get a 18s window from the middle of the volume
#         half_window = np.rint(window_size / 2)
#         mid_tr = (tr_end + tr_start) / 2
#         window_start = mid_tr - half_window
#         window_end = mid_tr + half_window
        
#         # get heart data in the window
#         ibi_start = np.where(ibi_timestamp > window_start)[0][0]
#         ibi_end = np.where(ibi_timestamp < window_end)[0][-1]
#         ibi = full_ibi_inter[ibi_start : ibi_end]
#         n_peak = len(ibi)
#         rmssd = np.mean(np.diff(ibi * 1000) ** 2) ** 0.5  # HRV in milliseconds
#         bpm = n_peak / window_size * 60
        
#         # get power info
#         a_start = np.where(t > window_start)[0][0]
#         a_end = np.where(t < window_end)[0][-1]
#         lf = amptitudes['lf']
#         hf = amptitudes['hf']
       
#         hrv_stats.loc[i, "lf_power"] = lf
#         hrv_stats.loc[i, "hf_power"] = hf
#         hrv_stats.loc[i, "rmssd"] = rmssd
#         hrv_stats.loc[i, "bpm"] = bpm
#     return hrv_stats, df_physio

def _nextpower2(x):
    import math
    return 0 if x == 0 else math.ceil(math.log2(x))

def round_up_to_odd(f):
    return int(np.ceil(f) // 2 * 2 + 1)