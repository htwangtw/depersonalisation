import os
from pathlib import Path

import pandas as pd
import numpy as np

home = str(Path.home())
p = Path(home + "/projects/critchley_depersonalisation")
print(p / "data" /"participants.tsv")
participants = pd.read_csv(p / "data" /"participants.tsv", sep='\t')

# check partcipant.json for participant.tsv codes
pass_qa = participants.query("task_heartbeat_physio > 0").copy()
# drop columns
pass_qa = pass_qa.iloc[:, :5].drop('PxID', axis=1)
pass_qa["mean_fd"] = np.nan
for idx, row in pass_qa.iterrows():
    subject = row.participant_id
    print(subject)
    path = list(p.glob(f"data/derivatives/fmriprep-1.5.1rc2/{subject}/func/{subject}_task-heartbeat_run-1_desc-confounds_regressors.tsv"))
    confounds_path = path[0]
    confounds = pd.read_csv(confounds_path, sep='\t')
    mean_fd = confounds.loc[5:, "framewise_displacement"].mean()
    pass_qa.loc[idx, "mean_fd"] = mean_fd


# add zscores for FSL group analysis
mean = pass_qa.loc[:, ['age', 'mean_fd']].mean()
std = pass_qa.loc[:, ['age', 'mean_fd']].std()
z_score = (pass_qa.loc[:, ['age', 'mean_fd']] - mean) / std
z_score.columns = ['z_age', 'z_mean_fd']
full = pd.concat([pass_qa, z_score], axis=1)

# save file
out_file = p / "results" / "group_confounds.tsv"
full.to_csv(out_file, sep='\t', index=False, float_format='%.5f')
