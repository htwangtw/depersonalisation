#!/bin/bash

OUTPUT=$(readlink -f ${HOME}/projects/critchley_depersonalisation/scratch/${1})
SUBJ=${2}

REG_FEAT=$(readlink -f ${HOME}/projects/critchley_depersonalisation/scratch/fake_reg.feat)
FEAT_DIR=${OUTPUT}/sub-${SUBJ}/sub-${SUBJ}.feat
# copy registration files
if [[ -d ${FEAT_DIR}/reg ]]; then
  rm -rf ${FEAT_DIR}/reg
fi
echo "copy reg"
cp -r ${REG_FEAT}/reg ${FEAT_DIR}
rm -rf ${FEAT_DIR}/reg/standard.nii.gz
ln -s ${FEAT_DIR}/mean_func.nii.gz ${FEAT_DIR}/reg/standard.nii.gz
updatefeatreg ${FEAT_DIR}