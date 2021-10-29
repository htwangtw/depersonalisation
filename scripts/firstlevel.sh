#!/bin/bash
#$ -N fsl_lvl1
#$ -o /home/$USER/logs
#$ -j y
#$ -t 1-49
#$ -tc 20

. ${HOME}/.bash_profile


i=$((SGE_TASK_ID - 1))

cd ${HOME}/projects/critchley_depersonalisation/

source env/bin/activate

cd scripts

SUBJ_LIST=($( sed -n -E "s/sub-(\S*)\>.*/\1/gp" \
             participants.tsv ))
SEED_DIR=${HOME}/projects/critchley_depersonalisation/references/ppi_seeds


subj=${SUBJ_LIST[${i}]}
echo sub-$subj

bash ./src/create_regressors.sh ${subj}
 # hrv
./src/first_level_model.sh hrv_level1.fsf FSL_hrv ${subj}
./src/registration.sh ../scratch/FSL_hrv ${subj}

# task only
./src/first_level_model.sh heart_wrt_note_level_1.fsf FSL_task ${subj}
./src/registration.sh ../scratch/FSL_task ${subj}
