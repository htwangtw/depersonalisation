import os
from pathlib import Path

import pandas as pd
import numpy as np

home = str(Path.home())
p = Path(home + "/projects/critchley_depersonalisation")
print(p / "data" /"participants.tsv")
participants = pd.read_csv(p / "code" /"participants.tsv", sep='\t')
participants = participants.iloc[:, :4]
participants["mean_fd"] = np.nan

for idx, row in participants.iterrows():
    subject = row.participant_id
    print(subject)
    path = list(p.glob(f"data/derivatives/fmriprep-1.5.1rc2/{subject}/func/{subject}_task-heartbeat_run-1_desc-confounds_regressors.tsv"))
    confounds_path = path[0]
    confounds = pd.read_csv(confounds_path, sep='\t')
    mean_fd = confounds.loc[5:, "framewise_displacement"].mean()
    participants.loc[idx, "mean_fd"] = mean_fd


# add zscores for FSL group analysis
mean = participants.loc[:, ['age', 'mean_fd']].mean()
std = participants.loc[:, ['age', 'mean_fd']].std()
z_score = (participants.loc[:, ['age', 'mean_fd']] - mean) / std
z_score.columns = ['z_age', 'z_mean_fd']
full = pd.concat([participants, z_score], axis=1)

# save file
out_file = p / "results" / "group_confounds.tsv"
full.to_csv(out_file, sep='\t', index=False, float_format='%.5f')