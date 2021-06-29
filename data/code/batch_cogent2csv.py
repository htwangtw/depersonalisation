import glob, os
import numpy as np
import pandas as pd

import seaborn as sns
import matplotlib.pyplot as plt

import h5py
from src.util import read_spike_mat, read_behav_mat, read_behav_congent

# misc
import warnings

# ran locally on the network drive; uploaded here for book keeping

freq = 1000
spikeMAT_path = "/mnt/s/psychiatry/Depersonalisation_Psychosis/SUBJECT_DATA/BEHAV_SPIKE_COLLATED/{}.mat"
dataMAT_path = (
    "/mnt/s/psychiatry/Depersonalisation_Psychosis/SUBJECT_DATA/BEHAV_SPIKE/{}/{}.mat"
)
dataCOG_path = (
    "/mnt/s/psychiatry/Depersonalisation_Psychosis/SUBJECT_DATA/BEHAV_SPIKE/{}/{}*.wri"
)

# Subject ID
with open("./spike_prepro_list.txt") as f:
    ID_list = [l.strip() for l in f.readlines()]


for subj in ID_list:
    # subj = ID_list[1]

    # compile all behavioural data logs into CSV
    print(subj)
    if subj[:4] == "HC16":  # cogent file only
        cog_path = glob.glob(dataCOG_path.format(subj, subj))
        df = read_behav_congent(cog_path[0])
    else:
        beh_path = dataMAT_path.format(subj, subj)
        df = read_behav_mat(beh_path)

    df.to_csv(
        "/home/bsms9gxx/Psychosis_Sarah/data/processed/behaviour/{}.csv".format(subj)
    )
