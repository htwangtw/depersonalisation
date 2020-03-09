import os
from pathlib import Path
import json
import pandas as pd
import numpy as np
import nibabel as nb
from scipy import interpolate, signal
import matplotlib.pyplot as plt
from src.spike import group_peaks, read_smr

home = str(Path.home())
p = Path(home + "/projects/critchley_depersonalisation/data")
participants = pd.read_csv(p /"participants.tsv", sep='\t')
pass_qa = participants.query("task_heartbeat_physio > 0 ").participant_id.tolist()

# correct for 50 msec flag in spike file
# The correction value was inpscted through raw spike file
# it's not quite the same as 50
correction = 44
# correct for the average error per TR
# calculated from files with healty trigger recording
tr_error = -2e-05

n = 0
for subject in pass_qa:
    n += 1
    print(f"{n} / {len(pass_qa)}, {subject}")
    # save the file with binirised heart beat and stimulus onset tag
    path = p / "derivatives" / "physio_spike2" / f"{subject}_task-heartbeat_run-1_physio.smr"
    bn = path.name.split('physio.smr')[0]
    vol_path = p / subject / "func" / f"{subject}_task-heartbeat_run-1_bold.json"
    
    with open(vol_path) as f:
        data = json.load(f)
    tr = data['RepetitionTime']

    try:
        n_vol = data['dcmmeta_shape'][-1]
    except KeyError:
        vol_path = p / subject / "func" / f"{subject}_task-heartbeat_run-1_bold.nii.gz"
        n_vol = nb.load(str(vol_path)).shape[-1]

    # load the four channels we need
    segment = read_smr(str(path))
    cardiac_event = segment.analogsignals[0]
    stim = segment.analogsignals[1]
    cardiac = segment.analogsignals[2]
    trigger = segment.events[0]
    spike_fs = np.round(cardiac.sampling_rate, 2)

    # create a data frame to store the physio data
    df = pd.DataFrame(cardiac.squeeze(), 
                      index=np.array(cardiac.times), columns=['cardiac'])

    # binarise the cardiac event and stim channels
    for name, ch in zip(['cardiac_event', 'stim'], [cardiac_event, stim]):
        # peak detection on the spike created detection channel resample to match the cardiac signal
        f = interpolate.interp1d(ch.times, ch.squeeze(), 
                                "nearest", fill_value="extrapolate")
        signal = f(cardiac.times)
        df[name] = group_peaks(signal.squeeze())

    time = df.index.tolist()
    time_trigger = np.array(trigger.times.simplified)

    # estimate starting of the first volume by the 6th vol trigger log
    vol6_time = df[df.stim==1].index[0]
    vol6_time -= correction / 1000  # correct for the square wave
    est_start = vol6_time - tr * 5

    df['trigger'] = 0
    spike_n_trigger = len(time_trigger)

    if (spike_n_trigger - 1)  != n_vol:
        print(f"bad trigger(spike/nifti): {spike_n_trigger}/{n_vol}")
        # estmate scan end time
        est_end = est_start + tr * n_vol + n_vol * tr_error

        # find the proximate time on the cardiac recording channel
        idx_trigger_first = np.where(time >= est_start)[0][0]
        idx_trigger_last = np.where(time <= est_end)[0][-1]
        start = time[idx_trigger_first]
        end = time[idx_trigger_last]

        # estimate all triggers
        time_trigger = np.linspace(start, end, n_vol + 1)

    # find the closest time on the cardiac recording channel
    for t in time_trigger:
        idx = np.where((time - t) <= 0)[0][-1]
        df.loc[time[idx], 'trigger'] = 1
    # save physio
    bn = path.name.split('physio.smr')[0]
    out_path = p / subject / "func" / f"{bn}physio.tsv" 
    df.to_csv(out_path, sep="\t", index=False)
    os.system(f"gzip {out_path}")

    # json
    json_paths = str(p / subject / "func" / f"{bn}physio.json")
    vol1_time = df[df.trigger==1].index[0]
    new_start_time = df.index[0] - vol1_time

    # edit the start time in json; align to the first volume
    with open(json_paths) as json_file:
        data = json.load(json_file)
        data['StartTime'] = str(new_start_time)
        data["SamplingFrequency"] = str(spike_fs)[:-3]

    # save json
    with open(json_paths, 'w') as outfile:
        json.dump(data, outfile, indent=4)