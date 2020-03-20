# Metacognitive deficits in interoception in FEP

Depersonalisation projects links to manuscript WIP by Sarah Garfinkel.  
Data originally collected and analysed by Geoff Davies, Charlotte Rae, and Cassandra Gould van Praag.  
The current version in this folder is curated and analysed by Hao-Ting Wang.  

Last update: 16 March 2020

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
├── code
│   ├── tests
│   └── src
├── references
├── results
├── scratch
└── README.md
```

## `data`

This is a BIDS directory containing the raw data (`sourcedata`), BIDS compiled Nifti, and minimally preprocessed dataset for statistical modeling (`derivatives`).

## `code`

Analysis and visualisation code, including FSL design files

## `references`

Code from referenced study, MNI space seed/gray matter masks

## `results`
Outputs from `code`, includes figures, important interim data, manuscripts.
Includes copy of metadata to produce the final figures.

## `scratch`

Scratch folder. Delete after a project is complete.

## Difference between `./data/derivatives` in and `results`

Prerpocessed first level data in `./data/derivatives`
Summary, second level data and meta data are in `results`.
Rule of thumb: data that might need permission to share, or too large for GitHub goes to `./data/derivatives`; otherwise `analysis`

## Framewise displacement threshold for quality assessments

The motion detection threshold is 0.5 mm for quality assessment and outlier frame cut-off in the heartbeat detection task. (c.f. 0.2 mm for resting state.)
I set the cut off at 20% of the volumes and then visually inspect the spiking.
