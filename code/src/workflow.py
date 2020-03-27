import os
from pathlib import Path

import nibabel as nb
from sklearn import neighbors
import pandas as pd
import numpy as np

from nipype import SelectFiles, Function
from nipype.pipeline import engine as pe
from nipype.interfaces import fsl
from nipype.interfaces.io import DataSink
import nipype.interfaces.utility as niu

from nilearn.image import (concat_imgs, resample_to_img,
                           mean_img, math_img)
from nilearn.image.resampling import coord_transform


# get first level copes
def cope_names(input_dir):
    """
    input_dir:
        BIDS derivative - FSL feat first level outputs
        all feat directories should be derived from the same design
    """
    first_level = Path(input_dir)
    feat_dir = first_level.glob("sub-*/sub-*[0-9].feat/")
    con = list(feat_dir)[0] / "design.con"
    print(con)
    with open(con) as f:
        contrast_names = [line.split()[-1] for line in f.readlines() if "ContrastName" in line]
    return contrast_names

def smooth_concat(cope_file, mm, output_dir):
    from nilearn.image import concat_imgs, smooth_img
    copes = []
    for i in cope_file:
        # i = smooth_img(i, mm)
        copes.append(i)
    copes_concat = concat_imgs(copes, auto_resample=True)
    copes_concat.to_filename(output_dir)
    return output_dir

def create_group_mask(brain_masks, base_dir):
    from nilearn.image import (resample_to_img, mean_img, math_img)
    from nilearn.plotting import plot_stat_map, plot_roi
    import os

    # create a group level mask and report the coverage
    mean_mask = mean_img(brain_masks)
    group_mask = math_img("a>=0.95", a=mean_mask)

    groupmask_path = base_dir + "group_mask.nii.gz"

    group_mask.to_filename(groupmask_path)
    if not os.path.exists(groupmask_path):
        group_mask.to_filename(groupmask_path)

    # plot report
    plot_stat_map(mean_mask,
                  output_file=base_dir + "coverage_group_mask.png")
    plot_roi(group_mask,
             output_file=base_dir + "bninary_group_mask.png")
    return groupmask_path

def create_sphere_mask(seed, group_mask, radius):
    """
    seed: tuple
    """
    import numpy as np
    from sklearn import neighbors
    from nilearn.image.resampling import coord_transform
    import nibabel as nb

    mask = group_mask.get_date()
    affine = group_mask.affine
    mask_coords = list(zip(*np.where(mask != 0)))
    # For each seed, get coordinates of nearest voxel
    for sx, sy, sz in seed:
        nearest = np.round(coord_transform(sx, sy, sz,
                                           np.linalg.inv(affine)))
        nearest = nearest.astype(int)
        nearest = (nearest[0], nearest[1], nearest[2])

    mask_coords = np.asarray(list(zip(*mask_coords)))
    mask_coords = coord_transform(mask_coords[0], mask_coords[1],
                                  mask_coords[2], affine)
    mask_coords = np.asarray(mask_coords).T
    clf = neighbors.NearestNeighbors(radius=radius)
    A = clf.fit(mask_coords).radius_neighbors_graph(seeds)
    A = A.tolil()
    for i, nearest in enumerate(nearests):
        if nearest is None:
            continue
        A[i, nearest] = True

    # save shpere mask
    roi_nii = nb.Nifti1Image(A, affine=affine, header=group_mask.header)
    return roi_nii

def roi_mask(roi, group_mask, base_dir):
    # if customised mask used, overlap it with
    # the group whole brain mask
    # check what type of ROI
    import os
    import nibabel as nb
    from nilearn.image import resample_to_img
    if "nii.gz" in roi:
        mask = resample_to_img(roi, group_mask, interpolation='nearest')
        fn = roi.split(os.sep)[-1]
    elif type(roi) is tuple:
        print(f"creating 8mm radius sphere around {roi}")
        mask = create_sphere_mask(seed=roi, group_mask=group_mask, radius=8)
        fn = roi.join('_') + ".nii.gz"
    else:
        mask = nb.load(group_mask)
        fn = "group_mask.nii.gz"

    mask_path = base_dir + fn
    if not os.path.exists(mask_path):
        mask.to_filename(mask_path)
    return mask_path

def groupmean_contrast(subject_list, regressors_path):
    import pandas as pd
    import numpy as np
    regressors = pd.read_csv(regressors_path, sep='\t', index_col=0)
    subject_list = [f"sub-{i}" for i in subject_list]

    if regressors.shape[0] != len(subject_list):
        regressors = regressors.loc[subject_list, :]

    # sort by subject list
    group = regressors.group.tolist()
    regressors = regressors.reindex(subject_list)[['z_age', 'z_mean_fd']]
    regressors['control'] = [1 if g=='control' else 0 for g in group]
    regressors['patient'] = np.abs(regressors['control'] - 1)

    # generate basic contrasts
    contrast_names = ['control', 'patient',
                      'patient > control', 'control > patient']
    df_con = pd.DataFrame(0, columns=regressors.columns,
                          index=contrast_names)
    df_con.loc['control', ['control']] = 1
    df_con.loc['patient', ['patient']] = 1
    df_con.loc['patient > control', ['patient']] = 1
    df_con.loc['patient > control', ['control']] = -1
    df_con.loc['control > patient', ['patient']] = -1
    df_con.loc['control > patient', ['control']] = 1

    contrasts = []
    for index, row in df_con.iterrows():
        cur_con = (str(index), 'T', row.index.tolist(), row.tolist())
        contrasts.append(cur_con)

    # group
    group = np.ones(len(subject_list)).astype(int).tolist()

    # save out the design matrix with subject number for seninty check

    return group, regressors.to_dict('list'), (contrasts)


def group_randomise_wf(input_dir, subject_list, regressors_path, roi=None):
    """
    input_dir:
        BIDS derivative
    subject_list:
        subjects entering group level analysis
    roi:
        mask or coordinate (default: whole brain)
    """
    def wf_prep_files():
        prep_files = pe.Workflow(name="prep_files")
        prep_files.base_dir = input_dir + os.sep + "group_level"

        template = {"mask":"sub-{subject}/sub-{subject}.feat/mask.nii.gz"}
        whole_brain_mask = pe.MapNode(SelectFiles(templates=template),
                                      iterfield="subject",
                                      name="whole_brain_mask")
        whole_brain_mask.inputs.base_directory = input_dir
        whole_brain_mask.inputs.subject = subject_list

        gen_groupmask = pe.Node(Function(function=create_group_mask,
                                         input_names=["brain_masks", "base_dir"],
                                         output_names=["groupmask_path"]),
                                name="gen_groupmask")
        gen_groupmask.inputs.base_dir = input_dir + os.sep + "group_level" + os.sep


        designs = pe.Node(Function(function=groupmean_contrast,
                                    input_names=["subject_list", "regressors_path"],
                                    output_names=["groups", "regressors", "contrasts"]),
                            name='designs')
        designs.inputs.subject_list = subject_list
        designs.inputs.regressors_path = regressors_path

        model = pe.Node(fsl.MultipleRegressDesign(), name=f'model')

        outputnode = pe.Node(
            interface=niu.IdentityInterface(fields=['mask', "regressors", "contrasts"]),
            name='outputnode')

        prep_files.connect([
            (whole_brain_mask, gen_groupmask, [("mask", "brain_masks")]),
            (designs, model, [("groups", "groups"),
                            ("regressors", "regressors"),
                            ("contrasts", "contrasts")]),
            (gen_groupmask, outputnode, [("groupmask_path", "mask")]),
            (model, outputnode, [("design_grp", "group"),
                                 ("design_mat", "regressors"),
                                 ("design_con","contrasts")])
        ])
        return prep_files

    analysis_name = "FSL_randomise"
    meta_workflow = pe.Workflow(name=analysis_name)
    meta_workflow.base_dir = input_dir + os.sep + "group_level"
    prep_files = wf_prep_files()
    # now run randomise...
    contrast_names = cope_names(input_dir)
    for cope_id, contrast in enumerate(contrast_names):
        wk = pe.Workflow(name=f"contrast_{contrast}")
        template = {"cope_file":"sub-{subject}/sub-{subject}.feat/stats/cope{cope}.nii.gz"}
        file_grabber = pe.MapNode(SelectFiles(template, base_directory=input_dir),
                                  iterfield="subject",
                                  name="file_grabber")
        file_grabber.inputs.cope = cope_id + 1
        file_grabber.inputs.subject = subject_list

        concat_copes = pe.Node(Function(function=smooth_concat,
                                        input_names=["cope_file", "mm",
                                                     "output_dir"],
                                        output_names=["output_dir"]),
                                 name="concat_copes")
        concat_copes.inputs.mm = 8
        concat_copes.inputs.output_dir = (input_dir + os.sep + "group_level" +
                                          os.sep + f"cope_{contrast}.nii.gz")
        prep_files = wf_prep_files()
        # generate design matri
        randomise = pe.Node(fsl.Randomise(), name="randomise")
        randomise.inputs.num_perm = 1000
        randomise.inputs.vox_p_values = True
        randomise.inputs.tfce = True
        # randomise.inputs.demean = True

        onesampleT_randomise = pe.Node(fsl.Randomise(), name="onesampleT_randomise")
        onesampleT_randomise.inputs.num_perm = 1000
        onesampleT_randomise.inputs.vox_p_values = True
        onesampleT_randomise.inputs.tfce = True
        # onesampleT_randomise.inputs.demean = True
        onesampleT_randomise.inputs.one_sample_group_mean=True

        wk.connect([
            (file_grabber, concat_copes, [("cope_file", "cope_file")]),
            (concat_copes, randomise, [("output_dir", "in_file")]),
            (prep_files, randomise, [("outputnode.mask", "mask"),
                                     ("outputnode.contrasts", "tcon"),
                                     ("outputnode.regressors", "design_mat")]),
            (concat_copes, onesampleT_randomise, [("output_dir", "in_file")]),
            (prep_files, onesampleT_randomise, [("outputnode.mask", "mask")]),
            ])
        meta_workflow.add_nodes([wk])
    return meta_workflow
