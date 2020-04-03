#!/bin/bash
if [[ "x$SGE_ROOT" = "x" ]] ; then
  echo "not on the cluster"
else
  . ~/.bash_profile
fi  
SUBJ=${1}
cd ${HOME}/projects/critchley_depersonalisation/code
python ./process_hrv.py sub-${SUBJ}
python ./fsl_level1_regressors.py sub-${SUBJ}