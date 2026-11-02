# Presentation script

## Slide 1: Wearable Computing Course Project

Welcome. This project is a simulation-based study of a wrist-worn assistant that reads a hallmark inscription, estimates how trustworthy its own reading is, and tells the wearer how to retake a bad capture. Two disclosures up front: no hardware was built, and all images are synthetic. And it reads characters only; it never claims authenticity or purity.

## Slide 2: Introduction and Motivation

Hallmarks are small and low contrast. OCR engines return a confident string even when it is wrong, so a silent misread costs more than a retake. A wrist camera keeps both hands free and sees held objects at a useful scale (Ohnishi et al.), and finger-worn readers show that feedback on alignment and focus helps capture (FingerReader).

## Slide 3: Problem Statement

Formally: given a frame we output a transcription, a calibrated score and a decision. Correct means whitespace-insensitive exact match. The score should estimate the probability the transcription is right, and the threshold is chosen for a target accepted-error rate. Explicitly out of scope: purity, authenticity, standards compliance.

## Slide 4: Objectives

Nine objectives, O1 to O9; O7 to O9 are the wearable interface, electronics and image acquisition. The central research question is O3: does combining image-quality assessment with OCR uncertainty reduce incorrectly accepted transcriptions compared to raw OCR confidence?

## Slide 5: Literature Review (verified sources only)

The paper cites twenty verified sources, including three hardware and simulator documentation pages for the wearable design. Closest to our task: goldsmith's-mark retrieval in silverware, which identifies marks by retrieval rather than reading characters. For OCR: Tesseract and PP-OCR. For confidence: calibration, maximum-probability baselines, scene-text calibration. Selective prediction: Chow, El-Yaniv, Geifman. Quality: no-reference gradient and contrast statistics. No peer-reviewed work on OCR of engraved hallmarks was found in our bounded search.

## Slide 6: Research Gap and Contribution

The gap is a combination: quality assessment, OCR uncertainty, calibrated abstention, and recapture advice for engraved inscriptions on a wearable. This is a statement about our bounded search, not proof of absence; we claim no novelty beyond this combination.

## Slide 7: Wearable Concept: Wrist Camera + Companion

The system has two parts. The wrist unit is one Seeed XIAO ESP32S3 Sense board with its proposed camera module (OV5640 with autofocus, unconfirmed until a kit is received) as the primary sensor, a white LED for illumination, a push button and a small OLED. The companion is a laptop running the Python pipeline, which does all recognition. When the button is pressed the unit lights the LED, captures a JPEG, sends it in one HTTP POST over Wi-Fi and shows the three-line text reply. Be clear about status: the physical design is proposed and was not built; the Python pipeline and the HTTP receiver are implemented; the firmware was only compiled and booted in Wokwi, which has no camera part; and the receiver was tested with a Python client, not with the device.

## Slide 8: System Architecture

Read the figure by section. Section A, the proposed wrist unit: the LED lights the hallmark, the proposed camera module (OV5640 with autofocus, unconfirmed) on the XIAO ESP32S3 Sense is the sensor, the same board sends the JPEG in one HTTP POST over Wi-Fi. Section B, the companion, which is implemented: acquisition, quality assessment, localisation, parallel OCR with RapidOCR and Tesseract, OCR uncertainty with the Random Forest readability class, calibrated rejection with ExtraTrees and isotonic calibration, and result plus guidance. The reply comes back in the same HTTP response as three lines of text and the board shows it on its OLED. The wrist block is proposed and not built.

## Slide 9: Camera and Illumination Design

We compared the XIAO ESP32S3 Sense, the AI-Thinker ESP32-CAM, the ESP32 DevKit-C V4 with a camera breakout, the Raspberry Pi camera and a USB macro camera. The XIAO ESP32S3 Sense is selected: the camera sits on the board-to-board connector and the board has eight megabytes of PSRAM and headers for the OLED, button and drivers. The proposed camera is the OV5640 autofocus module the vendor lists for the Sense, but the vendor also says boards may ship with an OV5640 or an OV3660, and older pages describe an OV2640, so the fitted module is unconfirmed. No field of view or focus range is listed, so the figures on this slide are an illustrative placeholder taken from the OV2640 Arducam page, not OV5640 values: about 23 millimetres field of view at 30 millimetres, about 68 pixels per millimetre. All optical values must be measured on the delivered module. A USB macro camera on the companion is the fallback. Wokwi cannot simulate a camera, so this is a drawing and the experiments use synthetic images.

## Slide 10: Wearable Camera: Architecture Decision

The earlier circuit had no camera, which was a gap. A DVP camera needs fourteen signals: eight data lines, the clock, pixel clock, vertical and horizontal sync, and two for the camera I2C bus. A DevKit-C V4 is not a camera board and would have little I/O left, and we did not verify that its module has the PSRAM that large JPEG frames need. The AI-Thinker ESP32-CAM leaves only six GPIOs free, each shared with the microSD socket or the flash LED, has no USB port and wants a five volt supply of at least two amps, so it cannot also run an OLED, a button and an LED driver. The XIAO ESP32S3 Sense carries the ESP32-S3 and the camera on one small board, so one board both acquires the image and runs the interface. The camera pins are fixed by the board; our I/O is OLED on D4 and D5, button on D1 and illumination on D0. The image goes to the companion by one HTTP POST over Wi-Fi. All of this is a proposed design; nothing was built.

## Slide 11: Wearable Camera: Verified vs Proposed

This slide separates what was actually done from what is proposed. Done: a literature and vendor-page search that fixed the board, camera and pin map; a short firmware (camera capture, LED, button, OLED, one HTTP POST) was compiled for the XIAO ESP32-S3 in the Wokwi build service and booted in the simulator; the camera probe fails there with not supported, as expected, because Wokwi has no camera part. The HTTP receiver on the companion was tested with a Python client. Not done: no physical board, no camera frame, no HTTP POST from the firmware, no button press or OLED screen verified in Wokwi, no round trip to the companion, no power measurement, no focus or field-of-view measurement. The laptop webcam is a separate implemented path, tested only with a test video, and is not evidence for the wearable camera.

## Slide 12: Proposed Wrist Unit: Electronics Layout

This is the proposed wrist unit, a design that was not built. One XIAO ESP32S3 Sense board carries the proposed camera module (OV5640 with autofocus, unconfirmed), which is the sensor, on its board-to-board connector. A white LED lights the hallmark through a transistor stage and is not a sensor. A button on D1 starts a capture and an OLED on D4 and D5 shows the result. The camera takes fixed pins; our I/O uses D0, D1, D4 and D5 and avoids GPIO3, a strapping pin. Nothing here is built or measured.

## Slide 13: Image Acquisition Workflow (Implemented)

This is the part that was missing and is now implemented: real image acquisition for the pipeline. There are two implemented software sources. First, a laptop webcam or USB camera through OpenCV, with live preview, camera selection, a capture button and error handling for no camera or a disconnect. Second, image upload, which matters because a normal webcam cannot resolve millimetre-high hallmarks. Both store the image on disk, validate it, show a preview with a retake option, and then use one function that reads the stored file back and runs the same pipeline. The proposed wrist camera and its HTTP sender are a design only. One honest limit: no physical webcam was available, so the webcam code was tested with a recorded test video.

## Slide 14: Application Demo: Webcam Path

These are real screenshots of the running application. In the left one the live preview shows the camera source, the frame was captured, saved and processed, and the result shows the transcription, calibrated probability against the threshold, both OCR readings, per-stage timings and the file hash. In the right one a glare frame was rejected with the hint 'Glare on mark: tilt wrist, lower LED'. Important: the camera source in these screenshots is a recorded test video of synthetic frames, because no camera was available in the environment. They demonstrate the software path, not a physical webcam or real jewellery.

## Slide 15: Application Demo: Image Upload and Errors

The upload path takes an image file, validates it and runs exactly the same pipeline. On the left the uploaded close-up was read and accepted. On the right a corrupt file is refused with a clear message and the Process button stays disabled. In the tests, a webcam frame and an uploaded file with identical pixels produced identical results, and the stored file's hash equals the uploaded bytes, which shows that the pipeline processes the actual input. The uploaded test image is a synthetic image saved as a file; no real jewellery photograph was processed.

## Slide 16: Software Application and Tests

The application is a Flask server with a browser interface. A camera manager runs the OpenCV capture in a thread and serves the preview; a capture store saves and validates every image; and one function reads the stored file back and calls the existing recognition pipeline unchanged. A wearable endpoint accepts a JPEG and returns a three-line text reply. Twenty-four automated tests pass, covering acquisition, the wearable endpoint and a headless-browser test of every control. The webcam tests use a recorded test video; no physical camera was tested.

## Slide 17: Wearable HTTP Interface

There is one exchange. The wrist unit POSTs the JPEG to slash api slash wearable slash upload. The companion stores the bytes, validates them, runs the same process-stored function as the webcam and upload paths, and replies in plain text with three lines: READ OK, RETAKE or NO MARK; the transcription or the hint; and the readability label. Bad images get a 400 or 422 reply starting with BAD IMAGE. There is no broker, no topics and no device state. What was tested: a Python client sending JPEG bytes; the reply equals a direct pipeline call, the stored file is byte-identical, and bad bodies are rejected. What was not tested: the camera, the firmware POST and any real Wi-Fi link.

## Slide 18: Communication Architecture and Test Status

This diagram shows the one HTTP request from the wrist unit to the companion and states the status of each acquisition source. The laptop webcam feeds the pipeline and was tested only with a test video. Image upload is implemented and tested. The wearable camera is a proposal: the HTTP receiver was tested with a Python client, but the ESP32 sender and the camera were never built or run. I do not claim the wearable path is integrated.

## Slide 19: Wokwi Project Circuit

This is the circuit of the Wokwi project in the hardware folder: the XIAO ESP32-S3 board, an SSD1306 OLED on D4 and D5, the capture button on D1 to ground, and the white LED on D0 through a 220 ohm resistor. It was redrawn from the project's diagram dot json file; it is not a screenshot of the Wokwi site, which could not be opened when the figure was made. Wokwi has no camera part, so the camera is not simulated. The transistor LED driver of the proposed design is also not in Wokwi, where a resistor drive stands in for it.

## Slide 20: Wokwi Firmware Check (No Camera)

This is a real screenshot of the serial output from the Wokwi simulator. The wrist firmware, about eighty lines, was loaded on Wokwi's XIAO ESP32-S3 board with an OLED, a button and a white LED. It compiled and booted. The camera probe fails with not supported, because Wokwi has no camera part, and the firmware reports camera init failed. That is the expected result and it is the only thing this run shows. The button press, the OLED screens, the Wi-Fi connection of this firmware, the HTTP POST and any round trip to the companion were not verified. The earlier Wokwi projects that used a messaging protocol were removed.

## Slide 21: Dataset (100 % synthetic)

1440 procedurally generated images from 240 fictitious inscriptions. Split by item: 144, 48, 48 items. Per-factor labels come from the generator parameters, and the readability label is a generator-defined proxy, not human judgement. These images are not photographs of real jewellery.

## Slide 22: Companion Pipeline and Model Roles

The companion runs the existing pipeline unchanged. Validation and resize, image-quality assessment with 21 features, contour-based localisation and ROI extraction. Then two OCR engines in parallel: RapidOCR on the raw grayscale ROI is the primary reading and Tesseract on the red channel is the secondary. OCR-uncertainty features feed an ExtraTrees rejector with isotonic calibration, compared with a threshold tau; a Random Forest on quality features gives the readability class; Gradient Boosting is the compared alternative and is not deployed; and rule-based guidance explains rejections.

## Slide 23: OCR and ML Workflow

Which model does what. Two OCR engines read the ROI. Their confidences, lengths and disagreement form OCR-uncertainty features, which are combined with the 21 quality features. A Random Forest on the quality features predicts the readability class, with Gradient Boosting as a compared alternative. An ExtraTrees base model on quality plus OCR uncertainty is calibrated with isotonic regression on out-of-fold scores, giving the probability p that the transcription is correct; the system accepts when p is at least the Clopper-Pearson upper-bound threshold. All models were trained on the 1440 synthetic images with an item-level split.

## Slide 24: Image-Processing Pipeline

Localisation uses the horizontal anisotropy of brushed metal: gradient energy then blob merging. It reaches IoU at least 0.5 on about three quarters of test images in six milliseconds, versus the PP-OCR detector at 133 milliseconds. Enhancement stages were ablated: they did not help.

## Slide 25: OCR Methodology

Two engines, neither fine-tuned. RapidOCR on the raw ROI reaches exact match 0.510; Tesseract 0.188. RapidOCR often drops spaces, so strict exact is much lower and WER is not meaningful; our primary metric ignores whitespace. Classical enhancement lowered accuracy.

## Slide 26: Readability Classification

Seven classifiers compared by grouped cross-validation over development items; test used once. Quality-only random forest: accuracy 0.830, macro-F1 0.804. Adding OCR uncertainty gives 0.826, a difference within cross-validation spread. The label is the generator's proxy.

## Slide 27: Confidence-Based Rejection and Recapture

Separated rejector: a base model is selected by grouped out-of-fold AURC, then isotonic-calibrated on out-of-fold scores. Thresholds are chosen on development data, empirically or with a Clopper-Pearson bound. When a capture is rejected, the largest standardised quality deficit selects the hint.

## Slide 28: Original Simulator (Synthetic Camera)

This is the original browser simulator, kept for the controlled demonstrations. Python, OpenCV, scikit-learn, Tesseract, RapidOCR ONNX, Flask. The simulator exposes a capture endpoint that renders a synthetic image under a chosen condition and runs the real pipeline, plus an upload endpoint. The OLED, LED and camera in the browser simulator are simulated and labelled as such. The companion application wraps the same analyse_image function.

## Slide 29: Experimental Methodology

Development equals train plus validation items. Model selection, calibration and thresholds use development data only, with grouped cross-validation by item. The test split, 48 items and 288 images, is evaluated once. Uncertainty is quantified with an item-level cluster bootstrap. We also run leave-one-source-out.

## Slide 30: Results: OCR by Condition

RapidOCR exact 0.510, Tesseract 0.188 overall. Accuracy falls with glare, occlusion and combined degradations; severity sweeps show graceful decline under blur and lighting and collapse at extreme levels.

## Slide 31: Results: Rejection

Raw OCR confidence has AURC 0.274 and ECE 0.144. The learned OCR-uncertainty rejector has AURC 0.181; the paired difference excludes zero. Adding quality features does not change AURC measurably. Quality alone is not significantly better than raw confidence.

## Slide 32: Results: Thresholds, Guidance, System

Dev-selected thresholds do not transfer exactly: S5 at a 5 percent target accepted 87 with 5 errors. Guidance top-1 hit rate 0.674 versus 0.185 random. Latency is on a sandbox CPU, not a Pi. Peak memory 176 MB.

## Slide 33: Discussion

Three findings. A learned OCR-uncertainty score, especially engine disagreement, rejects errors far better than raw confidence. Quality features add nothing measurable to rejection here, probably because OCR outputs already summarise degradation; their value is explanatory. Classical enhancement did not help modern recognisers.

## Slide 34: Limitations

Be explicit: synthetic data only; proxy labels from generator parameters; small test split; off-the-shelf engines; no user study; no hardware built; wearable camera never run (not simulable in Wokwi); device-to-companion link never run; latency measured on another CPU; and the development process looked at dev results while refining the generator.

## Slide 35: Conclusion and Future Work

A calibrated rejector on OCR-uncertainty features substantially improves reliability over raw confidence in this simulation; quality features support explainable hints but did not improve rejection. Next step: real photographs with provenance, fine-tuning, a built wrist unit with the macro camera, and a firmware-to-companion link that sends a real captured frame.

## Slide 36: References

These are the twenty references cited in the paper, in the paper's numbering; full entries are in the paper. Each was checked against its page.
