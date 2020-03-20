#!/bin/sh

TEMPLATE=$(readlink -f ${HOME}/projects/critchley_depersonalisation/code/templates/${1})
OUTPUT=$(readlink -f ${HOME}/projects/critchley_depersonalisation/scratch/${2})
REG_FEAT=$(readlink -f ${HOME}/projects/critchley_depersonalisation/scratch/fake_reg.feat)
SUBJ=${3}

fsf=${OUTPUT}/sub-${SUBJ}/sub-${SUBJ}_level_1.fsf
mkdir -p ${OUTPUT}/logs
cd $OUTPUT
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
        <$i> $fsf
  done
fi

# run feat
FEAT_DIR=${OUTPUT}/sub-${SUBJ}/sub-${SUBJ}.feat
if [[ ! -d "$FEAT_DIR" ]]; then
  feat ${OUTPUT}/sub-${SUBJ}/sub-${SUBJ}_level_1.fsf
  echo "run feat"
else
  echo "Feat directory exist"
fi

# copy registration files
if [[ -d ${FEAT_DIR}/reg ]]; then
  rm -rf ${FEAT_DIR}/reg
fi
echo "copy reg"
cp -r ${REG_FEAT}/reg ${FEAT_DIR}
rm -rf ${FEAT_DIR}/reg/standard.nii.gz
ln -s ${FEAT_DIR}/mean_func.nii.gz ${FEAT_DIR}/reg/standard.nii.gz
updatefeatreg ${FEAT_DIR}