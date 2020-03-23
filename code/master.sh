#!/bin/sh

cd ~/projects/critchley_depersonalisation/code

SUBJ_LIST=$( sed -n -E "s/sub-(\S*)\>.*/\1/gp" \
             participants.tsv )

for subj in $SUBJ_LIST; do
  echo $subj
  # python ./process_hrv.py sub-${subj}
  # python ./fsl_regressors.py sub-${subj}
  bash ./first_level.sh hrv_level1.fsf FSL_HRV ${subj}
  bash ./registration.sh FSL_HRV ${subj}
done

# group level analysis
# if [[ ! -d ~/projects/critchley_depersonalisation/results/group_confounds.tsv ]]
#   then
#   python ./fsl_group_regressors.py
# fi
