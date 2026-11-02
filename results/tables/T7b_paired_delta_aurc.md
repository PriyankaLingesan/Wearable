| comparison                                                             |   delta_AURC | CI95             | excludes_zero   |
|:-----------------------------------------------------------------------|-------------:|:-----------------|:----------------|
| S5 quality + OCR-uncertainty  minus  S3 OCR-uncertainty only (learned) |        0     | [-0.009, +0.010] | False           |
| S4 quality only (learned)  minus  S1 OCR conf (raw)                    |       -0.034 | [-0.084, +0.009] | False           |
| S3 OCR-uncertainty only (learned)  minus  S1 OCR conf (raw)            |       -0.09  | [-0.146, -0.041] | True            |
| S5 quality + OCR-uncertainty  minus  S4 quality only (learned)         |       -0.056 | [-0.091, -0.028] | True            |