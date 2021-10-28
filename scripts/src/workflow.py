import os
from pathlib import Path

from nipype import SelectFiles, Function
from nipype.pipeline import engine as pe
from nipype.interfaces import fsl
from nipype.interfaces.io import DataSink
import nipype.interfaces.utility as niu


def _cope_names(input_dir, selected_cope=None):
    """Get COPE names from the first level analysis

    Parameters
    ----------
    input_dir:
        BIDS derivative - FSL feat first level outputs
        all feat directories should be derived from the same design
    selected_cope:
        A list of cope of interest, names matching the first level design


    Return
    ------
    selected_contrasts: List of tuple
        cope index and cope name
    """
    first_level = Path(input_dir)
    feat_dir = first_level.glob("sub-*/sub-*[0-9].feat/")
    con = list(feat_dir)[0] / "design.con"
    print(con)
    with open(con) as f:
        contrast_names = [
            line.split()[-1] for line in f.readlines() if "ContrastName" in line
        ]

    selected_contrasts = []
    for i, cn in enumerate(contrast_names):
        cope_idx = i + 1
        if type(selected_cope) is list:
            # check if names matches
            for sc in selected_cope:
                if sc in contrast_names:
                    if sc == cn:
                        selected_contrasts.append((cope_idx, cn))
                    else:
                        pass
                else:
                    print(f"selected contrast {sc} doesn't exisit. Typo?")
        else:
            selected_contrasts.append((cope_idx, cn))
    return selected_contrasts


def _concat_copes(cope_file, output_dir):
    """Concatenate COPE images and save as a file"""
    from nilearn.image import concat_imgs

    copes = []
    for i in cope_file:
        copes.append(i)
    copes_concat = concat_imgs(copes, auto_resample=True)
    copes_concat.to_filename(output_dir)
    return output_dir


def _create_group_mask(brain_masks, base_dir):
    """Create mask fo the current sample."""
    from nilearn.image import mean_img, math_img
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
    plot_stat_map(mean_mask, output_file=base_dir + "coverage_group_mask.png")
    plot_roi(group_mask, output_file=base_dir + "bninary_group_mask.png")
    return groupmask_path


def _groupmean_contrast(subject_list, regressors_path, contrast_path):
    import pandas as pd
    import numpy as np

    # read regressor
    regressors = pd.read_csv(regressors_path, sep="\t", index_col=0)
    subject_list = [f"sub-{i}" for i in subject_list]

    # sort by subject list
    regressors = regressors.loc[subject_list, :]

    # generate basic contrasts
    df_con = pd.read_csv(contrast_path, sep="\t", index_col=0)
    contrasts = []
    for index, row in df_con.iterrows():
        cur_con = (str(index), "T", row.index.tolist(), row.tolist())
        contrasts.append(cur_con)

    # group (this is only for unpaired t test)
    group = np.ones(len(subject_list)).astype(int).tolist()
    return group, regressors.to_dict("list"), (contrasts)


def group_randomise_wf(
    input_dir,
    output_dir,
    subject_list,
    regressors_path,
    contrast_path,
    selected_cope=None,
    roi=None,
    oneSampleT=False,
    analysis_name="oneSampleT_PPI",
):
    """Group level non parametric test work flow

    Parameters
    ----------
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

        template = {"mask": "sub-{subject}/sub-{subject}.feat/mask.nii.gz"}
        whole_brain_mask = pe.MapNode(
            SelectFiles(templates=template),
            iterfield="subject",
            name="whole_brain_mask",
        )
        whole_brain_mask.inputs.base_directory = input_dir
        whole_brain_mask.inputs.subject = subject_list

        gen_groupmask = pe.Node(
            Function(
                function=_create_group_mask,
                input_names=["brain_masks", "base_dir"],
                output_names=["groupmask_path"],
            ),
            name="gen_groupmask",
        )
        gen_groupmask.inputs.base_dir = input_dir + os.sep + "group_level" + os.sep

        designs = pe.Node(
            Function(
                function=_groupmean_contrast,
                input_names=["subject_list", "regressors_path", "contrast_path"],
                output_names=["groups", "regressors", "contrasts"],
            ),
            name="designs",
        )
        designs.inputs.subject_list = subject_list
        designs.inputs.regressors_path = regressors_path
        designs.inputs.contrast_path = contrast_path

        model = pe.Node(fsl.MultipleRegressDesign(), name=f"model")

        outputnode = pe.Node(
            interface=niu.IdentityInterface(fields=["mask", "regressors", "contrasts"]),
            name="outputnode",
        )

        prep_files.connect(
            [
                (whole_brain_mask, gen_groupmask, [("mask", "brain_masks")]),
                (
                    designs,
                    model,
                    [
                        ("groups", "groups"),
                        ("regressors", "regressors"),
                        ("contrasts", "contrasts"),
                    ],
                ),
                (gen_groupmask, outputnode, [("groupmask_path", "mask")]),
                (
                    model,
                    outputnode,
                    [
                        ("design_grp", "group"),
                        ("design_mat", "regressors"),
                        ("design_con", "contrasts"),
                    ],
                ),
            ]
        )
        return prep_files

    meta_workflow = pe.Workflow(name=analysis_name)
    meta_workflow.base_dir = input_dir + os.sep + "group_level"
    prep_files = wf_prep_files()
    # now run randomise...
    contrast_names = _cope_names(input_dir, selected_cope)
    for cope_id, contrast in contrast_names:
        node_name = contrast.replace(">", "_wrt_")
        wk = pe.Workflow(name=f"contrast_{node_name}")
        template = {
            "cope_file": "sub-{subject}/sub-{subject}.feat/stats/cope{cope}.nii.gz"
        }
        file_grabber = pe.MapNode(
            SelectFiles(template, base_directory=input_dir),
            iterfield="subject",
            name="file_grabber",
        )
        file_grabber.inputs.cope = cope_id
        file_grabber.inputs.subject = subject_list

        concat_copes = pe.Node(
            Function(
                function=_concat_copes,
                input_names=["cope_file", "output_dir"],
                output_names=["output_dir"],
            ),
            name="concat_copes",
        )
        concat_copes.inputs.output_dir = (
            input_dir + os.sep + "group_level" + os.sep + f"cope_{node_name}.nii.gz"
        )
        prep_files = wf_prep_files()

        # generate design matrix
        randomise = pe.Node(fsl.Randomise(), name="stats_randomise")
        randomise.inputs.num_perm = 1000
        randomise.inputs.vox_p_values = True
        randomise.inputs.tfce = True

        import pandas as pd

        group_contrast_names = pd.read_csv(contrast_path, sep="\t", index_col=0).index
        group_contrast_names = group_contrast_names.tolist()

        # Create DataSink object
        sinker = pe.Node(DataSink(), name=f"sinker_{node_name}")
        sinker.inputs.base_directory = output_dir + os.sep + analysis_name
        t_test_new_name, p_new_name = [], []
        for i, name in enumerate(group_contrast_names):
            t_test_new_name.append((f"randomise_tstat{i + 1}", f"{name}_tstat"))
            p_new_name.append(
                (f"randomise_tfce_corrp_tstat{i + 1}", f"{name}_tfce_corrp_tstat")
            )
        sinker.inputs.substitutions = t_test_new_name + p_new_name

        # connect the nodes
        wk.connect(
            [
                (file_grabber, concat_copes, [("cope_file", "cope_file")]),
                (concat_copes, randomise, [("output_dir", "in_file")]),
                (
                    prep_files,
                    randomise,
                    [
                        ("outputnode.mask", "mask"),
                        ("outputnode.contrasts", "tcon"),
                        ("outputnode.regressors", "design_mat"),
                    ],
                ),
                (
                    randomise,
                    sinker,
                    [
                        ("tstat_files", f"contrast_{node_name}.@tstat_files"),
                        (
                            "t_corrected_p_files",
                            f"contrast_{node_name}.@t_corrected_p_files",
                        ),
                    ],
                ),
            ]
        )

        if oneSampleT:
            # one sample T test
            onesampleT_randomise = pe.Node(fsl.Randomise(), name="onesampleT_randomise")
            onesampleT_randomise.inputs.num_perm = 1000
            onesampleT_randomise.inputs.vox_p_values = True
            onesampleT_randomise.inputs.tfce = True
            onesampleT_randomise.inputs.one_sample_group_mean = True

            # Create DataSink object
            gsinker = pe.Node(DataSink(), name=f"sinker_{node_name}_group")
            gsinker.inputs.base_directory = output_dir + os.sep + analysis_name
            gsinker.inputs.substitutions = [
                ("tstat1", "tstat"),
                ("randomise", "fullsample"),
            ]
            wk.connect(
                [
                    (concat_copes, onesampleT_randomise, [("output_dir", "in_file")]),
                    (prep_files, onesampleT_randomise, [("outputnode.mask", "mask")]),
                    (
                        onesampleT_randomise,
                        gsinker,
                        [
                            ("tstat_files", f"contrast_{node_name}.@group_tstat_files"),
                            (
                                "t_corrected_p_files",
                                f"contrast_{node_name}.@group_t_corrected_p_files",
                            ),
                        ],
                    ),
                ]
            )

        meta_workflow.add_nodes([wk])
    return meta_workflow
