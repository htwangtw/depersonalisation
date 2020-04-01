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
  for hemi in L R; do
    for seed in anterior_short_gyrus middle_short_gyrus anterior_inferior_cortex; do
      if [[ "x$SGE_ROOT" = "x" ]] ; then
        ./first_level_PPI.sh PPI_level1.fsf FSL_PPI-${seed}_${hemi} ${subj} ${seed}_${hemi}
      else
        qsub -o ${HOME}/logs -j y -N sub-${subj}_${seed}_${hemi} \
            ./first_level_PPI.sh PPI_level1.fsf FSL_PPI-${seed}_${hemi} ${subj} ${seed}_${hemi}
      fi  
    done
  done

done

for hemi in L R; do
  for seed in anterior_short_gyrus middle_short_gyrus anterior_inferior_cortex; do
    qsub -o ${HOME}/logs -j y -N ${seed}_${hemi} \
          ./master_grouplevel.sh ${seed}_${hemi}
    
  done
done