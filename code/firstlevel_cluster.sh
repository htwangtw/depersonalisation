#!/bin/bash
#$ -N fsl_lvl1
#$ -o /home/$USER/logs
#$ -j y

. ${HOME}/.bash_profile

ls ${HOME}/projects/
cd ${HOME}/projects/critchley_depersonalisation/code

SUBJ_LIST=$( sed -n -E "s/sub-(\S*)\>.*/\1/gp" \
             participants.tsv )
SEED_DIR=${HOME}/projects/critchley_depersonalisation/code/ppi_seeds

# i=$(expr $SGE_TASK_ID - 1)
# subj=${SUBJ_LIST[$i]}
for subj in $SUBJ_LIST; do
echo sub-$subj

# generate nuisance and task regressors
# bash ./create_regressors.sh ${subj}

# HRV analysis
# ./first_level.sh hrv_level1.fsf FSL_HRV_no_td ${subj}
# ./registration.sh FSL_HRV_no_td ${subj}

# task only
# ./first_level.sh heart_wrt_note_level_1.fsf FSL_task ${subj}
# ./registration.sh FSL_task ${subj}

#PPI
for seed in $(ls ${SEED_DIR}/*); do
  SEED_NAME=$(echo $(basename $seed) | cut -d - -f4 | cut -d . -f1)
  echo sub-${subj}_${SEED_NAME}
  bash ./first_level_PPI.sh PPI_level1.fsf FSL_PPI-${SEED_NAME} ${subj} ${seed}  
done

done