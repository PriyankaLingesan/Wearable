| feature_set     | model            |   accuracy |   precision_macro |   recall_macro |   f1_macro |
|:----------------|:-----------------|-----------:|------------------:|---------------:|-----------:|
| quality_only    | SVM-RBF          |      0.785 |             0.795 |          0.739 |      0.755 |
| quality_only    | RandomForest     |      0.83  |             0.826 |          0.788 |      0.804 |
| quality_only    | GradientBoosting |      0.83  |             0.829 |          0.789 |      0.806 |
| quality_only    | ExtraTrees       |      0.799 |             0.796 |          0.752 |      0.768 |
| quality_only    | LogReg           |      0.753 |             0.742 |          0.694 |      0.705 |
| quality_only    | kNN              |      0.729 |             0.706 |          0.658 |      0.67  |
| quality_only    | MLP              |      0.858 |             0.845 |          0.824 |      0.833 |
| quality+ocr_unc | SVM-RBF          |      0.806 |             0.81  |          0.771 |      0.783 |
| quality+ocr_unc | RandomForest     |      0.826 |             0.805 |          0.792 |      0.793 |
| quality+ocr_unc | GradientBoosting |      0.844 |             0.834 |          0.819 |      0.826 |
| quality+ocr_unc | ExtraTrees       |      0.792 |             0.773 |          0.741 |      0.742 |
| quality+ocr_unc | LogReg           |      0.771 |             0.748 |          0.719 |      0.728 |
| quality+ocr_unc | kNN              |      0.747 |             0.723 |          0.687 |      0.691 |
| quality+ocr_unc | MLP              |      0.819 |             0.801 |          0.797 |      0.799 |