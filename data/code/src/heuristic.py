import os


def create_key(template, outtype=("nii.gz",), annotation_classes=None):
    if template is None or not template:
        raise ValueError("Template must be a valid format string")
    return template, outtype, annotation_classes


def infotodict(seqinfo):
    """Heuristic evaluator for determining which runs belong where

    allowed template fields - follow python string module:

    item: index within category
    subject: participant id
    seqitem: run number during scanning
    subindex: sub index within group
    """

    t1w = create_key("sub-{subject}/anat/sub-{subject}_run-{item:01d}_T1w")
    task_interoception = create_key(
        "sub-{subject}/func/sub-{subject}_task-heartbeat_run-{item:01d}_bold"
    )
    task_rs = create_key(
        "sub-{subject}/func/sub-{subject}_task-rest_echo-{item:01d}_bold"
    )
    noddi_300 = create_key("sub-{subject}/dwi/sub-{subject}_acq-NODDIb300dirs9_dwi")
    noddi_800 = create_key("sub-{subject}/dwi/sub-{subject}_acq-NODDIb800dirs30_dwi")
    noddi_2400 = create_key("sub-{subject}/dwi/sub-{subject}_acq-NODDIb2400dirs60_dwi")

    info = {
        t1w: [],
        task_rs: [],
        task_interoception: [],
        noddi_300: [],
        noddi_800: [],
        noddi_2400: [],
    }

    for s in seqinfo:
        """
        The namedtuple `s` contains the following fields:

        * total_files_till_now
        * example_dcm_file
        * series_id
        * dcm_dir_name
        * unspecified2
        * unspecified3
        * dim1
        * dim2
        * dim3
        * dim4
        * TR
        * TE
        * protocol_name
        * is_motion_corrected
        * is_derived
        * patient_id
        * study_acqription
        * referring_physician_name
        * series_acqription
        * image_type
        """
        if (
            (s.dim1 == 256)
            and (s.dim2 == 240)
            and ("HiResMPRAGE_WIDER_GRAPPA" in s.protocol_name)
        ):
            info[t1w].append(s.series_id)
        elif (
            (s.dim1 == 64)
            and (s.dim2 == 64)
            and ("multi-echo RS fMRI" in s.protocol_name)
        ):
            info[task_rs].append(s.series_id)
        elif (
            (s.dim1 == 64)
            and (s.dim2 == 64)
            and ("ep2d_fid_INTEROCEPTION" in s.protocol_name)
        ):
            info[task_interoception].append(s.series_id)
        elif ("NODDI" in s.protocol_name) and not s.is_derived:
            if "300" in s.protocol_name:
                info[noddi_300].append(s.series_id)
            elif "800" in s.protocol_name:
                info[noddi_800].append(s.series_id)
            elif "2400" in s.protocol_name:
                info[noddi_2400].append(s.series_id)
    return info
