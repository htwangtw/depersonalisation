#!/bin/bash
#$ -N fsl_lvl1
#$ -o /home/$USER/logs
#$ -j y

. ${HOME}/.bash_profile


cd ${HOME}/projects/critchley_depersonalisation/

source env/bin/activate

cd code

SUBJ_LIST=$( sed -n -E "s/sub-(\S*)\>.*/\1/gp" \
             participants.tsv )
SEED_DIR=${HOME}/projects/critchley_depersonalisation/code/ppi_seeds

for subj in $SUBJ_LIST; do
    echo sub-$subj

    # generate nuisance and task regressors
    bash ./src/create_regressors.sh ${subj}

    # hrv
    ./src/first_level_model.sh hrv_level1.fsf FSL_hrv ${subj}
    ./src/registration.sh ../scratch/FSL_hrv ${subj}

    # task only
    ./src/first_level_model.sh heart_wrt_note_level_1.fsf FSL_task_new ${subj}
    ./src/registration.sh ../scratch/FSL_task_new ${subj}

done
