| strategy                          |   target_accepted_error |     tau |   test_coverage |   test_rejection_rate |   test_accepted_error |   accepted |   accepted_errors |
|:----------------------------------|------------------------:|--------:|----------------:|----------------------:|----------------------:|-----------:|------------------:|
| S0 accept-all                     |                    0.01 | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S0 accept-all                     |                    0.02 | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S0 accept-all                     |                    0.05 | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S0 accept-all                     |                    0.1  | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S1 OCR conf (raw)                 |                    0.01 | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S1 OCR conf (raw)                 |                    0.02 | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S1 OCR conf (raw)                 |                    0.05 | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S1 OCR conf (raw)                 |                    0.1  |   0.819 |           0.285 |                 0.715 |                 0.195 |         82 |                16 |
| S2 rule gate + OCR conf           |                    0.01 | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S2 rule gate + OCR conf           |                    0.02 | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S2 rule gate + OCR conf           |                    0.05 | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S2 rule gate + OCR conf           |                    0.1  |   0.819 |           0.146 |                 0.854 |                 0.19  |         42 |                 8 |
| S3 OCR-uncertainty only (learned) |                    0.01 | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S3 OCR-uncertainty only (learned) |                    0.02 |   0.938 |           0.156 |                 0.844 |                 0     |         45 |                 0 |
| S3 OCR-uncertainty only (learned) |                    0.05 |   0.929 |           0.312 |                 0.688 |                 0.056 |         90 |                 5 |
| S3 OCR-uncertainty only (learned) |                    0.1  |   0.714 |           0.441 |                 0.559 |                 0.094 |        127 |                12 |
| S4 quality only (learned)         |                    0.01 | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S4 quality only (learned)         |                    0.02 | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S4 quality only (learned)         |                    0.05 | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S4 quality only (learned)         |                    0.1  |   0.875 |           0.212 |                 0.788 |                 0.115 |         61 |                 7 |
| S5 quality + OCR-uncertainty      |                    0.01 | nan     |           0     |                 1     |               nan     |          0 |                 0 |
| S5 quality + OCR-uncertainty      |                    0.02 |   1     |           0.083 |                 0.917 |                 0     |         24 |                 0 |
| S5 quality + OCR-uncertainty      |                    0.05 |   0.917 |           0.302 |                 0.698 |                 0.057 |         87 |                 5 |
| S5 quality + OCR-uncertainty      |                    0.1  |   0.667 |           0.517 |                 0.483 |                 0.148 |        149 |                22 |
| S6 + grammar validity (ablation)  |                    0.01 |   1     |           0.233 |                 0.767 |                 0     |         67 |                 0 |
| S6 + grammar validity (ablation)  |                    0.02 |   0.923 |           0.253 |                 0.747 |                 0     |         73 |                 0 |
| S6 + grammar validity (ablation)  |                    0.05 |   0.868 |           0.368 |                 0.632 |                 0.075 |        106 |                 8 |
| S6 + grammar validity (ablation)  |                    0.1  |   0.667 |           0.549 |                 0.451 |                 0.177 |        158 |                28 |