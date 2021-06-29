#!/bin/bash

if [[ "x$SGE_ROOT" = "x" ]] ; then
  echo "not on the cluster"
else
  . ${HOME}/.bash_profile
fi

PATH_REGRESSORS=$(readlink -f "${HOME}/projects/critchley_depersonalisation/code/group_design/groupmean_regressors.tsv")
PATH_CONTRAST=$(readlink -f "${HOME}/projects/critchley_depersonalisation/code/group_design/groupmean_contrast.tsv")

PATH_ANALYSIS=$(readlink -f "${HOME}/projects/critchley_depersonalisation/scratch/FSL_task")
PATH_OUTPUT=$(readlink -f "${HOME}/projects/critchley_depersonalisation/results/FSL_task")

cd ${HOME}/projects/critchley_depersonalisation/code

SUBJ_LIST=$( sed -n -E "s/sub-(\S*)\>.*/\1/gp" \
             participants.tsv )

# group level nuisance regressors
if [[ ! -f $PATH_REGRESSORS ]]
  then
  python ./src/fsl_group_regressors.py
fi

python ./src/fsl_group_nonpara.py -s $SUBJ_LIST -i $PATH_ANALYSIS -o $PATH_OUTPUT \
                              -r $PATH_REGRESSORS -c $PATH_CONTRAST \
                              -l "heart_wrt_note" "note_wrt_heart" \
                              -n task --oneSampleT