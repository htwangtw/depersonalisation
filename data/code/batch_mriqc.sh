BIDS_DIR="E:\DepersonalisationPsychosis\data"
OUTPUT_DIR="${BIDS_DIR}\derivatives\mriqc-0.15.2rc1"
WORK_DIR="E:\DepersonalisationPsychosis\scratch"
subject=$( sed -n -E \
    "s/sub-(\S*)\>.*/\1/gp" \
    /mnt/e/DepersonalisationPsychosis/data/participants.tsv ) 
docker run -it --rm -v $BIDS_DIR:/data \
                    -v $OUTPUT_DIR:/out \
                    -v $WORK_DIR:/work \
                    -u $(id -u):$(id -g) \
                    poldracklab/mriqc:latest \
                    -w /work \
                    -m bold \
                    --task-id heartbeat \
                    --fd_thres 0.5 \
                    --dsname depersonalisation \
                    /data /out participant \
                    --participant_label $subject

docker run -it --rm -v $BIDS_DIR:/data \
                    -v $OUTPUT_DIR:/out \
                    -v $WORK_DIR:/work \
                    -u $(id -u):$(id -g) \
                    poldracklab/mriqc:latest \
                    -w /work \
                    -m T1w \
                    --dsname depersonalisation \
                    /data /out participant \
                    --participant_label $subject   

# did not check resting state
docker run -it --rm -v $BIDS_DIR:/data \
                    -v $OUTPUT_DIR:/out \
                    -v $WORK_DIR:/work \
                    -u $(id -u):$(id -g) \
                    poldracklab/mriqc:latest \
                    -w /work \
                    -m bold \
                    --task-id rest \
                    --dsname depersonalisation \
                    /data /out participant \
                    --participant_label $subject                    
                    