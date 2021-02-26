import pandas as pd
import numpy as np
from tqdm import tqdm
from influxdb_client import InfluxDBClient, Point
from pyedflib import highlevel
from pyedflib import edfreader
from optparse import OptionParser
import re


class InfluxdbLoader:

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
            self.headers['startdate'])
        # For French hour, UTC+1 (no summer date) and
        # months currently start at 0
        self.startdate = self.startdate.replace(
            month=self.startdate.month + 1) + pd.Timedelta(hours=1)

        # InfluxDB API
        self.base = 'ecg_lateppe'
        self.token = token
        self.org = "datasciences"
        self.bucket = "ecg_classif"
        self.client = InfluxDBClient(url="http://localhost:8086",
                                     token=self.token)
        self.write_client = self.client.write_api()
        self.batch_size = batch_size

    def load_edf(self,
                 channel_name: str) -> pd.DataFrame:

        self.fs = self.headers[
            'SignalHeaders'][
                self.channels.index(channel_name)]['sample_rate']
        with edfreader.EdfReader(self.edf_file) as f:
            signals = f.readSignal(self.channels.index(channel_name))

        df = pd.DataFrame(signals,
                          columns=['signal'],
                          index=pd.date_range(self.startdate,
                                              periods=len(signals),
                                              freq='{}ns'.format(
                                                  int(1/self.fs*1_000_000_000))
                                              ))
        return df



    def prepare_batch(self,
                     ecg_array: np.ndarray,
                     timestamps_array: pd.Timestamp,
                     channel_name: str) -> Point:

        # Prepare a batch of data to be sent in InfluxDB with proper format

        point_list = [Point("ecg_signal").
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

    def load_data(self, channel_name: str):

        # For a channel, prepare the data by batch and sent it to InfluxDB

        df_ecg = self.load_edf(channel_name=channel_name)

        for i in tqdm(range(0, df_ecg.shape[0], self.batch_size)):
            ecg_array = df_ecg['signal'].iloc[i:i+self.batch_size].values
            timestamps_array = df_ecg.index[i:i+self.batch_size]
            point_list = self.prepare_batch(
                ecg_array=ecg_array,
                timestamps_array=timestamps_array,
                channel_name=channel_name)
            self.write_client.write(self.bucket, self.org, point_list)

        print('all loaded :) ')


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
