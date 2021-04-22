import pandas as pd
import numpy as np
from tqdm import tqdm
from influxdb_client import InfluxDBClient, Point
from pyedflib import highlevel
from pyedflib import edfreader
from optparse import OptionParser
from typing import List
import re
from rr_detection import compute_heart_rate


class InfluxdbLoader:

    # The purpose of this class is to prepare and use parameters to read an 
    # edf file, then for a channel prepare and send the ECG data in InfluxDB
    # by batch

    def __init__(self,
                 edf_file: str,
                 version: str,
                 token: str,
                 batch_size: int = 50_000):

        self.edf_file = edf_file
        self.version = version

        self.headers = highlevel.read_edf_header(self.edf_file)
        self.channels = self.headers['channels']

        file_pattern = self.edf_file[re.search('PAT_*', edf_file).start():]
        self.patient_name = file_pattern[:re.search('/', file_pattern).start()]
        edf_file_name = file_pattern[re.search('/', file_pattern).start()+1:]
        self.segment = edf_file_name[-5:][0]
        self.record = edf_file_name[-9:][:2]

        self.startdate = pd.to_datetime(
            self.headers['startdate']) + pd.Timedelta(hours=1)

        # InfluxDB API
        self.base = 'ecg_lateppe'
        self.token = token
        self.org = "datasciences"
        self.bucket = "ecg_classif"
        self.client = InfluxDBClient(url="http://localhost:8086",
                                     token=self.token)
        self.write_client = self.client.write_api()
        self.batch_size = batch_size

    def convert_edf_to_dataframe (self,
                                  channel_name: str) -> pd.DataFrame:

        # From its path, load an edf file for a selected channel and
        # adapt it in DataFrame

        self.fs = self.headers[
            'SignalHeaders'][
            self.channels.index(channel_name)]['sample_rate']
        with edfreader.EdfReader(self.edf_file) as f:
            signals = f.readSignal(self.channels.index(channel_name))

        freq_ns = int(1/self.fs*1_000_000_000)
        df = pd.DataFrame(signals,
                          columns=['signal'],
                          index=pd.date_range(self.startdate,
                                              periods=len(signals),
                                              freq=f'{freq_ns}ns'
                                              ))
        return df


    def prepare_batch(self,
                     ecg_array: np.ndarray,
                     timestamps_array: pd.Timestamp,
                     channel_name: str) -> List[Point]:

        # Prepare a batch of data to be sent in InfluxDB with proper format
        
        print(f'batch from {timestamps_array[0]} to {timestamps_array[-1]}')
        print(f'sample : {ecg_array[:10]}')


        point_list = [Point("VNS").
                      tag("patient", self.patient_name).
                      tag("base", self.base).
                      tag("segment", self.segment).
                      tag("channel", channel_name).
                      tag("version", self.version).
                      tag("record", self.record).
                      field("signal", ecg_array[i]).
                      time(timestamps_array[i])
                      for i in range(len(ecg_array))]

        return point_list

    def load_data(self, channel_name: str = 'ECG1+ECG1-'):

        # For a channel, prepare the data by batch and sent it to InfluxDB

        df_hr = self.convert_edf_to_dataframe(channel_name=channel_name)

        df_input = df_hr
        compute_hr = compute_heart_rate(fs=self.fs)
        compute_hr.compute(df_input=df_input, beginning_frame=int(self.startdate.value))
        data = compute_hr.data

        for algorithm in ['hamilton', 'swt', 'xqrs']:

            print(f'Starting algorithm {algorithm}')

            df_hr = self.hr_data_to_df(data, algorithm=algorithm)

            for batch_iteration in tqdm(range(0, df_hr.shape[0], self.batch_size)):
                ecg_array = df_hr['signal'].iloc[
                    batch_iteration:batch_iteration+self.batch_size].values
                timestamps_array = df_hr.index[
                    batch_iteration:batch_iteration+self.batch_size]
                point_list = self.prepare_batch(
                    ecg_array=ecg_array,
                    timestamps_array=timestamps_array,
                    channel_name=algorithm)
                self.write_client.write(self.bucket, self.org, point_list)

        print('all loaded :) ')

    def hr_data_to_df(self, hr_data, algorithm='hamilton'):

        qrs = hr_data[algorithm]['qrs'][:-1]
        hr = hr_data[algorithm]['hr']

        df = pd.DataFrame(hr, columns=['signal'])
        df.index = [pd.Timestamp(x) for x in qrs]

        return df


if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option("-i", "--input_file", dest="input_file",
                      help="input edf file", metavar="FILE")
    parser.add_option("-c", "--channel", dest="channel",
                      help="channel to load", metavar="FILE")
    parser.add_option("-v", "--version", dest="version",
                      help="version tag in influxdb", metavar="FILE")
    parser.add_option("-t", "--token", dest="token",
                      help="token for InfluxDB", metavar="FILE")

    (options, args) = parser.parse_args()

    loader = InfluxdbLoader(edf_file=options.input_file,
                            version=options.version,
                            token=options.token)

    loader.load_data(options.channel)
