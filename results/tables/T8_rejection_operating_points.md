| strategy                          |   target_accepted_error |     tau |   test_coverage |   test_rejection_rate |   test_accepted_error |   accepted |   accepted_errors |
|:----------------------------------|------------------------:|--------:|----------------:|----------------------:|----------------------:|-----------:|------------------:|
| S0 accept-all                     |                    0.01 | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S0 accept-all                     |                    0.02 | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S0 accept-all                     |                    0.05 | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S0 accept-all                     |                    0.1  | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S1 OCR conf (raw)                 |                    0.01 |   0.894 |           0.014 |                 0.986 |                 0.5   |          4 |                 2 |
| S1 OCR conf (raw)                 |                    0.02 |   0.877 |           0.028 |                 0.972 |                 0.375 |          8 |                 3 |
| S1 OCR conf (raw)                 |                    0.05 |   0.862 |           0.09  |                 0.91  |                 0.154 |         26 |                 4 |
| S1 OCR conf (raw)                 |                    0.1  |   0.796 |           0.399 |                 0.601 |                 0.209 |        115 |                24 |
| S2 rule gate + OCR conf           |                    0.01 |   0.894 |           0.003 |                 0.997 |                 1     |          1 |                 1 |
| S2 rule gate + OCR conf           |                    0.02 |   0.894 |           0.003 |                 0.997 |                 1     |          1 |                 1 |
| S2 rule gate + OCR conf           |                    0.05 |   0.862 |           0.052 |                 0.948 |                 0.133 |         15 |                 2 |
| S2 rule gate + OCR conf           |                    0.1  |   0.777 |           0.243 |                 0.757 |                 0.257 |         70 |                18 |
| S3 OCR-uncertainty only (learned) |                    0.01 |   0.938 |           0.156 |                 0.844 |                 0     |         45 |                 0 |
| S3 OCR-uncertainty only (learned) |                    0.02 |   0.938 |           0.156 |                 0.844 |                 0     |         45 |                 0 |
| S3 OCR-uncertainty only (learned) |                    0.05 |   0.861 |           0.34  |                 0.66  |                 0.051 |         98 |                 5 |
| S3 OCR-uncertainty only (learned) |                    0.1  |   0.684 |           0.538 |                 0.462 |                 0.161 |        155 |                25 |
| S4 quality only (learned)         |                    0.01 |   1     |           0.007 |                 0.993 |                 0     |          2 |                 0 |
| S4 quality only (learned)         |                    0.02 |   0.98  |           0.045 |                 0.955 |                 0     |         13 |                 0 |
| S4 quality only (learned)         |                    0.05 |   0.909 |           0.111 |                 0.889 |                 0.094 |         32 |                 3 |
| S4 quality only (learned)         |                    0.1  |   0.857 |           0.257 |                 0.743 |                 0.108 |         74 |                 8 |
| S5 quality + OCR-uncertainty      |                    0.01 |   0.981 |           0.135 |                 0.865 |                 0     |         39 |                 0 |
| S5 quality + OCR-uncertainty      |                    0.02 |   0.929 |           0.25  |                 0.75  |                 0.028 |         72 |                 2 |
| S5 quality + OCR-uncertainty      |                    0.05 |   0.917 |           0.302 |                 0.698 |                 0.057 |         87 |                 5 |
| S5 quality + OCR-uncertainty      |                    0.1  |   0.583 |           0.531 |                 0.469 |                 0.157 |        153 |                24 |
| S6 + grammar validity (ablation)  |                    0.01 |   0.923 |           0.253 |                 0.747 |                 0     |         73 |                 0 |
| S6 + grammar validity (ablation)  |                    0.02 |   0.889 |           0.312 |                 0.688 |                 0.056 |         90 |                 5 |
| S6 + grammar validity (ablation)  |                    0.05 |   0.867 |           0.382 |                 0.618 |                 0.1   |        110 |                11 |
| S6 + grammar validity (ablation)  |                    0.1  |   0.667 |           0.549 |                 0.451 |                 0.177 |        158 |                28 |