from pathlib import Path

import nibabel as nb
from sklearn import neighbors

from nipype import SelectFiles, Function
from nipype.pipeline import engine as pe
from nipype.interfaces import fsl

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
    with open(con) as f:
        contrast_names = [line.split()[-1] for line in f.readlines() if "ContrastName" in line]
    return contrast_names

def smooth_concat(lst_copes, mm):
    copes = []
    for i in lst_copes
        copes.append(smooth_img(i, mm))
    copes_concat = concat_imgs(copes, auto_resample=True)
    return copes_concat

def create_group_mask(brain_masks):
    # create a group level mask and report the coverage
    mean_mask = mean_img(brain_masks)
    group_mask = math_img("a>=0.95", a=mean_mask)
    group_mask = resample_to_img(group_mask, copes_concat,
                                interpolation='nearest')
    return group_mask

def create_sphere_mask(seed, group_mask, radius):
    """
    seed: tuple
    """
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

def roi_mask(roi, group_mask):
    # if customised mask used, overlap it with
    # the group whole brain mask
    # check what type of ROI
    if "nii.gz" in roi:
        mask = resample_to_img(roi, group_mask, interpolation='nearest')
    elif type(roi) is tuple:
        print(f"creating 8mm radius sphere around {roi}")
        mask = create_sphere_mask(seed=roi, group_mask=group_mask, radius=8)
    else:
        mask = group_mask
    return mask
    
def GLM_contrast(groups, regressors, contrasts):
    import pandas as pd
    groups = pd.read_csv(groups, sep='\t').values[:, 1].tolist()
    regressors = pd.read_csv(regressors, sep='\t').iloc[:, 1:].to_dict('list')
    df_contrasts = pd.read_csv(contrasts, sep='\t')
    
    var_names = df_contrasts.columns[2:].tolist()
    contrasts = []
    for index, row in df_contrasts.iterrows():
        cur_con = [row['contrast_name'], row['test'],
                   var_names, row[var_names].tolist()]
        contrasts.append(cur_con)        
    
    return groups, regressors, contrasts

def group_randomise_wf(input_dir, subject_list, roi=None):
    """
    input_dir: 
        BIDS derivative
    subject_list:
        subjects entering group level analysis
    roi:
        mask or coordinate (default: whole brain)
    """
    analysis_name = input_dir.split(os.sep)[-1]
    contrast_names = cope_names(input_dir)
    roi_dir = input_dir + os.sep + "group_level" + os.sep + "roi_masks"
    os.makedirs(roi_dir)

    meta_workflow = pe.Workflow(name=analysis_name)
    meta_workflow.base_dir = input_dir + os.sep + "group_level"
    
    template = {"mask":"sub-{subject}/sub-{subject}.feat/mask.nii.gz"}
    whole_brain_mask = pe.Node(SelectFiles(template, base_directory=input_dir))
    whole_brain_mask.iterables = [('subject', subject_list)]

    gen_groupmask = pe.Node(Function(create_group_mask, 
                                          input_names=['brain_masks'], 
                                          output_names=['group_mask']), 
                                 name='gen_groupmask')
    
    gen_inputmask = pe.Node(Function(roi_mask, input_names=['roi', 'group_mask'], 
                                     output_names=['mask']), 
                            name='gen_inputmask')

    # generate design matrix
    model = pe.Node(fsl.MultipleRegressDesign(), name='model')            
    model.inputs.groups = groups
    model.inputs.contrasts = [contrast]
    model.inputs.regressors = regressors

    # now run randomise...
    for cope_id, contrast in enumerate(contrast_names):
        wk = pe.Workflow(name=f"contrast_{contrast}")

        template = {"cope":"sub-{subject}/sub-{subject}.feat/stats/cope{cope}.nii.gz"}
        file_grabber = pe.Node(SelectFiles(template, base_directory=input_dir))
        file_grabber.inputs.cope = cope_id + 1
        file_grabber.inputs.subject = subject_list

        generate_input = pe.Node(Function(smooth_concat, 
                                          input_names=['lst_copes', 'mm'], 
                                          output_names=['copes_concat']), 
                                 name='concat_copes',
                                 mm=8)

        randomise_results = pe.Node(fsl.Randomise)
        # (in_file=in_cope,mask=mask_path,tcon=,design_mat=,num_perm=1000
        meat_workflow.add_nodes([wk])