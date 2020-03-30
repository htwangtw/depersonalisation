#!/bin/bash

if [[ "x$SGE_ROOT" = "x" ]] ; then
  echo "not on the cluster"
else
  . ~/.bash_profile
fi  


TEMPLATE=$(readlink -f ${HOME}/projects/critchley_depersonalisation/code/templates/${1})
OUTPUT=$(readlink -f ${HOME}/projects/critchley_depersonalisation/scratch/${2})
SUBJ=${3}

cd ${HOME}/projects/critchley_depersonalisation/code

# generate regressors if not exist
if [[ ! -d "$OUTPUT/physio_measures/sub-${SUBJ}" ]]
then
  python ./process_hrv.py sub-${SUBJ}
else
fi

if [[ ! -d "$OUTPUT/regressors/sub-${SUBJ}" ]]
then
  python ./fsl_level1_regressors.py sub-${SUBJ}
else
fi

# make output dir
mkdir -p ${OUTPUT}/logs
cd $OUTPUT

# create fsf template
fsf=${OUTPUT}/sub-${SUBJ}/sub-${SUBJ}_level_1.fsf
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
else
  echo "Feat directory exist"
fi

# fake reg
./registration.sh FSL_task ${subj}