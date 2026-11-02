# Models and their roles (from the code in this repository)

The system is a **pipeline of several components**, not one ML model. All were fitted/evaluated on SYNTHETIC data only.

| Stage | Component | Where | Role | Trained here? |
|---|---|---|---|---|
| 1 | Frame validation (size, blur, blank, format) | `acquisition/validate.py` | Refuse unusable uploads/frames before processing | No (rules) |
| 2 | Hallmark localisation, `contour` method (also `mser`, `ocrdet`, `full` benchmarked) | `src/hallmark/localize.py` | Find the inscription region; parameters tuned on the development split | No (classical CV) |
| 3 | RapidOCR (PP-OCR recogniser, ONNX Runtime, detector and angle classifier off) | `src/hallmark/ocr.py` | **Primary** text reader (raw ROI) | Pretrained, not trained here |
| 3 | Tesseract 5 (whitelist A-Z0-9, PSM 7) | `src/hallmark/ocr.py` | **Secondary** reader; its disagreement with RapidOCR is an uncertainty feature | Pretrained, not trained here |
| 4 | Random Forest (300 trees) | `models/readability.joblib`, `src/hallmark/models.py` | Classifies readability class (readable / partial / unreadable) from quality + OCR-uncertainty features. Labels are a **synthetic proxy** (derived from the rendering parameters) | Yes, synthetic |
| 5 | ExtraTrees (400 trees) + isotonic calibration (`CalibratedRejector`) | `models/rejector.joblib` | Predicts P(transcription correct); a threshold chosen on out-of-fold development scores for a target accepted-error rate accepts or rejects the reading | Yes, synthetic |
| 6 | Rule-based guidance (`Guidance`) | `models/guidance.joblib` | Names the likeliest capture problem (blur, glare, dark, uneven light, too small) from standardised quality deficits | Fitted statistics only |

Selection of deployed components is recorded in `models/deployment.json` (`rejector: ExtraTrees`, `readability: RandomForest`, primary `rapidocr/raw`, secondary `tesseract/red`). Other candidates (gradient boosting, logistic regression) were compared in `scripts/03_train.py` and are not deployed.

Note: `taus_ucb` in `models/deployment.json` contains `Infinity` for one target (no threshold met the upper-confidence-bound criterion); this is expected output, not corruption, but it is not strict JSON, so read it with Python's `json`.

Not claimed anywhere: purity detection, authentication, BIS verification, real-jewellery performance.
