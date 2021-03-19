# How to extract the cardiac features

## Prepare the environment
```bash
## Install python packages dependencies
foo@bar:pip install -r requirements.txt
```

## Extract the cardiac features
```bash
## Extract the RR-intervals
foo@bar: python3 ECG_detector_wrapper.py -i <your EDF file> -o <RR-json-result-file>

## Transform TSE annotations to JSON
foo@bar: python3 AnnotationExtractor.py -i <your Annotation TSE_BI file> -o <Annotation-json-result-file>


## Extract Cardiac feature on 1s splitted windows
foo@bar: python3 Cardiac_features_computation_wrapper.py -i <RR-json-result-file> -a <Annotation-json-result-file> -q <qrs-method-used:swt/gqrs/hamilton/emgelsee/xqrs> -o <json result file>
```
