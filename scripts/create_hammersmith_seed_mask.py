import os
import sys
import re
from pathlib import Path

import nibabel as nb
from nilearn import image

home = str(Path.home())
p = Path(home + "/projects/critchley_depersonalisation/references/insular_masks")
mask_dir = (p / "prob" / "Hammers_mith-n30-regional-prob-maps-MNI152-SPM12" / "gm")
target_space = Path(home + "/projects/critchley_depersonalisation/data/derivatives/func_smooth-6mm/sub-10048/func/sub-10048_task-heartbeat_run-1_space-MNI152NLin2009cAsym_desc-preproc-fwhm6mm_bold.nii.gz")
for seed_number in [86, 87, 88, 89, 92, 93]:
    source = list(mask_dir.glob(f"probmap-gm-r{seed_number}-*.nii.gz"))[0]
    re_nii = image.resample_to_img(str(source), str(target_space))
    val = re_nii.get_fdata().max() / 2
    thresh = image.threshold_img(re_nii, val)
    data = thresh.get_fdata()
    bin_nii = nb.Nifti1Image((data > 0).astype(int),
                             header=thresh.header,
                             affine=thresh.affine)
    file_name = str(Path(home + "/projects/critchley_depersonalisation/code/ppi_seeds"))
    file_name = file_name + os.sep + source.name
    bin_nii.to_filename(file_name)
