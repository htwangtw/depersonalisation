#!/bin/bash
#$ -N fsl_group
#$ -o /home/$USER/logs
#$ -j y
#$-t 1-10
#$-tc 1

. ${HOME}/.bash_profile
SEED_DIR=${HOME}/projects/critchley_depersonalisation/code/ppi_seeds
SEED_LIST=($(ls ${SEED_DIR}/*))
i=$(expr $SGE_TASK_ID - 1)
seed=${SEED_LIST[$i]}
SEED_NAME=$(echo $(basename $seed) | cut -d - -f4 | cut -d . -f1)
PATH_CONTRAST=${HOME}/projects/critchley_depersonalisation/code/group_design/CDS_group_interaction_contrast.tsv
PATH_REGRESSORS=${HOME}/projects/critchley_depersonalisation/code/group_design/CDS_group_interaction_regressors.tsv

cd ${HOME}/projects/critchley_depersonalisation/code
# bash ./grouplevel.sh $SEED_NAME $PATH_REGRESSORS $PATH_CONTRAST
bash ./grouplevel.sh task $PATH_REGRESSORS $PATH_CONTRAST