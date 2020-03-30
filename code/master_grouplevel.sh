#!/bin/bash

if [[ "x$SGE_ROOT" = "x" ]] ; then
  echo "not on the cluster"
else
  . ~/.bash_profile
fi  

cd ~/projects/critchley_depersonalisation/code

SUBJ_LIST=$( sed -n -E "s/sub-(\S*)\>.*/\1/gp" \
             participants.tsv )

# group level nuisance regressors
PATH_REGRESSORS=$(readlink -f $HOME/projects/critchley_depersonalisation/results/group_confounds.tsv)
if [[ ! -f $PATH_REGRESSORS ]]
  then
  python ./fsl_group_regressors.py
fi

# group level
for seed in pag insularL insularR; do
  echo $seed
  PATH_ANALYSIS=$(readlink -f "${HOME}/projects/critchley_depersonalisation/scratch/FSL_PPI-$seed")
  python ./fsl_group_nonpara.py -s $SUBJ_LIST -i $PATH_ANALYSIS -r $PATH_REGRESSORS
done