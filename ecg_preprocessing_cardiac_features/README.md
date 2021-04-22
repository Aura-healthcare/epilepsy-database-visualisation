# How to extract the cardiac features

## Prepare the environment
```bash
## Install python packages dependencies
foo@bar:pip install -r requirements.txt
```

## Extract the cardiac features from a single file
```bash
## Extract the RR-intervals
foo@bar: python3 ECG_detector_wrapper.py -i <your EDF file> -o <RR-json-result-file>

## Transform TSE annotations to JSON
foo@bar: python3 AnnotationExtractor.py -i <your Annotation TSE_BI file> -o <Annotation-json-result-file>


## Extract Cardiac feature on 1s splitted windows
foo@bar: python3 Cardiac_features_computation_wrapper.py -i <RR-json-result-file> -a <Annotation-json-result-file> -q <qrs-method-used:swt/gqrs/hamilton/emgelsee/xqrs> -o <json result file>
```

## Extract the cardiac feature from the full TUH database
```bash
## Extract the RR-intervals on the full database
foo@bar: ./loop_over_TUH_ECG_detector_wrapper.sh -i <Path-to-working-folder>/edf -o <Path-to-working-folder>/res-v0_6

## Transform TSE annotations to JSON on the full database
foo@bar: ./loop_over_TUH_Annotation_extractor.sh -i <Path-to-working-folder>/edf -o <Path-to-working-folder>/annot-v0_6

## Extract Cardiac feature on the full database
foo@bar: ./loop_over_TUH_Cardiac_features_computation_wrapper.sh -i <Path-to-working-folder>/edf -o <Path-to-working-folder>/res-v0_6 -a <Path-to-working-folder>/annot-v0_6 -o <Path-to-working-folder>/feats-v0_6
```
