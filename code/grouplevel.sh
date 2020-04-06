#!/bin/bash

if [[ "x$SGE_ROOT" = "x" ]] ; then
  echo "not on the cluster"
else
  . ~/.bash_profile
fi  

SEED_NAME=${1}

cd ~/projects/critchley_depersonalisation/code

SUBJ_LIST=$( sed -n -E "s/sub-(\S*)\>.*/\1/gp" \
             participants.tsv )

# group level nuisance regressors
PATH_REGRESSORS=$(readlink -f $HOME/projects/critchley_depersonalisation/results/mri_regressors.tsv.tsv)
if [[ ! -f $PATH_REGRESSORS ]]
  then
  python ./fsl_group_regressors.py
fi

PATH_ANALYSIS=$(readlink -f "${HOME}/projects/critchley_depersonalisation/scratch/FSL_PPI-$SEED_NAME")
PATH_OUTPUT=$(readlink -f "${HOME}/projects/critchley_depersonalisation/results/FSL_PPI-$SEED_NAME")
python ./fsl_group_nonpara.py -s $SUBJ_LIST -i $PATH_ANALYSIS -o $PATH_OUTPUT -r $PATH_REGRESSORS