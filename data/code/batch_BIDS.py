import os, glob
import re

# Note: study ID conflict - CISC9097 (behavioural data doesn't exist/didn't pass quality check)
# All files convered and DICOM deleted: HTW 13.11.2019

# direct working dir to /research/cisc2/critchley_depersonalisation
# local copy of DICOM has been removed for space saving

dcm = sorted([i.split('/')[-1].split('CISC')[-1] for i in glob.glob('data/sourcedata/DICOM/CISC*')])

# weird file structure
os.system(
'''
heudiconv \
    -d data/sourcedata/DICOM/CISC{subject}/session-*/????????/??????.??????/*/* \
    -o data -f data/code/src/heuristic.py -s 9389 \
    -c dcm2niix -b --overwrite
''')

os.system(
'''
heudiconv \
    -d data/sourcedata/DICOM/CISC{subject}/session-*/????????/??????.??????/* \
    -o data -f data/code/src/heuristic.py -s 9933 \
    -c dcm2niix -b --overwrite
''')

# most of the subjects
docker_cmd = '''
heudiconv \
    -d data/sourcedata/DICOM/CISC{subject}/session-*/*/*/* \
    -o data -f data/code/src/heuristic.py -s %s \
    -c dcm2niix -b --overwrite
'''

subj_lst = dcm
for ID in subj_lst:
    # get the subject id
    print(ID)
    # get sessions
    sessions = glob.glob('data/sourcedata/DICOM/CISC{}/session*'.format(ID))
    os.system(docker_cmd %(ID))


# get the rest of the unconverted ones
bids = [i.split('/')[-1].split('-')[-1] for i in glob.glob('data/sub-*')]
subj_lst = list(set(dcm).difference(set(bids)))

docker_cmd = '''
heudiconv \
    -d data/sourcedata/DICOM/CISC{subject}/session-{session}/*/*/*/* \
    -o data -f data/code/src/heuristic.py -s %s \
    -c dcm2niix -b --overwrite
'''
for ID in subj_lst:
    # get the subject id
    print(ID)
    # get sessions
    sessions = glob.glob('data/sourcedata/DICOM/CISC{}/session*'.format(ID))
    if len(sessions) > 1:
        print('skip %s' %(ID))
    else:
        os.system(docker_cmd %(ID))

# participants with two sessions
os.system(
'''
heudiconv \
    -d data/sourcedata/DICOM/CISC{subject}/session-{session}/????????/??????.??????/* \
    -o data -f data/code/src/heuristic.py -s 10048 -ss 01 \
    -c dcm2niix -b --overwrite
''')

os.system(
'''
heudiconv \
    -d data/sourcedata/DICOM/CISC{subject}/session-{session}/????????/??????.??????/* \
    -o . -f data/code/src/heuristic.py -s 10048 -ss 02 \
    -c dcm2niix -b --overwrite
''')

os.system(
'''
heudiconv \
    -d data/sourcedata/DICOM/CISC{subject}/session-{session}/????????/??????.??????/* \
    -o data -f data/code/src/heuristic.py -s 8494 -ss 01 \
    -c dcm2niix -b --overwrite
''')

os.system(
'''
heudiconv \
    -d data/sourcedata/DICOM/CISC{subject}/session-{session}/????????/??????.??????/* \
    -o data -f data/code/src/heuristic.py -s 8494 -ss 02 \
    -c dcm2niix -b --overwrite
''')
