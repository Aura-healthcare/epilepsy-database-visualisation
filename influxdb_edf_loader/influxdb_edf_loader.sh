#!/bin/bash


while getopts ":i:v:t:" option
do
case "${option}"
in
i) SearchDest=${OPTARG};;
v) Version=${OPTARG};;
t) Token=${OPTARG};;
esac
done

# Check script input integrity
if [[ $SearchDest ]] || [[ $Version ]] || [[ $Token ]];
then
  echo "Start loading processing"
else
  echo "No Search directory: $SearchDest, Version or Token: $TargetDest, use -i -v -t options" >&2
  exit 1
fi


#Hack to force the bash to split command result only on newline char
#It is done to support the spaces in the folder names
OIFS="$IFS"
IFS=$'\n'

for EDF_FILE in $(find $SearchDest* -type f -name "*.edf" ); 
do
	echo loading $EDF_FILE
	for CHANNEL in ECG1+ECG1-
#	for CHANNEL in BEAT+BEAT- C3G2 C4G2 CzG2 ECG1+ECG1- EMG1+EMG1- EMG2G2 EMG3G2 EMG5G2 EMG6+EMG6- EOG+EOG- F10G2 F3G2 F4G2 F7G2 F8G2 F9G2 Fp1G2 Fp2G2 FzG2 MKR+MKR- O1G2 O2G2 P10G2 P3G2 P4G2 P7G2 P8G2 P9G2 PULS+PULS- Pos+Pos- PzG2 SpO2+SpO2- T10G2 T7G2 T8G2 T9G2 abdo+abdo- emg4+emg4- thor+thor-thor-
	do
		echo channel: $CHANNEL
		python3  influxdb_hr_loader.py -i $EDF_FILE -c $CHANNEL -v $Version -t $Token
		if [ $? -eq 0 ]
		then
			echo "File $EDF_FILE processed"
		else
			echo "Failed to process $EDF_FILE" >&2
		fi
	done
done


IFS="$IFS"
exit 0