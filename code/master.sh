#!/bin/bash

cd ~/projects/critchley_depersonalisation
# . env/bin/activate

cd ~/projects/critchley_depersonalisation/code

SUBJ_LIST=$( sed -n -E "s/sub-(\S*)\>.*/\1/gp" \
             participants.tsv )

# generate regressors
# for subj in $SUBJ_LIST; do
#   qsub ./create_regressors.sh ${subj}
# done

# first level 
for subj in $SUBJ_LIST; do
  echo sub-$subj
  # HRV analysis
  # ./first_level.sh hrv_level1.fsf FSL_HRV_no_td ${subj}
  # ./registration.sh FSL_HRV_no_td ${subj}

  # HRV and task 
  # ./first_level.sh hrv_with_task_level1.fsf FSL_task_HRV ${subj}
  # ./registration.sh FSL_task_HRV ${subj}

  # task only
  # ./first_level.sh heart_wrt_note_level_1.fsf FSL_task ${subj}
  # ./registration.sh FSL_task ${subj}

  #PPI
  for seed in pag insularL insularR; do
    if [[ "x$SGE_ROOT" = "x" ]] ; then
      ./first_level_PPI.sh PPI_level1.fsf FSL_PPI-$seed ${subj} $seed
    else
      qsub -o ${HOME}/logs -N sub-${subj}_${seed} \
           ./first_level_PPI.sh PPI_level1.fsf FSL_PPI-$seed ${subj} $seed
    fi  
  done

done

PATH_REGRESSORS=$(readlink -f ~/projects/critchley_depersonalisation/results/group_confounds.tsv)
# group level nuisance regressors
if [[ ! -f $PATH_REGRESSORS ]]
  then
  python ./fsl_group_regressors.py
fi

# group level

# PATH_ANALYSIS=$(readlink -f ${HOME}/projects/critchley_depersonalisation/scratch/FSL_HRV_no_td)
# python ./fsl_group_nonpara.py -s $SUBJ_LIST -i $PATH_ANALYSIS -r $PATH_REGRESSORS 

# PATH_ANALYSIS=$(readlink -f ${HOME}/projects/critchley_depersonalisation/scratch/FSL_task_HRV)
# python ./fsl_group_nonpara.py -s $SUBJ_LIST -i $PATH_ANALYSIS -r $PATH_REGRESSORS 

# PATH_ANALYSIS=$(readlink -f ${HOME}/projects/critchley_depersonalisation/scratch/FSL_task)
# python ./fsl_group_nonpara.py -s $SUBJ_LIST -i $PATH_ANALYSIS -r $PATH_REGRESSORS 

# PPI
# for seed in lf_HRV hf_HRV bpm; do
#   PATH_ANALYSIS=$(readlink -f "${HOME}/projects/critchley_depersonalisation/scratch/FSL_PPI-$seed")
#   python ./fsl_group_nonpara.py -s $SUBJ_LIST -i $PATH_ANALYSIS -r $PATH_REGRESSORS
# done
