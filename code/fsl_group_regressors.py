import os
from pathlib import Path

import pandas as pd
import numpy as np

home = str(Path.home())
p = Path(home + "/projects/critchley_depersonalisation")
participants = pd.read_csv(p / "code" /"participants.tsv", sep='\t', index_col=0)
regressors = participants.iloc[:, :2]
regressors["mean_fd"] = np.nan

for idx, row in regressors.iterrows():
    subject = idx
    print(subject)
    path = list(p.glob(f"data/derivatives/fmriprep-1.5.1rc2/{subject}/func/{subject}_task-heartbeat_run-1_desc-confounds_regressors.tsv"))
    confounds_path = path[0]
    confounds = pd.read_csv(confounds_path, sep='\t')
    mean_fd = confounds.loc[5:, "framewise_displacement"].mean()
    regressors.loc[idx, "mean_fd"] = mean_fd

stats = pd.read_csv(p / "results" / "full_sample_stats.tsv", sep="\t", index_col=0)
cds = stats.CDS_State

# concatenate cds and the rest
regressors = pd.concat([regressors, cds], axis=1, join="inner")

# create z test var
for c in ["control", "patient"]:
    regressors[c] = 0
    regressors[c][regressors.group == c] = 1
regressors.group = 1

# z score
z_convert = ["age", "mean_fd", "CDS_State"]
regressors[z_convert] -= regressors[z_convert].mean()
regressors[z_convert] /= regressors[z_convert] .std(ddof=0)

# sort by group
regressors = regressors.sort_index()
regressors = regressors.sort_values(by=["patient"])

# save file
out_file = p / "results" / "mri_regressors.tsv"
regressors.to_csv(out_file, sep="\t", float_format="%.5f")