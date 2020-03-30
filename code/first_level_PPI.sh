#!/bin/bash

if [[ "x$SGE_ROOT" = "x" ]] ; then
  echo "not on the cluster"
else
  . ~/.bash_profile
fi  

TEMPLATE=$(readlink -f ${HOME}/projects/critchley_depersonalisation/code/templates/${1})
OUTPUT=$(readlink -f ${HOME}/projects/critchley_depersonalisation/scratch/${2})
SUBJ=${3}
SEED=${4}


fsf=${OUTPUT}/sub-${SUBJ}/sub-${SUBJ}_level_1.fsf
# create fsf template
if [[ -f $fsf ]]
then
  echo "fsf file exist!"
else
  echo "sub-${SUBJ}: create .fsf"
  mkdir -p ${OUTPUT}/sub-${SUBJ}
  
  path=~/projects/critchley_depersonalisation/data/derivatives/func_smooth-6mm/sub-${SUBJ}/func/*.gz
  N_VOL=$(fslinfo $path | grep ^dim4 | awk '{print $2}')
  TR=$(fslinfo $path | grep pixdim4 | awk '{print $2}')
  echo $N_VOL
  for i in $TEMPLATE; do
    sed -e 's@SUBJECT@'$SUBJ'@g' \
        -e 's@VOLUMENUMBER@'$N_VOL'@g' \
        -e 's@TR@'$TR'@g' \
        -e 's@OUTPUT@'$OUTPUT'@g' \
        -e 's@SEED@'$SEED'@g' \
        -e 's@HOME@'$HOME'@g' \
        <$i> $fsf
  done
fi

# run feat
FEAT_DIR=${OUTPUT}/sub-${SUBJ}/sub-${SUBJ}.feat
if [[ ! -d "$FEAT_DIR" ]]
then
  export SGE_ROOT=""
  feat ${OUTPUT}/sub-${SUBJ}/sub-${SUBJ}_level_1.fsf
  echo "run feat"

  # cd ${HOME}/projects/critchley_depersonalisation/code
  # # fake reg
  # ./registration.sh ${OUTPUT} ${subj}
else
  echo "Feat directory exist"
fi