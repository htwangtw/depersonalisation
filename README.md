# Metacognitive deficits in interoception in FEP

Depersonalisation projects links to manuscript WIP by Sarah Garfinkel.  
Data originally collected and analysed by Geoff Davies, Charlotte Rae, and Cassandra Gould van Praag.  
The current version in this folder is curated and analysed by Hao-Ting Wang.  

```
./
├── data
│   ├── code
│   ├── derivatives
│   ├── sourcedata
│   ├── sub-*
│   ├── CHANGES.md
│   ├── dataset_description.json
│   ├── participants.json
│   ├── participants.tsv
│   ├── README.md
│   ├── task-heartbeat_bold.json
│   └── task-rest_bold.json
├── analysis
│   ├── fmri
│   │   ├── code
│   │   │   ├── src
│   │   │   ├── clusterSubmit.sh
│   │   │   └── fmri_level-first_model-full.py
│   │   └── reports
│   │       └── model-modelname
│   └── behaviour
│       ├── code
│       └── reports
├── references
├── results
├── scratch
└── README.md
```

## `data`

This is a BIDS directory containing the raw data (`sourcedata`), BIDS compiled Nifti, and minimally preprocessed dataset for statistical modeling (`derivatives`).

## `analysis`

Containing GLM model, code for the analysis and the final reports with.

## `references`

Code from referenced study, MNI space seed/gray matter masks

## `results`

Code and metadata to produce the final figures. And, of course the figures.

## `scratch`

Scratch folder. Delete after a project is complete.

## Difference between `./data/derivatives` in and `analysis`

Prerpocessed first level data in `./data/derivatives`
Summary, second level data and metadat derived `analysis`
Rule of thumb: data that might need permission to share, or too large for GitHub goes to `./data/derivatives`; otherwise `analysis`

## Framewise displacement threshold for quality assessments

The motion detection threshold is 0.5 mm for quality assessment and outlier frame cut-off in the heartbeat detection task. (c.f. 0.2 mm for resting state.)
I set the cut off at 20% of the volumes and then visually inspect the spiking.
