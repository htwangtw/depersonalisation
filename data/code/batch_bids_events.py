import os, glob
import pandas as pd

os.chdir("/its/home/bsms9gxx/projects/critchley_depersonalisation/data")
beh_csv = "sourcedata/behaviour/*.csv"
path_beh = glob.glob(beh_csv)

for i in path_beh:
    df = pd.read_csv(i, index_col=0)
    df.loc[:, "sixth_vol":] /= 1000
    df["onset"] = (
        df.loc[:, "startHeartBeatMonitoring"] - df.loc[:, "sixth_vol"] + 2.52 * 5
    )
    df["duration"] = (
        df.loc[:, "endHeartBeatMonitoring"] - df.loc[:, "startHeartBeatMonitoring"]
    )
    bids_id = i.split("_")[-1].split(".csv")[0]
    tsv_path = glob.glob(
        f"sub-{bids_id}/func/sub-{bids_id}_task-heartbeat_run-?_events.tsv"
    )
    if len(tsv_path) > 1:
        print(bids_id, "two runs")  # only for sub-9734
        df_run1, df_run2 = df.iloc[:27, :], df.iloc[27:, :]
        for t in tsv_path:
            if t.split("run-")[-1][0] == "1":
                df_run1.to_csv(t, sep="\t", index=False, float_format="%.3f")
            else:
                df_run2.to_csv(t, sep="\t", index=False, float_format="%.3f")
    else:
        df.to_csv(tsv_path[0], sep="\t", index=False, float_format="%.3f")
