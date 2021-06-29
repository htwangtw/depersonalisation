from nipype import Function, MapNode, SelectFiles
from nipype.interfaces.fsl import ApplyMask
from nipype.interfaces.io import DataSink
from nipype.pipeline import engine as pe
import nipype.interfaces.utility as util  # utility
from nipype.interfaces import fsl


def create_susan_smooth(name="susan_smooth", separate_masks=True):
    """Create a SUSAN smoothing workflow
    Parameters
    ----------
    ::
        name : name of workflow (default: susan_smooth)
        separate_masks : separate masks for each run
    Inputs::
        inputnode.in_files : functional runs (filename or list of filenames)
        inputnode.fwhm : fwhm for smoothing with SUSAN (float or list of floats)
        inputnode.mask_file : mask used for estimating SUSAN thresholds (but not for smoothing)
    Outputs::
        outputnode.smoothed_files : functional runs (filename or list of filenames)
    Example
    -------
    >>> smooth = create_susan_smooth()
    >>> smooth.inputs.inputnode.in_files = 'f3.nii'
    >>> smooth.inputs.inputnode.fwhm = 5
    >>> smooth.inputs.inputnode.mask_file = 'mask.nii'
    >>> smooth.run() # doctest: +SKIP
    """

    # replaces the functionality of a "for loop"
    def cartesian_product(fwhms, in_files, usans, btthresh):
        from nipype.utils.filemanip import ensure_list

        # ensure all inputs are lists
        in_files = ensure_list(in_files)
        fwhms = [fwhms] if isinstance(fwhms, (int, float)) else fwhms
        # create cartesian product lists (s_<name> = single element of list)
        cart_in_file = [s_in_file for s_in_file in in_files for s_fwhm in fwhms]
        cart_fwhm = [s_fwhm for s_in_file in in_files for s_fwhm in fwhms]
        cart_usans = [s_usans for s_usans in usans for s_fwhm in fwhms]
        cart_btthresh = [s_btthresh for s_btthresh in btthresh for s_fwhm in fwhms]

        return cart_in_file, cart_fwhm, cart_usans, cart_btthresh

    susan_smooth = pe.Workflow(name=name)
    """
    Set up a node to define all inputs required for the preprocessing workflow
    """

    inputnode = pe.Node(
        interface=util.IdentityInterface(fields=["in_files", "fwhm", "mask_file"]),
        name="inputnode",
    )
    """
    Smooth each run using SUSAN with the brightness threshold set to 75%
    of the median value for each run and a mask consituting the mean
    functional
    """

    multi_inputs = pe.Node(
        util.Function(
            function=cartesian_product,
            output_names=["cart_in_file", "cart_fwhm", "cart_usans", "cart_btthresh"],
        ),
        name="multi_inputs",
    )

    smooth = pe.MapNode(
        interface=fsl.SUSAN(),
        iterfield=["in_file", "brightness_threshold", "usans", "fwhm"],
        name="smooth",
    )
    """
    Determine the median value of the functional runs using the mask
    """

    if separate_masks:
        median = pe.MapNode(
            interface=fsl.ImageStats(op_string="-k %s -p 50"),
            iterfield=["in_file", "mask_file"],
            name="median",
        )
    else:
        median = pe.MapNode(
            interface=fsl.ImageStats(op_string="-k %s -p 50"),
            iterfield=["in_file"],
            name="median",
        )
    susan_smooth.connect(inputnode, "in_files", median, "in_file")
    susan_smooth.connect(inputnode, "mask_file", median, "mask_file")
    """
    Mask the motion corrected functional runs with the dilated mask
    """

    if separate_masks:
        mask = pe.MapNode(
            interface=fsl.ImageMaths(suffix="_mask", op_string="-mas"),
            iterfield=["in_file", "in_file2"],
            name="mask",
        )
    else:
        mask = pe.MapNode(
            interface=fsl.ImageMaths(suffix="_mask", op_string="-mas"),
            iterfield=["in_file"],
            name="mask",
        )
    susan_smooth.connect(inputnode, "in_files", mask, "in_file")
    susan_smooth.connect(inputnode, "mask_file", mask, "in_file2")
    """
    Determine the mean image from each functional run
    """

    meanfunc = pe.MapNode(
        interface=fsl.ImageMaths(op_string="-Tmean", suffix="_mean"),
        iterfield=["in_file"],
        name="meanfunc2",
    )
    susan_smooth.connect(mask, "out_file", meanfunc, "in_file")
    """
    Merge the median values with the mean functional images into a coupled list
    """

    merge = pe.Node(interface=util.Merge(2, axis="hstack"), name="merge")
    susan_smooth.connect(meanfunc, "out_file", merge, "in1")
    susan_smooth.connect(median, "out_stat", merge, "in2")
    """
    Define a function to get the brightness threshold for SUSAN
    """

    susan_smooth.connect(
        [
            (inputnode, multi_inputs, [("in_files", "in_files"), ("fwhm", "fwhms")]),
            (median, multi_inputs, [(("out_stat", getbtthresh), "btthresh")]),
            (merge, multi_inputs, [(("out", getusans), "usans")]),
            (
                multi_inputs,
                smooth,
                [
                    ("cart_in_file", "in_file"),
                    ("cart_fwhm", "fwhm"),
                    ("cart_btthresh", "brightness_threshold"),
                    ("cart_usans", "usans"),
                ],
            ),
        ]
    )

    outputnode = pe.Node(
        interface=util.IdentityInterface(fields=["smoothed_files"]), name="outputnode"
    )

    susan_smooth.connect(smooth, "smoothed_file", outputnode, "smoothed_files")

    return susan_smooth


def getbtthresh(medianvals):
    return [0.75 * val for val in medianvals]


def getusans(x):
    return [[tuple([val[0], 0.75 * val[1]])] for val in x]


# First level analysis
def smoothing_skullstrip(
    fmriprep_dir,
    output_dir,
    work_dir,
    subject_list,
    task,
    run,
    fwhm=6.0,
    name="smoothing_skullstrip",
):
    """
    FSL smooth fMRIprep output
    """
    workflow = pe.Workflow(name=name)
    workflow.base_dir = work_dir

    template = {
        "bolds": "sub-{subject}/func/sub-{subject}_task-{task}_run-{run}_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz",
        "mask": "sub-{subject}/func/sub-{subject}_task-{task}_run-{run}_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz",
    }

    bg = pe.Node(SelectFiles(template, base_directory=fmriprep_dir), name="datagrabber")
    bg.iterables = [("subject", subject_list), ("task", task), ("run", run)]

    # Create DataSink object
    sinker = pe.Node(DataSink(), name="sinker")
    sinker.inputs.base_directory = output_dir
    sinker.inputs.substitutions = [
        ("_run_1_subject_", "sub-"),
        ("_skip0", "func"),
        ("desc-preproc_bold_smooth_masked_roi", f"desc-preproc-fwhm{int(fwhm)}mm_bold"),
    ]

    # Smoothing
    susan = create_susan_smooth()
    susan.inputs.inputnode.fwhm = fwhm

    # masking the smoothed output
    # note: susan workflow returns a list but apply mask only accept string of path
    mask_results = pe.MapNode(
        ApplyMask(), name="mask_results", iterfield=["in_file", "mask_file"]
    )

    # remove first five volumes
    skip = pe.MapNode(fsl.ExtractROI(), name="skip", iterfield=["in_file"])
    skip.inputs.t_min = 5
    skip.inputs.t_size = -1

    workflow.connect(
        [
            (
                bg,
                susan,
                [("bolds", "inputnode.in_files"), ("mask", "inputnode.mask_file")],
            ),
            (bg, mask_results, [("mask", "mask_file")]),
            (susan, mask_results, [("outputnode.smoothed_files", "in_file")]),
            (mask_results, skip, [("out_file", "in_file")]),
            (skip, sinker, [("roi_file", f"func_smooth-{int(fwhm)}mm.@out_file")]),
        ]
    )
    return workflow


bids_dir = "/its/home/bsms9gxx/projects/critchley_depersonalisation/data/derivatives/fmriprep-1.5.1rc2"
output_dir = "/its/home/bsms9gxx/projects/critchley_depersonalisation/data/derivatives"
work_dir = "/its/home/bsms9gxx/projects/critchley_depersonalisation/scratch"
subjects = [
    9539,
    9634,
    9664,
    9675,
    9097,
    9946,
    10048,
    10155,
    10186,
    10185,
    10218,
    10317,
    10434,
    10469,
    10474,
    10593,
    10620,
    9389,
    9393,
    9420,
    9431,
    9454,
    9478,
    9503,
    9575,
    9676,
    9686,
    9734,
    9790,
    9933,
    9934,
    9995,
    10076,
    10086,
    10108,
    10142,
    10188,
    10245,
    10261,
    10284,
    10353,
    10404,
    8494,
    10449,
    10451,
    10456,
    10471,
    10472,
    10473,
    10573,
]
workflow = smoothing_skullstrip(
    bids_dir, output_dir, work_dir, subject_list=subjects, task=["heartbeat"], run=[1]
)
workflow.run()
