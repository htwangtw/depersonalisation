# Heightened dissociation in patients with first episode psychosis linked to interoceptive disturbance

Depersonalisation projects links to manuscript WIP lead by Sarah Garfinkel.
Data originally collected and analysed by Geoff Davies, Charlotte Rae, and Cassandra Gould van Praag.
The current version in this folder is curated and analysed by Hao-Ting Wang.

## Repository overview
<details>
  <summary>Expand to see the tree</summary>

```
./
├── data/
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
├── references/
├── results/
├── scratch/
├── scripts/
├── Makefile
├── requirements.txt
└── README.md
```
</details>


## Using the material in this repo:
<details>
  <summary>create `virtualenv`</summary>
  Recommanded steps:

  ```
  cd /path/to/project/
  make install
  source env/bin/activate
  ```
  ### Important note on dependecy
  We used a patched version of `tftb`. The pip image hasn't been updated yet.
  ```
  pip install git+https://github.com/htwangtw/tftb.git@spwv_fix
  ```
  This step is not needed if you use the `Makefile` to create the environment
  ```
  make install
  ```
</details>

<details>
  <summary>data</summary>

  This is a BIDS directory containing the raw data (`sourcedata`), BIDS compiled Nifti, and minimally preprocessed dataset for statistical modeling (`derivatives`).
</details>

<details>
  <summary>scripts</summary>

  Analysis and visualisation code, including FSL design files
</details>


<details>
  <summary>references</summary>

  Code from referenced study, MNI space seed/gray matter masks
</details>

<details>
  <summary>results</summary>

  Outputs from `scripts`, includes figures, important interim data, manuscripts.
  Includes copy of metadata to produce the final figures.

  ### Difference between `./data/derivatives` in and `results`

  Prerpocessed first level data in `./data/derivatives`
  Summary, second level data and meta data are in `results`.
  Rule of thumb: data that might need permission to share, or too large for GitHub goes to `./data/derivatives`; otherwise `analysis`
</details>

<details>
  <summary>Misc</summary>

  ### scratch
  Scratch folder. Delete after a project is complete.
</details>


## Notes on preprocessing

Framewise displacement threshold for quality assessments

The motion detection threshold is 0.5 mm for quality assessment and outlier frame cut-off in the heartbeat detection task. (c.f. 0.2 mm for resting state.)
I set the cut off at 20% of the volumes and then visually inspect the spiking
