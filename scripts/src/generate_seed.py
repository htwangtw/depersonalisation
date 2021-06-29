# generate seed
import os
import sys
from pathlib import Path
import json

import numpy as np

from nilearn import input_data

subject = sys.argv[1]
mask = Path(sys.argv[2])

home = str(Path.home())
p = Path(home + "/projects/critchley_depersonalisation")
vol_path = p / "data" / subject / "func" / f"{subject}_task-heartbeat_run-1_bold.json"
target_path = p / "scratch" / "regressors" / subject
confounds_path = (
    p
    / "scratch"
    / "regressors"
    / subject
    / f"{subject}_task-heartbeat_run-1_desc-FSLconfounds_regressors.tsv"
)
func_filename = str(
    p
    / "data"
    / "derivatives"
    / "func_smooth-6mm"
    / subject
    / "func"
    / f"{subject}_task-heartbeat_run-1_space-MNI152NLin2009cAsym_desc-preproc-fwhm6mm_bold.nii.gz"
)

label = mask.name.split(os.sep)[-1].split(".")[0]
out_file = target_path / f"{subject}_task-heartbeat_run-1_desc-{label}_regressors.tsv"

if not out_file.is_file():
    label = mask.name.split(os.sep)[-1].split(".")[0]
    mask = str(mask)

    # load TR and dimension info
    with open(vol_path) as f:
        data = json.load(f)

    tr = data["RepetitionTime"]

    # extract signal
    seed_masker = input_data.NiftiMasker(mask, detrend=True, t_r=tr)
    seed_time_series = seed_masker.fit_transform(
        func_filename, confounds=str(confounds_path)
    )
    seed_time_series = seed_time_series.mean(axis=1)
    mean_seed = seed_time_series.mean()
    seed_time_series -= mean_seed  # mean centre
    np.savetxt(str(out_file), seed_time_series, fmt="%10.5f")
print(str(out_file))
