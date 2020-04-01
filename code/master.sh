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
  for seed in anterior_short_gyrus_L anterior_short_gyrus_R middle_short_gyrus_L middle_short_gyrus_R anterior_inferior_cortex_L anterior_inferior_cortex_R; do
    if [[ "x$SGE_ROOT" = "x" ]] ; then
      ./first_level_PPI.sh PPI_level1.fsf FSL_PPI-$seed ${subj} $seed
    else
      qsub -o ${HOME}/logs -N sub-${subj}_${seed} \
           ./first_level_PPI.sh PPI_level1.fsf FSL_PPI-$seed ${subj} $seed
    fi  
  done

done