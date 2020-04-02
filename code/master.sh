#!/bin/bash

cd ~/projects/critchley_depersonalisation
# . env/bin/activate

cd ~/projects/critchley_depersonalisation/code

SUBJ_LIST=$( sed -n -E "s/sub-(\S*)\>.*/\1/gp" \
             participants.tsv )

# generate regressors
for subj in $SUBJ_LIST; do
  qsub ./create_regressors.sh ${subj}
done

for subj in $SUBJ_LIST; do
  ls -l ~/sub-$subj*
  qstat | grep sub-$subj | wc -l
done
# first level 
for subj in $SUBJ_LIST; do
  echo sub-$subj
  # HRV analysis
  # ./first_level.sh hrv_level1.fsf FSL_HRV_no_td ${subj}
  # ./registration.sh FSL_HRV_no_td ${subj}

  # HRV and task 
  # ./first_level.sh hrv_with_task_level1.fsf FSL_task_HRV ${subj}
  # ./registration.sh FSL_task_HRV ${subj}

  # task only
  # ./first_level.sh heart_wrt_note_level_1.fsf FSL_task ${subj}
  # ./registration.sh FSL_task ${subj}

  #PPI
  SEED_DIR=${HOME}/projects/critchley_depersonalisation/references/insular_masks
  for seed in $(ls ${SEED_DIR}/probmap-gm-*-insula*); do
    SEEDPATH=$(python ./generate_seed.py sub-$subj ${seed})
    SEED_NAME=$(basename $seed)
    if [[ "x$SGE_ROOT" = "x" ]] ; then
      ./first_level_PPI.sh PPI_level1.fsf FSL_PPI-${SEED_NAME} ${subj} ${SEEDPATH}
    else
      qsub -o ${HOME}/logs -j y -N sub-${subj}_${SEED_NAME} \
          ./first_level_PPI.sh PPI_level1.fsf FSL_PPI-${SEED_NAME} ${subj} ${SEEDPATH}
    fi  
  done
done


# for seed in lf_HRV hf_HRV bpm; do
#   qsub -o ${HOME}/logs -j y -N ${seed} \
#         ./master_grouplevel.sh ${seed}
# done
