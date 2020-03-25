#!/bin/sh

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

  # simple task contrast
  # ./first_level.sh hrv_level1.fsf FSL_HRV ${subj}
  # ./registration.sh FSL_tasks ${subj}
done


PATH_REGRESSORS=$(readlink -f ~/projects/critchley_depersonalisation/results/group_confounds.tsv)
# group level nuisance regressors
if [[ ! -f $PATH_REGRESSORS ]]
  then
  python ./fsl_group_regressors.py
fi

# ROI based analysis
PATH_ANALYSIS=$(readlink -f ~/projects/critchley_depersonalisation/scratch/FSL_HRV)
python ./group_level_FSL.py -s $SUBJ_LIST -i $PATH_ANALYSIS -r $PATH_REGRESSORS 

# whole brain analysis
# python group_level_FSL.py FSL_task ../reference/gray_matter_mask.nii.gz
