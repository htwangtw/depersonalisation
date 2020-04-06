#!/bin/bash
#$ -N fsl_group
#$ -o /home/$USER/logs
#$ -j y
#$-t 1-6
#$-tc 6

. ~/.bash_profile
SEED_DIR=${HOME}/projects/critchley_depersonalisation/references/insular_masks
SEED_LIST=($(ls ${SEED_DIR}/probmap-gm-*-insula*))
i=$(expr $SGE_TASK_ID - 1)
seed=${SEED_LIST[$i]}
SEED_NAME=$(echo $(basename $seed) | cut -d - -f4 | cut -d . -f1)

cd ~/projects/critchley_depersonalisation/code
bash ./grouplevel.sh $SEED_NAME