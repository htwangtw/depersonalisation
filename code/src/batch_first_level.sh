#!/bin/sh

# need to refector this code!!!!

SUBJ_LIST=$( sed -n -E "s/sub-(\S*)\>.*/\1/gp" \
             ~/projects/critchley_depersonalisation/code/participants.tsv )

TEMPLATE=/research/cisc2/projects/critchley_depersonalisation/code/templates/$1
OUTPUT=/research/cisc1/projects/critchley_depersonalisation/$2

mkdir -p ${OUTPUT}/logs
cd $OUTPUT
for SUBJ in ${SUBJ_LIST}; do
  # create fsf template
  echo "sub-${SUBJ}: create .fsf"
  mkdir -p ${OUTPUT}/sub-${SUBJ}
  
  path=~/projects/critchley_depersonalisation/data/derivatives/func_smooth-6mm/sub-${SUBJ}/func/*.gz
  N_VOL=$(fslinfo $path | grep dim4 | cut -d " " -f12)
  TR=$(fslinfo $path | grep pixdim4 | awk '{print $2}')
  for i in $TEMPLATE; do
    sed -e 's@SUBJECT@'$SUBJ'@g' \
        -e 's@VOLUMENUMBER@'$N_VOL'@g' \
        -e 's@TR@'$TR'@g' \
        -e 's@OUTPUT@'$OUTPUT'@g' \
        <$i> ${OUTPUT}/sub-${SUBJ}/sub-${SUBJ}_level_1.fsf
  done
  cd ${OUTPUT}/logs
  # send the preprocess job to cluster
  fsl_sub -N sub-${SUBJ} -l ${OUTPUT}/logs \
          feat ${OUTPUT}/sub-${SUBJ}/sub-${SUBJ}_level_1.fsf
done
