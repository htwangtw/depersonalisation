"""
Group level FSL using `randomised` in nypipe
"""

import os
import sys
import argparse

def run_group_randomised(args):
    from src.workflow import group_randomise_wf
    print(type(args.subject_list))
    workflow = group_randomise_wf(input_dir=args.input,
                                  output_dir=args.output,
                                  subject_list=args.subject_list,
                                  regressors_path=args.regressors,
                                  roi=args.roi
                                 )
    workflow.write_graph()
    workflow.run()
    return None

def main():
    parser=argparse.ArgumentParser(description="group level analysis with FSL `randomise`")
    parser.add_argument("-s", help="a list of subject ID", dest="subject_list",
                        type=str, nargs="*", required=True)
    parser.add_argument("-i", help="BIDS like derivative - first level feat dir",
                        dest="input", type=str, required=True)
    parser.add_argument("-r", help="noise regressors and group membership",
                        dest="regressors", type=str, required=True)
    parser.add_argument("-o", help="Output dir",
                        dest="output", type=str , required=True)
    parser.add_argument("-m", help="ROI mask (default: full brain)",
                        dest="roi", required=False)

    parser.set_defaults(func=run_group_randomised)
    args=parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
