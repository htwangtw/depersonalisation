from nilearn import image
from nilearn.datasets import load_mni152_template
import os
import sys
from pathlib import Path
import nibabel as nb

home = str(Path.home())
p = Path(home + "/projects/critchley_depersonalisation/references/insular_masks")
mask_dir = (p / "prob" / "Hammers_mith-n30-regional-prob-maps-MNI152-SPM12" / "gm")
mni = load_mni152_template()
for seed_number in [86, 87, 88, 89, 92, 93]:
    source = list(mask_dir.glob(f"probmap-gm-r{seed_number}-*.nii.gz"))[0]
    re_nii = image.resample_to_img(str(source), mni)
    val = re_nii.get_fdata().max() / 2
    thresh = image.threshold_img(re_nii, val)
    data = thresh.get_fdata()
    bin_nii = nb.Nifti1Image((data > 0).astype(int),
                             header=thresh.header,
                             affine=thresh.affine)
    bin_nii.to_filename(source.name)
