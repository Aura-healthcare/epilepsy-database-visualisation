import numpy as np
# install from https://pypi.org/project/py-ecg-detectors/
from ecgdetectors import Detectors
from wfdb import processing
import pandas as pd
import biosppy.signals.ecg as bsp_ecg

# We consider two matching QRS as QRS frames within a 50 milliseconds window
MATCHING_QRS_FRAMES_TOLERANCE = 50
# We consider the laximum duration of a beat in milliseconds - 33bpm
MAX_SINGLE_BEAT_DURATION = 1800


ecg_data = np.array(0)
data = {}
fs = 256  # Frequency of hearty patch


# List of RR detection algorithms


def detect_qrs_swt(ecg_data, fs):
    qrs_frames = []
    try:
        detectors = Detectors(fs)  # Explain why
        qrs_frames = detectors.swt_detector(ecg_data)
    except Exception:
        # raise ValueError("swt")
        print("Exception in detect_qrs_swt")
    return qrs_frames


def detect_qrs_xqrs(ecg_data, fs):
    qrs_frames = []
    try:
        qrs_frames = processing.xqrs_detect(sig=ecg_data, fs=fs, verbose=False)
    except Exception:
        print("Exception in detect_qrs_xqrs")
    # return qrs_frames.tolist()
    return qrs_frames


def detect_qrs_gqrs(ecg_data, fs):
    qrs_frames = []
    try:
        qrs_frames = processing.qrs.gqrs_detect(sig=ecg_data, fs=fs)
    except Exception:
        print("Exception in detect_qrs_gqrs")
    return qrs_frames.tolist()


def detect_qrs_hamilton(ecg_data, fs):
    qrs_frames = []
    try:
        qrs_frames = bsp_ecg.hamilton_segmenter(
            signal=np.array(ecg_data),
            sampling_rate=fs)[0]

    except Exception:
        # raise ValueError("xqrs")
        print("Exception in detect_qrs_hamilton")
    return qrs_frames

# Centralising function


def get_cardiac_infos(ecg_data, fs, method):
    if method == "xqrs":
        qrs_frames = detect_qrs_xqrs(ecg_data, fs)
    elif method == "gqrs":
        qrs_frames = detect_qrs_gqrs(ecg_data, fs)
    elif method == "swt":
        qrs_frames = detect_qrs_gqrs(ecg_data, fs)
    elif method == "hamilton":
        qrs_frames = detect_qrs_hamilton(ecg_data, fs)

    rr_intervals = np.zeros(0)
    hr = np.zeros(0)
    if len(qrs_frames):
        rr_intervals = to_rr_intervals(qrs_frames, fs)
        hr = to_hr(rr_intervals)
    return qrs_frames, rr_intervals, hr


# UTILITIES

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

    frame_tolerance = MATCHING_QRS_FRAMES_TOLERANCE * (
        0.001 / single_frame_duration)
    max_single_beat_frame_duration = MAX_SINGLE_BEAT_DURATION * (
        0.001 / single_frame_duration)

    # Catch complete failed QRS detection
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
        if (min_qrs_frame - previous_min_qrs_frame) > (
                max_single_beat_frame_duration):
            missing_beats_frames_count += (min_qrs_frame -
                                           previous_min_qrs_frame)

        # Matching frames

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

    correlation_coefs = 2 * matching_frames / (len(qrs_frames_1) +
                                               len(qrs_frames_2))

    missing_beats_duration = missing_beats_frames_count * single_frame_duration
    correlation_coefs = round(correlation_coefs, 2)
    return correlation_coefs, matching_frames, missing_beats_duration


class compute_heart_rate:

    def __init__(self, fs=256):
        self.fs = fs
        self.data = {"infos": {"sampling_freq": None
                               },
                     "gqrs": {"qrs": None,
                              "rr_intervals": None,
                              "hr": None
                              },
                     "xqrs": {"qrs": None,
                              "rr_intervals": None,
                              "hr": None
                              },
                     "swt": {"qrs": None,
                             "rr_intervals": None,
                             "hr": None
                             },
                     "hamilton": {"qrs": None,
                                  "rr_intervals": None,
                                  "hr": None
                                  },
                     }

    def compute(self, df_input, beginning_frame):

        ecg_data = np.array(df_input['signal'].values)

        qrs_frames_gqrs, rr_intervals_gqrs, hr_gqrs = \
            get_cardiac_infos(ecg_data, fs, "gqrs")  # Explain
        qrs_frames_xqrs, rr_intervals_xqrs, hr_xqrs = \
            get_cardiac_infos(ecg_data, fs, "xqrs")
        qrs_frames_swt, rr_intervals_swt, hr_swt = \
            get_cardiac_infos(ecg_data, fs, "swt")  # Explain
        qrs_frames_hamilton, rr_intervals_hamilton, hr_hamilton = \
            get_cardiac_infos(ecg_data, fs, "hamilton")

        hr_gqrs = hr_gqrs  # Explain
        hr_swt = hr_swt/2  # Explain

        qrs_frames_gqrs = beginning_frame + np.array(qrs_frames_gqrs)*(10**9)/fs
        qrs_frames_xqrs = beginning_frame + np.array(qrs_frames_xqrs)*(10**9)/fs
        qrs_frames_swt = beginning_frame + np.array(qrs_frames_swt)*(10**9)/fs
        qrs_frames_hamilton = beginning_frame + np.array(
            qrs_frames_hamilton)*(10**9)/fs

        self.data = {"infos": {"sampling_freq": fs
                               },
                     "gqrs": {"qrs": qrs_frames_gqrs,
                              "rr_intervals": rr_intervals_gqrs.tolist(),
                              "hr": hr_gqrs.tolist()
                              },
                     "xqrs": {"qrs": qrs_frames_xqrs,
                              "rr_intervals": rr_intervals_xqrs.tolist(),
                              "hr": hr_xqrs.tolist()
                              },
                     "swt": {"qrs": qrs_frames_swt,
                             "rr_intervals": rr_intervals_swt.tolist(),
                             "hr": hr_swt.tolist()
                             },
                     "hamilton": {"qrs": qrs_frames_hamilton,
                                  "rr_intervals": rr_intervals_hamilton.
                                  tolist(),
                                  "hr": hr_hamilton.tolist()
                                  }
                     }
    
