t1w=$(ls /home/hw1012/datasets/sussex/data/sub-*/ses-*/anat/sub-*_T1w.nii.gz)

for f in $t1w; do
    chmod +w $f
    mri_deface $f \
    ~/.local/etc/mri_deface/talairach_mixed_with_skull.gca \
    ~/.local/etc/mri_deface/face.gca \
    $f
    chmod -w $f
done