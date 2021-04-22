from optparse import OptionParser
import json

parser = OptionParser()
parser.add_option("-a", "--annotations_file", dest="annotations_filename",
                  help="annotations file path")
parser.add_option("-o", "--output_file", dest="output_filename",
                  help="output file path")
parser.add_option("-v", "--verbose",
                  action="store_const", const=1, dest="verbose")

(options, args) = parser.parse_args()

if not options.annotations_filename:
    raise ValueError("Invalid annotations filepath")
    exit()


if not options.output_filename:
    raise ValueError("Invalid output filepath")
    exit()

if not options.output_filename.endswith(".json"):
    raise ValueError("Invalid output filepath - " + options.output_filename)
    exit()

annotations_filename = options.annotations_filename
output_filename = options.output_filename

background_intervals = []
seizure_intervals = []

SEIZURE_TAG = "seiz"
BACKGROUND_TAG = "bckg"
with open(annotations_filename, "r") as f:
    print(f)
    if annotations_filename.endswith("tse_bi"):
        for line in f:
            tokens = line.split(" ")
            if(len(tokens) == 4):
                if tokens[2] == SEIZURE_TAG:
                    seizure_intervals.append([float(tokens[0]), float(tokens[1])])
                elif tokens[2] == BACKGROUND_TAG:
                    background_intervals.append([float(tokens[0]), float(tokens[1])])

data = {"background": background_intervals, "seizure": seizure_intervals}
with open(output_filename, "w") as out_f:
    json.dump(data, out_f)
