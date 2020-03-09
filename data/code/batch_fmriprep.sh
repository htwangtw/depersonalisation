subj_lst=$(ls -d ~/sussex/BIDS/sub*)

for subj in $subj_lst; do
    id=${subj#*-}
    echo $id
        fmriprep-docker ~/sussex/BIDS \
        ~/sussex/derivatives \
        participant --participant-label $id \
        --task-id interoception \
        --fs-license-file ${FREESURFER_HOME}/license.txt \
        --dummy-scans 6 \
        --fs-no-reconall
done