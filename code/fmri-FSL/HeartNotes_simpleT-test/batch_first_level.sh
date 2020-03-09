#!/bin/bash
# do not run this script on the cluster
# cluster submission for running first level analysis for a list of subjects as task array

# source /mnt/nfs2/bsms/bsms9gxx/.bash_profile

cd ~/projects/critchley_depersonalisation/analysis

subject=$( sed -n -E \
  "s/sub-(\S*)\>.*/\1/gp" \
  participants.tsv )
cd ~/projects/critchley_depersonalisation/analysis/FSL/HeartNotes_first_level
TEMPLATE=template.fsf

# to-do: load subject with multiple runs

for SUBJ in $subject; do
    # create fsf template
    echo "sub-$SUBJ: create .fsf"
    path=~/projects/critchley_depersonalisation/data/derivatives/func_smooth-6mm/sub-$SUBJ/func/*.gz
    N_VOL=$(fslinfo $path | grep dim4|cut -d " " -f12)
    TR=$(fslinfo $path | grep pixdim4 | awk '{print $2}')
    RUN=1
    for i in $TEMPLATE; do
        sed -e 's@SUBJECT@'$SUBJ'@g' \
        -e 's@VOLUMENUMBER@'$N_VOL'@g' \
        -e 's@TR@'$TR'@g' \
        -e 's@RUN@'$RUN'@g' \
        <$i> sub-${SUBJ}_HeartNotes_first_level.fsf
    done
    # send the preprocess job to cluster
    fsl_sub feat sub-${SUBJ}_HeartNotes_first_level.fsf
done
