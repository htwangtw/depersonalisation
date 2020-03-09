import os
from pathlib import Path

import pandas as pd
import numpy as np
from scipy import signal

from src.hrv import window_hrv


# load file
# File created through spike export to spreadsheet function
# resample to frequecny = 100 hz
# method: linear
home = str(Path.home())
p = Path(home + "/projects/critchley_depersonalisation")
print(p / "data" /"participants.tsv")
participants = pd.read_csv(p / "analysis" /"participants.tsv", sep='\t')

# check partcipant.json for participant.tsv codes
pass_qa = participants.query("task_heartbeat_physio > 0").participant_id.tolist()
# pass_qa = participants.query("task_heartbeat_physio == 3").participant_id.tolist()

for subject in pass_qa:
    print(subject)
    path = list(p.glob(f"data/{subject}/func/{subject}_task-heartbeat_run-1_physio.tsv.gz"))
    path = path[0]
    vol_path = (p / "data" / "derivatives" /
                "fmriprep-1.5.1rc2" / subject / "func" /
                f"{subject}_task-heartbeat_run-1_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz")
    confounds_path = (p / "data" / "derivatives" /
            "fmriprep-1.5.1rc2" / subject / "func" /
            f"{subject}_task-heartbeat_run-1_desc-confounds_regressors.tsv")
    event_path = (p / "data" / subject / "func" /
                  f"{subject}_task-heartbeat_run-1_events.tsv")
    target_path = p / "data" / "derivatives" / "func_smooth-6mm" / subject / "func"

    if not os.path.isdir(target_path):
        os.makedirs(target_path)
    out_file = target_path / f"{subject}_task-heartbeat_run-1_desc-hrv_timeseries.tsv"

    # HRV regressors (low and high frequency HRV)
    hrv_stats, _ = window_hrv(path, vol_path, tr=2.52, spike_fs=1010.1)
    hrv_stats.to_csv(out_file,
                    sep='\t', index=False, float_format='%.5f')

    # BPM regressors

    # save an fsl ready version
    for measure in ['lf_power', 'hf_power', 'bpm']:
        out_file = target_path / f"{subject}_task-heartbeat_run-1_desc-{measure}_regressors.tsv"
        fsl_ver = hrv_stats.loc[5:, measure]
        fsl_ver.to_csv(out_file, sep='\t', header=False, index=False, float_format='%.5f')

    # # FSL task regressors
    # events = pd.read_csv(event_path, sep='\t')
    # for c, name in zip([1, 2], ['heart', 'notes']):
    #     condition = events.query(f"condition == {c}")[['onset', 'duration']]
    #     condition['col'] = 1
    #     condition['onset'] -= 2.52 * 5  # input epi volume was chopped
    #     out_file = target_path / f"{subject}_task-heartbeat_run-1_desc-{name}_regressors.tsv"
    #     condition.to_csv(out_file, sep='\t', header=False, index=False, float_format='%.5f')

    # # confounds regressors
    # confounds = pd.read_csv(confounds_path, sep='\t')
    # var = ["framewise_displacement",
    #         "a_comp_cor_00",
    #         "a_comp_cor_01",
    #         "a_comp_cor_02",
    #         "a_comp_cor_03",
    #         "a_comp_cor_04",
    #         "a_comp_cor_05",
    #         "cosine00",
    #         "cosine01",
    #         "cosine02",
    #         "cosine03",
    #         "trans_x",
    #         "trans_y",
    #         "trans_z",
    #         "rot_x",
    #         "rot_y",
    #         "rot_z"]
    # fsl_ver = confounds.loc[5:, var]
    # out_file = target_path / f"{subject}_task-heartbeat_run-1_desc-FSLconfounds_regressors.tsv"
    # fsl_ver.to_csv(out_file, sep='\t', header=False, index=False, float_format='%.5f')
    print("done")
