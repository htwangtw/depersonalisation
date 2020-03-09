
# loaction of the fake registration results and all the first level stats
reg_feat="/research/cisc1/projects/critchley_depersonalisation/fake_reg.feat"
FEAT_DIRS="/research/cisc1/projects/critchley_depersonalisation/brain_HRV/HRV/*.feat"
# FSLDIR=$FSLDIR

# copy the feat/reg 
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
