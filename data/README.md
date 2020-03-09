# Depersonalise Psychosis Study

## Onset time in event files
By BIDS standard, the time logged as onset shoud be aligned to the first volume of the file.
The unit is second. 
In the original heartbeat detection task, the time is logged in relation to the start of the behavioural experiment.
The unit of the time is millisecond. 
See `code/beh_copy2tsv.py` for details

## Dummy volume handling
See discussions: https://neurostars.org/t/dummy-scans-option-on-fmriprep-functional/4683
When running first level analysis, one must 
1. include the non steady state parameters as nuisance regressors
2. calculate the onset of events accordingly for task regressors