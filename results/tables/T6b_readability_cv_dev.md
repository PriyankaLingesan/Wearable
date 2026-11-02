| feature_set     | model            |   cv_f1_mean |   cv_f1_sd |   cv_acc_mean |
|:----------------|:-----------------|-------------:|-----------:|--------------:|
| quality_only    | RandomForest     |        0.804 |      0.029 |         0.841 |
| quality_only    | SVM-RBF          |        0.798 |      0.013 |         0.839 |
| quality_only    | GradientBoosting |        0.794 |      0.026 |         0.834 |
| quality_only    | MLP              |        0.784 |      0.023 |         0.826 |
| quality_only    | ExtraTrees       |        0.781 |      0.04  |         0.825 |
| quality_only    | LogReg           |        0.731 |      0.016 |         0.787 |
| quality_only    | kNN              |        0.719 |      0.043 |         0.782 |
| quality+ocr_unc | GradientBoosting |        0.809 |      0.024 |         0.845 |
| quality+ocr_unc | RandomForest     |        0.793 |      0.034 |         0.836 |
| quality+ocr_unc | SVM-RBF          |        0.787 |      0.014 |         0.83  |
| quality+ocr_unc | ExtraTrees       |        0.773 |      0.027 |         0.823 |
| quality+ocr_unc | MLP              |        0.771 |      0.021 |         0.817 |
| quality+ocr_unc | LogReg           |        0.76  |      0.009 |         0.811 |
| quality+ocr_unc | kNN              |        0.73  |      0.018 |         0.79  |