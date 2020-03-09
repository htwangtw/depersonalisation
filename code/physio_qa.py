import os
from pathlib import Path

import pandas as pd
import numpy as np

import nibabel as nb

from src.hrv import prepro_rr


home = str(Path.home())
p = Path(home + "/projects/critchley_depersonalisation")
participants = pd.read_csv(p / "analysis" / "participants.tsv", sep='\t')

pass_qa = participants.participant_id.tolist()
spike_fs = 1010.10
tr_ref = 5  # stim channel marks the onset of the 6th volume

for n_sub, subject in enumerate(pass_qa):
    print(f"{subject} : {n_sub + 1} / {len(pass_qa)}")
    target_path = p / "results" / "physio_measures" / subject
    physio_path = list(p.glob(f"data/{subject}/func/*_task-heartbeat_run-1_physio.tsv.gz"))[0]
    vol_path = (p / "data" / "derivatives" /
            "fmriprep-1.5.1rc2" / subject / "func" /
            f"{subject}_task-heartbeat_run-1_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz")

    df_physio = pd.read_csv(physio_path, sep='\t', compression='gzip')
    start = df_physio.index[df_physio['trigger']==1][0]
    end = df_physio.index[df_physio['trigger']==1][-1]

    # chop to the length of the experiment
    beats = df_physio[start:end].cardiac_event.values

    if subject == 'sub-9575':  #big drift after task ended; detrend
        cut = int(df_physio.index[df_physio['stim']==1][-1] + 35 / spike_fs)
        beats[cut - start:] = 0

    ibi, lf, hf, t, (fig_ibi, fig_psd, fig_hrv) = prepro_rr(beats, spike_fs, graphs=True)

    # save files
    if not os.path.isdir(target_path):
        os.makedirs(target_path)

    for i, fig in enumerate((fig_ibi, fig_psd, fig_hrv)):
        fig.savefig(target_path / f"{subject}_task-heartbeat_run-1_fig-{i + 1}.png")

    np.savetxt(target_path / f"{subject}_task-heartbeat_run-1_desc-ibi_physio.tsv",
               ibi)

    df = pd.DataFrame(np.array([lf, hf]).T, columns=['lf_HRV', 'hf_HRV'], index=t)
    out_file = target_path / f"{subject}_task-heartbeat_run-1_desc-continuousHRV_physio.tsv"
    df.to_csv(out_file, sep='\t')

    print("done")
