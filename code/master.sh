#!/bin/bash

cd ~/projects/critchley_depersonalisation
# . env/bin/activate

cd ~/projects/critchley_depersonalisation/code

SUBJ_LIST=$( sed -n -E "s/sub-(\S*)\>.*/\1/gp" \
             participants.tsv )

# generate nuisance and task regressors
# for subj in $SUBJ_LIST; do
#   qsub ./create_regressors.sh ${subj}
# done

# first level 
for subj in $SUBJ_LIST; do
  echo sub-$subj
  # HRV analysis
  # ./first_level.sh hrv_level1.fsf FSL_HRV_no_td ${subj}
  # ./registration.sh FSL_HRV_no_td ${subj}

  # task only
  # ./first_level.sh heart_wrt_note_level_1.fsf FSL_task ${subj}
  # ./registration.sh FSL_task ${subj}

  #PPI
  SEED_DIR=${HOME}/projects/critchley_depersonalisation/references/insular_masks
  for seed in $(ls ${SEED_DIR}/probmap-gm-*-insula*); do
    SEED_NAME=$(echo $(basename $seed) | cut -d - -f4 | cut -d . -f1)
    echo sub-${subj}_${SEED_NAME}
    qsub -o ${HOME}/logs -j y -N sub-${subj}_${SEED_NAME} \
        ./first_level_PPI.sh PPI_level1.fsf FSL_PPI-${SEED_NAME} ${subj} ${seed}  
  done
done

# for seed in lf_HRV hf_HRV bpm; do
#   qsub -o ${HOME}/logs -j y -N ${seed} \
#         ./master_grouplevel.sh ${seed}
# done