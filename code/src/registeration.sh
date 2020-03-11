#!/usr/bin/env bash

# copy feat/reg folder to first level stats output
# performed on fMRIprep output
# Hao-Ting Wang 09 March 2020

# loaction of the fake registration results and all the first level stats
# reg_feat="/research/cisc1/projects/critchley_depersonalisation/fake_reg.feat"
reg_feat=${1?Error: no fake registreation feat dir give}

# parental dir of all the first level feat directory
feat_parents=${2?Error: no path given}
FEAT_DIRS=$feat_parents/*/*.feat
# FSLDIR=$FSLDIR

# update the transformation matrix
# only need to perform on the fake registeration once
# rm -r $reg_feat/reg/*.mat
# cp $FSLDIR/etc/flirtsch/ident.mat $reg_feat/reg/example_func2standard.mat
# cp $FSLDIR/etc/flirtsch/ident.mat $reg_feat/reg/standard2example_func.mat

# populate the reg dir to each subject
for subject_feat in $(ls -d $FEAT_DIRS); do
    # replace the original standard to meanfunc
    rm -rf $subject_feat/reg
    cp -r $reg_feat/reg $subject_feat
    rm -rf $subject_feat/reg/standard.nii.gz
    ln -s $subject_feat/mean_func.nii.gz $subject_feat/reg/standard.nii.gz
    updatefeatreg $subject_feat
done
