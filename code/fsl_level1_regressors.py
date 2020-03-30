"""
usage:
    python fsl_regressors.py $subject
"""
import os
import sys
from pathlib import Path
import json

import pandas as pd
import numpy as np
from scipy import signal, interpolate
from scipy.stats import zscore

import nibabel as nb

print("create regressors")
subject = sys.argv[1]
# load file
# File created through spike export to spreadsheet function
# resample to frequecny = 100 hz
# method: linear
home = str(Path.home())
p = Path(home + "/projects/critchley_depersonalisation")
vol_path = (p / "data" / subject / "func" /
            f"{subject}_task-heartbeat_run-1_bold.json")
confounds_path = (p / "data" / "derivatives" /
                  "fmriprep-1.5.1rc2" / subject / "func" /
                  f"{subject}_task-heartbeat_run-1_desc-confounds_regressors.tsv")
event_path = (p / "data" / subject / "func" /
              f"{subject}_task-heartbeat_run-1_events.tsv")
hrv_path = (p / "scratch" / "physio_measures" / subject / 
            f"{subject}_task-heartbeat_run-1_desc-continuousHRV_physio.tsv")
ibi_path = (p / "scratch" / "physio_measures" / subject / 
            f"{subject}_task-heartbeat_run-1_desc-ibi_physio.tsv")
target_path = (p / "scratch" / "regressors" / subject)

# predefined var
n_dummy = 5
confound_vars = (p / "code" / "confound_regressors.txt")
confound_vars = [line.rstrip('\n') for line in open(confound_vars)]

# create dir
if not os.path.isdir(target_path):
    os.makedirs(target_path)
out_file = target_path / f"{subject}_task-heartbeat_run-1_desc-hrv_timeseries.tsv"

# load TR and dimension info
with open(vol_path) as f:
    data = json.load(f)

tr = data['RepetitionTime']

try:
    n_vol = data['dcmmeta_shape'][-1]
except KeyError:
    vol_path = (p / "data" / subject / "func" /
                f"{subject}_task-heartbeat_run-1_bold.nii.gz")
    n_vol = nb.load(str(vol_path)).shape[-1]

# HRV regressors (low and high frequency HRV)
hrv = pd.read_csv(hrv_path, sep='\t', index_col=0)
x = hrv.index.to_numpy()
y = hrv.values.T
# interpolate to TR
f = interpolate.interp1d(x, y, kind='slinear', fill_value='extrapolate')
new_time = np.arange(0, n_vol, 1) * tr
hrv_tr_match = f(new_time)
for i, name in enumerate(hrv.columns):
    power = hrv_tr_match[i, 5:]  # trim off the first five volumes
    power = zscore(np.log10(power))  # take log and normalise
    out_file = target_path / f"{subject}_task-heartbeat_run-1_desc-{name}_regressors.tsv"
    np.savetxt(str(out_file), power, fmt='%10.5f')

# BPM regressors
ibi = np.loadtxt(ibi_path)
t_beats = np.cumsum(ibi)
window = 20
bpm = []
for t in new_time[5:]: # trim off 5 vol
    start = t - window / 2
    if start < 0:
        start = 0
    end = t + window / 2
    if end > new_time[-1]:
        end = new_time[-1]
    idx = np.logical_and(t_beats >= start, t_beats <= end)
    bpm.append(sum(idx) / ((end - start) / 60))
out_file = target_path / f"{subject}_task-heartbeat_run-1_desc-bpm_regressors.tsv"
np.savetxt(str(out_file), np.array(bpm), fmt='%10.5f')

# FSL task regressors
events = pd.read_csv(event_path, sep='\t')
for c, name in zip([1, 2], ['heart', 'notes']):
    condition = events.query(f"condition == {c}")[['onset', 'duration']]
    condition['col'] = 1
    condition['onset'] -= tr * n_dummy  # input epi volume was chopped
    out_file = target_path / f"{subject}_task-heartbeat_run-1_desc-{name}_regressors.tsv"
    condition = condition.to_numpy()
    np.savetxt(str(out_file), condition, fmt='%10.5f')

# confounds regressors
confounds = pd.read_csv(confounds_path, sep='\t')
fsl_ver = confounds.loc[n_dummy:, confound_vars]
fsl_ver = fsl_ver.to_numpy()
out_file = target_path / f"{subject}_task-heartbeat_run-1_desc-FSLconfounds_regressors.tsv"
np.savetxt(str(out_file), fsl_ver, fmt='%10.5f')

# ppi seeds
from nilearn import input_data

func_filename = str(p / "data" / "derivatives" / 
                 "func_smooth-6mm" / subject / "func" /
                 f"{subject}_task-heartbeat_run-1_space-MNI152NLin2009cAsym_desc-preproc-fwhm6mm_bold.nii.gz")
coords = [(-2, -14, -32)]
seed_masker = input_data.NiftiSpheresMasker(coords, radius=8, t_r=tr, 
                                            detrend=True, standardize=True)
seed_time_series = seed_masker.fit_transform(func_filename, confounds=fsl_ver)
out_file = target_path / f"{subject}_task-heartbeat_run-1_desc-pag_regressors.tsv"
np.savetxt(str(out_file), seed_time_series, fmt='%10.5f')

nii_masks = p / "references" / "insular_masks" 
nii_masks = list(nii_masks.glob("juelich_GM_insular_prob90_[LR].nii.gz"))
for m in nii_masks:
    hemi = m.name.split("_")[-1].split('.')[0]
    m = str(m)
    seed_masker = input_data.NiftiMasker(m, t_r=tr, detrend=True)
    seed_time_series = seed_masker.fit_transform(func_filename, confounds=fsl_ver)
    seed_time_series = seed_time_series.mean(axis=0)
    out_file = target_path / f"{subject}_task-heartbeat_run-1_desc-insular{hemi}_regressors.tsv"
    np.savetxt(str(out_file), seed_time_series, fmt='%10.5f')       

print("done")