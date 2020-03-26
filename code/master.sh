#!/bin/bash

cd ~/projects/critchley_depersonalisation/code

SUBJ_LIST=$( sed -n -E "s/sub-(\S*)\>.*/\1/gp" \
             participants.tsv )

for subj in $SUBJ_LIST; do
  echo $subj
  # generate regressors
  # python ./process_hrv.py sub-${subj}
  # python ./fsl_regressors.py sub-${subj}

  # HRV analysis
  # ./first_level.sh hrv_level1.fsf FSL_HRV ${subj}
  # ./registration.sh FSL_HRV ${subj}

  # HRV and task interaction
  ./first_level.sh hrv_with_task_level1.fsf FSL_full_HRV_PPI ${subj}
  ./registration.sh FSL_full_HRV_PPI ${subj}
done


PATH_REGRESSORS=$(readlink -f ~/projects/critchley_depersonalisation/results/group_confounds.tsv)
# group level nuisance regressors
if [[ ! -f $PATH_REGRESSORS ]]
  then
  python ./fsl_group_regressors.py
fi

PATH_ANALYSIS=$(readlink -f ~/projects/critchley_depersonalisation/scratch/FSL_HRV)
python ./fsl_group_nonpara.py -s $SUBJ_LIST -i $PATH_ANALYSIS -r $PATH_REGRESSORS 

PATH_ANALYSIS=$(readlink -f ~/projects/critchley_depersonalisation/scratch/FSL_full_HRV_PPI)
python ./fsl_group_nonpara.py -s $SUBJ_LIST -i $PATH_ANALYSIS -r $PATH_REGRESSORS 
