from optparse import OptionParser
import json
import pyedflib
import numpy as np
from ecgdetectors import Detectors
import wfdb
from wfdb import processing
import biosppy.signals.ecg as bsp_ecg
import biosppy.signals.tools as bsp_tools

import os

MATCHING_QRS_FRAMES_TOLERANCE = 50 # We consider two matching QRS as QRS frames within a 50 milliseconds window
MAX_SINGLE_BEAT_DURATION = 1800 # We consider the laximum duration of a beat in milliseconds - 33bpm

def get_cardiac_infos(ecg_data, fs, method):
    if method == "xqrs":
        qrs_frames = detect_qrs_xqrs(ecg_data, fs)
    elif method == "gqrs":
        qrs_frames = detect_qrs_gqrs(ecg_data, fs)
    elif method == "swt":
        qrs_frames = detect_qrs_swt(ecg_data, fs)
    elif method == "hamilton":
        qrs_frames = detect_qrs_hamilton(ecg_data, fs)
    else:
        qrs_frames = detect_qrs_engelsee(ecg_data, fs)

    rr_intervals = np.zeros(0)
    hr = np.zeros(0)
    if len(qrs_frames):
      rr_intervals = to_rr_intervals(qrs_frames, fs)
      hr = to_hr(rr_intervals)
    return qrs_frames, rr_intervals, hr

def detect_qrs_swt(ecg_data, fs):
    qrs_frames = []
    try:
        detectors = Detectors(fs)
        qrs_frames = detectors.swt_detector(ecg_data)
    except:
        # raise ValueError("swt")
        print("Exception in detect_qrs_swt")
    return qrs_frames

def detect_qrs_xqrs(ecg_data, fs):
    qrs_frames = []
    try:
        qrs_frames = processing.xqrs_detect(sig=ecg_data, fs=fs)
    except:
        print("Exception in detect_qrs_xqrs")
    return qrs_frames.tolist()

def detect_qrs_gqrs(ecg_data, fs):
    qrs_frames = []
    try:
        qrs_frames = processing.qrs.gqrs_detect(sig=ecg_data, fs=fs*2)
    except:
        print("Exception in detect_qrs_gqrs")
    return qrs_frames.tolist()

def detect_qrs_hamilton(ecg_data, fs):
    qrs_frames = []
    try:
        qrs_frames = bsp_ecg.ecg(signal=np.array(ecg_data), sampling_rate=fs, show=False)[2]
    except:
        # raise ValueError("xqrs")
        print("Exception in detect_qrs_gqrs")
    return qrs_frames.tolist()

def detect_qrs_engelsee(ecg_data, fs):
    qrs_frames = []
    try:
        qrs_frames = bsp_ecg.ecg(signal=ecg_data, sampling_rate=fs, show=False)[2]
        order = int(0.3 * fs)
        filtered, _, _ = bsp_tools.filter_signal(signal=ecg_data,
                                                 ftype='FIR',
                                                 band='bandpass',
                                                 order=order,
                                                 frequency=[3, 45],
                                                 sampling_rate=fs)
        rpeaks, = bsp_ecg.engzee_segmenter(signal=filtered, sampling_rate=fs)
        rpeaks, = bsp_ecg.correct_rpeaks(signal=filtered, rpeaks=rpeaks, sampling_rate=fs, tol=0.05)
        _, qrs_frames = bsp_ecg.extract_heartbeats(signal=filtered, rpeaks=rpeaks, sampling_rate=fs,
                                                       before=0.2, after=0.4)
    except:
        # raise ValueError("xqrs")
        print("Exception in detect_qrs_gqrs")
    return qrs_frames.tolist()

def get_ecg_labels(signal_labels):
    ecg_labels =  [l for l in signal_labels if ("EKG" in l.upper() or "ECG" in l.upper())]
    return ecg_labels

def to_rr_intervals(frame_data, fs):
    rr_intervals = np.zeros(len(frame_data) - 1)
    for i in range(0, (len(frame_data) - 1)):
        rr_intervals[i] = (frame_data[i+1] - frame_data[i]) * 1000.0 / fs

    return rr_intervals

def to_hr(rr_intervals):
    hr = np.zeros(len(rr_intervals))
    for i in range(0, len(rr_intervals)):
        hr[i] = (int)(60 * 1000 / rr_intervals[i])

    return hr

def compute_qrs_frames_correlation(fs, qrs_frames_1, qrs_frames_2):
    single_frame_duration = 1./fs

    frame_tolerance = MATCHING_QRS_FRAMES_TOLERANCE * 0.001 / single_frame_duration
    max_single_beat_frame_duration = MAX_SINGLE_BEAT_DURATION  * 0.001 / single_frame_duration

    #Catch complete failed QRS detection
    if (len(qrs_frames_1) == 0 or len(qrs_frames_2) == 0):
        return 0, 0, 0

    i = 0
    j = 0
    matching_frames = 0

    previous_min_qrs_frame = min(qrs_frames_1[0], qrs_frames_2[0])
    missing_beats_frames_count = 0

    while i < len(qrs_frames_1) and j < len(qrs_frames_2):
        min_qrs_frame = min(qrs_frames_1[i], qrs_frames_2[j])
        # Get missing detected beats intervals
        if (min_qrs_frame - previous_min_qrs_frame) > max_single_beat_frame_duration:
            missing_beats_frames_count += (min_qrs_frame - previous_min_qrs_frame)

        #Matching frames
        if abs(qrs_frames_2[j] - qrs_frames_1[i]) < frame_tolerance:
            matching_frames += 1
            i += 1
            j += 1
        else:
            # increment first QRS in frame list
            if min_qrs_frame == qrs_frames_1[i]:
                i += 1
            else:
                j += 1
        previous_min_qrs_frame = min_qrs_frame

    correlation_coefs = 2 * matching_frames / ( len(qrs_frames_1) + len(qrs_frames_2) )

    missing_beats_duration = missing_beats_frames_count * single_frame_duration
    return correlation_coefs, matching_frames, missing_beats_duration

def get_ref_file(input_filename):
    return os.path.basename(input_filename)

parser = OptionParser()
parser.add_option("-i", "--input_file", dest="input_filename",
                  help="input file path")
parser.add_option("-o", "--output_file", dest="output_filename",
                  help="output file path")
parser.add_option("-v", "--verbose",
                  action="store_const", const=1, dest="verbose")

(options, args) = parser.parse_args()


if not options.output_filename:
    raise ValueError("Invalid output filepath")
    exit()

if not options.output_filename.endswith(".json"):
    raise ValueError("Invalid output filepath - " + options.output_filename)
    exit()

output_filename = options.output_filename

if not options.input_filename:
    print("Invalid input filepath")
    exit()

input_filename = options.input_filename

try:
    f = pyedflib.EdfReader(input_filename)
    n = f.signals_in_file

    # Get general informations
    start_datetime = f.getStartdatetime()
    exam_duration = f.getFileDuration()

    # get ECG channel
    signal_labels = f.getSignalLabels()
    ecg_labels = get_ecg_labels(signal_labels)
    n_ecg_channels = len(ecg_labels)
    if n_ecg_channels != 1:
        raise ValueError("Invalid ECG channels - " + str(n_ecg_channels))

    ecg_label = ecg_labels[0]
    ecg_channel_index = signal_labels.index(ecg_label)

    # get ECG data and attributes
    ecg_data = f.readSignal(ecg_channel_index)
    fs = f.getSampleFrequency(ecg_channel_index)

    qrs_frames_1, rr_intervals_1, hr_1 = get_cardiac_infos(ecg_data, fs, "gqrs")
    qrs_frames_2, rr_intervals_2, hr_2 = get_cardiac_infos(ecg_data, fs, "xqrs")
    qrs_frames_3, rr_intervals_3, hr_3 = get_cardiac_infos(ecg_data, fs, "hamilton")
    qrs_frames_4, rr_intervals_4, hr_4 = get_cardiac_infos(ecg_data, fs, "engelsee")
    qrs_frames_5, rr_intervals_5, hr_5 = get_cardiac_infos(ecg_data, fs, "swt")

    frame_correl_12, matching_frames_12, missing_beats_duration_12 = compute_qrs_frames_correlation(fs, qrs_frames_1, qrs_frames_2)
    frame_correl_13, matching_frames_13, missing_beats_duration_13 = compute_qrs_frames_correlation(fs, qrs_frames_1, qrs_frames_3)
    frame_correl_14, matching_frames_14, missing_beats_duration_14 = compute_qrs_frames_correlation(fs, qrs_frames_1, qrs_frames_4)
    frame_correl_15, matching_frames_15, missing_beats_duration_15 = compute_qrs_frames_correlation(fs, qrs_frames_1, qrs_frames_5)

    frame_correl_23, matching_frames_23, missing_beats_duration_23 = compute_qrs_frames_correlation(fs, qrs_frames_2, qrs_frames_3)
    frame_correl_24, matching_frames_24, missing_beats_duration_24 = compute_qrs_frames_correlation(fs, qrs_frames_2, qrs_frames_4)
    frame_correl_25, matching_frames_25, missing_beats_duration_25 = compute_qrs_frames_correlation(fs, qrs_frames_2, qrs_frames_5)

    frame_correl_34, matching_frames_34, missing_beats_duration_34 = compute_qrs_frames_correlation(fs, qrs_frames_3, qrs_frames_4)
    frame_correl_35, matching_frames_35, missing_beats_duration_35 = compute_qrs_frames_correlation(fs, qrs_frames_3, qrs_frames_5)

    frame_correl_45, matching_frames_45, missing_beats_duration_45 = compute_qrs_frames_correlation(fs, qrs_frames_4, qrs_frames_5)



    print("Total detected QRS frames GQRS " + str(len(qrs_frames_1)) + " XQRS " + str(len(qrs_frames_2)) + " Hamilton " + str(len(qrs_frames_3)) + " Engelsee " + str(len(qrs_frames_4)) + " Swt " + str(len(qrs_frames_5)))
    print(hr_3)
    print(hr_1)

    data = {"infos": {"sampling_freq":fs, "start_datetime": start_datetime.strftime("%Y-%m-%dT%H:%M:%S"), "exam_duration": exam_duration, "ref_file": get_ref_file(input_filename)},
            "gqrs": {"qrs": qrs_frames_1, "rr_intervals":rr_intervals_1.tolist(), "hr": hr_1.tolist()},
            "xqrs": {"qrs": qrs_frames_2, "rr_intervals":rr_intervals_2.tolist(), "hr": hr_2.tolist()},
            "hamilton": {"qrs": qrs_frames_3, "rr_intervals":rr_intervals_3.tolist(), "hr": hr_3.tolist()},
            "engelsee": {"qrs": qrs_frames_4, "rr_intervals":rr_intervals_4.tolist(), "hr": hr_4.tolist()},
            "swt": {"qrs": qrs_frames_5, "rr_intervals":rr_intervals_5.tolist(), "hr": hr_5.tolist()},
            "score": {"corrcoefs":           [[1, frame_correl_12, frame_correl_13, frame_correl_14, frame_correl_15],
                                              [frame_correl_12, 1, frame_correl_23, frame_correl_24, frame_correl_25],
                                              [frame_correl_13, frame_correl_23, 1, frame_correl_34, frame_correl_35],
                                              [frame_correl_14, frame_correl_24, frame_correl_34, 1, frame_correl_45],
                                              [frame_correl_15, frame_correl_25, frame_correl_35, frame_correl_45, 1]],
                      "matching_frames":   [[len(qrs_frames_1), matching_frames_12, matching_frames_13, matching_frames_14, matching_frames_15],
                                            [matching_frames_12, len(qrs_frames_2), matching_frames_23, matching_frames_24, matching_frames_25],
                                            [matching_frames_13, matching_frames_23, len(qrs_frames_3), matching_frames_34, matching_frames_35],
                                            [matching_frames_14, matching_frames_24, matching_frames_34, len(qrs_frames_4), matching_frames_45],
                                            [matching_frames_15, matching_frames_25, matching_frames_35, matching_frames_45, len(qrs_frames_5)]],
                      "missing_beats_duration": [[len(qrs_frames_1), missing_beats_duration_12, missing_beats_duration_13, missing_beats_duration_14, missing_beats_duration_15],
                                            [missing_beats_duration_12, len(qrs_frames_2), missing_beats_duration_23, missing_beats_duration_24, missing_beats_duration_25],
                                            [missing_beats_duration_13, missing_beats_duration_23, len(qrs_frames_3), missing_beats_duration_34, matching_frames_35],
                                            [missing_beats_duration_14, missing_beats_duration_24, missing_beats_duration_34, len(qrs_frames_4), missing_beats_duration_45],
                                            [missing_beats_duration_15, missing_beats_duration_25, missing_beats_duration_35, missing_beats_duration_45, len(qrs_frames_5)]]}}
    try:
        json.dump(data, open(output_filename, "w"))
    except:
        print("Output file error")

except OSError as er:
    print(er)
    print("Cannot read file - " + input_filename)
    exit()
except ValueError as e:
    json.dump({"error": e} , open(output_filename, "w"))
