"""
usage:
    python physio_qa.py $subject

Convert list of peaks into
1. inter beat interval
2. time-frequecny spectrumgram
3. continuous HRV in different frequency band
4. export figures of IBI, time-frequency representation
   and HRV for visual inspection
"""
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np
import nibabel as nb

from src.hrv import ContinuousHRV

# load subject
subject = sys.argv[1]
spike_fs = 1010.10

# set paths
home = str(Path.home())
p = Path(home + "/projects/critchley_depersonalisation")
target_path = p / "scratch" / "physio_measures" / subject
physio_path = list(p.glob(f"data/{subject}/func/*_task-heartbeat_run-1_physio.tsv.gz"))[0]
vol_path = (p / "data" / "derivatives" /
        "fmriprep-1.5.1rc2" / subject / "func" /
        f"{subject}_task-heartbeat_run-1_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz")

# load file
df_physio = pd.read_csv(physio_path, sep='\t', compression='gzip')
start = df_physio.index[df_physio['trigger']==1][0]
end = df_physio.index[df_physio['trigger']==1][-1]

# chop to the length of the experiment
beats = df_physio[start:end].cardiac_event.values

if subject == 'sub-9575':  #big drift after task ended; detrend
    cut = int(df_physio.index[df_physio['stim']==1][-1] + 35 / spike_fs)
    beats[cut - start:] = 0

# continuous HRV
calculate_hrv = ContinuousHRV(peaks=beats, frequency=spike_fs)
calculate_hrv.calculate_ibi()
calculate_hrv.outlier_ibi(sd=3, n=2)
if sum(calculate_hrv.ibi > 1.5) + sum(calculate_hrv.ibi < 0.3) > 0:
    # use more agressive cut off for people with too many out of normal range
    calculate_hrv.outlier_ibi(sd=2.5, n=2) # run again
fig_ibi = calculate_hrv.plot_ibi()
calculate_hrv.resample()
calculate_hrv.spwvd_power()
fig_psd = calculate_hrv.plot_spectrum()
calculate_hrv.power_ampt()
fig_hrv = calculate_hrv.plot_HRV()

# Save the processed HRV/ IBI data
lf, hf = calculate_hrv.lf, calculate_hrv.hf
ibi = calculate_hrv.ibi
t = calculate_hrv.resample_time

if not os.path.isdir(target_path):
    os.makedirs(target_path)

for i, fig in enumerate((fig_ibi, fig_psd, fig_hrv)):
    fig.savefig(target_path / f"{subject}_task-heartbeat_run-1_fig-{i + 1}.png")

np.savetxt(target_path / f"{subject}_task-heartbeat_run-1_desc-ibi_physio.tsv",
            ibi)

df = pd.DataFrame(np.array([lf, hf]).T, columns=['lf_HRV', 'hf_HRV'], index=t)
out_file = target_path / f"{subject}_task-heartbeat_run-1_desc-continuousHRV_physio.tsv"
df.to_csv(out_file, sep='\t')