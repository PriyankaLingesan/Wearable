# Viva questions and answers

**Q1. What exactly does the system do and not do?** It localises an inscription, transcribes it with two OCR engines, estimates the probability that the transcription is exactly right, and accepts or requests a retake with a hint. It does not determine authenticity, purity or composition.

**Q2. Was a wearable built?** No. The wrist unit (XIAO ESP32S3 Sense with its proposed camera module (OV5640 AF; the vendor says OV5640 or OV3660 may ship, so unconfirmed), white illumination LED, button, OLED) is a proposed design. The Python pipeline is real and was evaluated on synthetic images; Wokwi only compiled and booted the firmware (no camera part exists).

**Q3. Are the images real?** No, all 1440 are procedurally generated (`provenance=synthetic`).

**Q4. How did you avoid leakage?** Split by item: all six acquisitions of an inscription sit in one split (asserted in code); model selection used GroupKFold by item; the test split was used once.

**Q5. Why not use OCR confidence as probability?** Engine scores are not calibrated: raw confidence had ECE 0.144 and its reliability curve sat far above observed accuracy. We calibrate a learned score with isotonic regression on out-of-fold data [9], [8].

**Q6. What are AURC and E-AURC?** AURC is the mean selective risk over all coverages when accepting in order of score (lower is better); E-AURC subtracts the oracle ordering's AURC.

**Q7. Main result?** The learned OCR-uncertainty rejector (engine disagreement + confidences) lowers AURC from 0.274 to 0.181 with a paired CI excluding zero.

**Q8. Did image quality help rejection?** Not measurably (dAURC 0.000, CI -0.009..+0.010). It does power the hints and the readability classifier.

**Q9. Why did enhancement hurt?** Likely because modern recognisers are trained on natural images and the synthetic renderings have little noise to remove; enhancement (CLAHE, binarisation) introduced artefacts. This is a result on this data, not a general claim.

**Q10. Why two OCR engines?** Their disagreement is the strongest uncertainty signal; it also costs latency (Tesseract ~99 ms of ~264 ms).

**Q11. What is isotonic calibration and why out-of-fold?** A monotone mapping from score to empirical accuracy; out-of-fold scores avoid fitting the calibrator on predictions the base model memorised.

**Q12. How are thresholds chosen, and do they work?** From dev out-of-fold scores, empirically or with a Clopper-Pearson upper bound [11]; they transfer imperfectly (e.g., 5.7 % vs 5 % target) and are conservative at strict targets. With 48 test items a single error shifts rates noticeably.

**Q13. Why is WER odd for RapidOCR?** It drops spaces, so token-level comparison is unreliable; the primary metric is whitespace-insensitive exact match.

**Q14. How is guidance evaluated?** Against the generator's degradation labels among rejected captures with a flagged factor: top-1 hit 0.674 vs 0.185 for a random cause. It is not a user study.

**Q15. Which compute platform?** Design target is a Pi Zero 2 W-class wrist unit with companion offload; measured peak RSS ~176 MB on x86 (no Pi measurement). Latency on a Pi was not measured and is not extrapolated.

**Q16. Biggest threat to validity?** Synthetic data and generator-defined labels; also small test set. Real-photo validation is the next step.

**Q17. Novelty?** Not claimed beyond the specific combination of quality assessment, OCR uncertainty, calibrated abstention and recapture advice; our bounded search found no verified peer-reviewed work on the combination for engraved hallmarks, which is not proof of absence.

**Q18. What would you do next?** Real consented, provenance-tracked photographs; fine-tune recogniser; real wearable camera; user study of hints; conformal threshold control.

**Q19. Why is the camera not in Wokwi, and what stands in for it?** Wokwi cannot simulate a camera. The camera is documented in a separate schematic (FOV and px/mm are OV2640-based placeholder estimates; macro focus must be verified), and the experiments use synthetic images.

**Q20. What does the LED do?** It illuminates the hallmark (GPIO5, white LED, 220 ohm). It is not a sensor.

**Q21. Does the ESP32 do OCR?** No. It sends a capture request and displays the result the companion computed; with no reply it shows NO LINK / NO REPLY.

**Q22. Why plain HTTP, and not a messaging protocol?** One request carries the JPEG and the reply carries the three-line result, so nothing else is needed. No broker, topics or device state.

**Q23. Is the end-to-end system verified?** No. The HTTP receiver was tested with a Python client (reply equals a direct pipeline call; bad bodies rejected). The firmware was only compiled and booted in Wokwi; no hardware exists and the device never sent a request.

**Q24. How is the LED driven?** Proposed: GPIO -> 1 k -> NPN, LED + series resistor from 5 V, because a white LED's forward voltage is near 3.3 V. Wokwi has no transistor, so its project uses GPIO -> 220 ohm -> LED as a stand-in. Not built.

**Q25. How does a real image enter the system?** Through the OpenCV webcam path (preview, Capture button) or the upload path. Both store the file, validate it, and call one function (`process_stored`) that reads the stored file back and runs the pipeline.

**Q26. Was the webcam tested?** Only with a recorded test video through the same `cv2.VideoCapture` code; no physical camera was available. I do not claim a physical webcam test.

**Q27. How do you know the pipeline processes the actual input?** The result carries the SHA-256 of the processed file, which equals the hash of the uploaded bytes; different inputs give different outputs; identical pixels via either path give identical results; and results equal a direct call of `analyse_image` on the stored file.

**Q28. Why is a laptop webcam not enough?** Characters are 1 to 3 mm high; a fixed-focus webcam at typical distances gives only a few pixels per character. Hence the upload path and the proposed OV2640 macro camera.

**Q29. Did you test on real jewellery photographs?** No. Uploads in tests are synthetic images saved as files; real-photograph evaluation needs consented, provenance-tracked images and would be a new, separately reported experiment.


**Q30. Where is the camera in your hardware?** On the proposed wrist unit: a Seeed XIAO ESP32S3 Sense with its proposed camera module (OV5640 AF; the vendor says OV5640 or OV3660 may ship, so unconfirmed) on the board-to-board connector (pin map in `docs/camera_subsystem_verification.md`). Not built, never captured an image. Wokwi has no camera part.

**Q31. Why not the ESP32 DevKit-C V4 or an ESP32-CAM?** A DVP camera needs 14 signals; the DevKit-C has no camera connector and we did not verify PSRAM on it. The AI-Thinker ESP32-CAM has only six spare GPIOs, shared with microSD/flash LED, no USB and a 2 A 5 V supply advice (secondary source), too little for OLED, button, and LED driver. One XIAO ESP32S3 Sense does both jobs.

**Q32. Did you simulate the camera in Wokwi?** No. No camera part exists; camera init fails in the simulator (0x106) by design. What ran: compile, boot, the expected failure message.

**Q33. Is the laptop webcam proof the wearable camera works?** No. It is a separate Python path (OpenCV, tested only with a test video). The wearable camera, its firmware POST and its power/optics are untested.

**Q34. What did testing the wire sequence find?** The receiver answers HTTP 202; the first firmware draft accepted only 200 and would have shown a false upload failure. Fixed to any 2xx and covered by a test (a Python stand-in, not the firmware).
