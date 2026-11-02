# Verification report (Review 2 final pass, 2026-11-02)

Environment: cloud Linux sandbox, 2 vCPU, no camera, no ESP32. Python 3.13, Tesseract 5.3.4. **Nothing below touches physical hardware.**

## Run during this pass
| Command | Outcome |
|---|---|
| `pytest tests -q` (repo, before changes) | 24 passed |
| `pytest tests -q` (after adding `tests/test_repo_files.py`, from a fresh extract of the ZIP) | **27 passed**, 0 failed, 0 skipped |
| `python3 -m acquisition.server --port 5071`, then POST of a sample image to `/api/wearable/upload` | Returned a 3-line text reply (`RETAKE` / guidance / `readable`) |
| `python3 scripts/01_make_dataset.py` (clean copy, ~82 s) | Regenerated 1,440 images; `manifest.csv` identical to the bundled one; all 27 sample images byte-identical |
| `python3 scripts/02_extract_features.py` then `scripts/03_train.py` (clean copy) | Exit 0; `ocr_raw.csv`, `dev_scores.csv`, `test_scores.csv`, `rejection_results.json`, `readability_results.json`, `guidance_results.json` identical to the recorded files |
| `python3 paper/build_paper.py` (x3), `slides/build_slides.py`, LibreOffice PDF conversion | Paper 6 pages, slides 36 |

## Not re-run in this pass
`scripts/04` (leave-one-source-out localisation), `05` (ablation/severity sweeps), `06` (tables/figures) and `07` (latency/memory; timing-dependent, will differ by machine). Their recorded outputs in `results/` are from the earlier session. `scripts/09_fig4_shots.py` was not re-run. Do not describe these as reproduced in this pass.

## Test-count reconciliation
Earlier documents said 24 tests; `tests/test_repo_files.py` added 3, so the suite is now **27**. `docs/Test_Report.md` is the detailed 24-test record from 2026-10-31 and is kept as history; its per-file table does not list the 3 new tests (they check Wokwi file consistency, no camera/network claims in the Wokwi sketch, and that the bundled synthetic sample runs through the pipeline). `tests/test_ui_playwright.py` has been flaky once (browser timing).

## Cannot be verified without hardware
Camera capture, board firmware compile/run on the XIAO ESP32S3 Sense, Wi-Fi transfer from the board, OLED reply on the board, physical laptop webcam. Wokwi (`hardware/wokwi_xiao_s3/`) showed compile/boot and the camera-probe failure only. The Review 2 Wokwi interface run (`hardware/wokwi_review2/`) has no recorded run or screenshot yet.
