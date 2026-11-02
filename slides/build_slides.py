import os, sys, json, re
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from PIL import Image
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "literature")); import refs
T = lambda n: pd.read_csv(os.path.join(ROOT, "results", "tables", n + ".csv"))
F = lambda n: os.path.join(ROOT, "figures", n); D = lambda n: os.path.join(ROOT, "diagrams", n)
NAVY, ACC, GREY, RED = RGBColor(0x1F,0x3A,0x5F), RGBColor(0x2F,0x7D,0x6D), RGBColor(0x55,0x55,0x55), RGBColor(0xB0,0x30,0x30)
prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]
NOTES = []
_ORDER = json.load(open(os.path.join(ROOT, "paper", "cite_order.json")))
_ORDER = _ORDER + [r["n"] for r in refs.REFS if r["n"] not in _ORDER]   # paper numbering first, remaining references after
def C(t):
    """Renumber [n] citations to the paper's IEEE (first-appearance) order."""
    return re.sub(r"\[(\d{1,2})\](?!\s*\w)" if False else r"\[(\d{1,2})\]", lambda m: f"[{_ORDER.index(int(m.group(1))) + 1}]", t)

def slide(title, notes, banner=None):
    s = prs.slides.add_slide(blank)
    bar = s.shapes.add_shape(1, 0, 0, prs.slide_width, Inches(0.95)); bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
    tb = s.shapes.add_textbox(Inches(0.5), Inches(0.15), Inches(12.3), Inches(0.7)); p = tb.text_frame.paragraphs[0]
    r = p.add_run(); r.text = title; r.font.size = Pt(28); r.font.bold = True; r.font.color.rgb = RGBColor(255,255,255)
    ft = s.shapes.add_textbox(Inches(0.5), Inches(7.05), Inches(12.3), Inches(0.35)).text_frame.paragraphs[0]
    r = ft.add_run(); r.text = "Simulation-based study on SYNTHETIC data | no physical wearable built | reads characters only: no authenticity/purity claims"; r.font.size = Pt(10); r.font.color.rgb = GREY
    nb = s.shapes.add_textbox(Inches(12.2), Inches(7.05), Inches(0.9), Inches(0.35)).text_frame.paragraphs[0]; nb.alignment = PP_ALIGN.RIGHT
    r = nb.add_run(); r.text = str(len(prs.slides)); r.font.size = Pt(11); r.font.color.rgb = GREY
    notes = C(notes); s.notes_slide.notes_text_frame.text = notes; NOTES.append((title, notes))
    return s

def bullets(s, items, x=0.6, y=1.2, w=12, h=5.5, size=20):
    tf = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)).text_frame; tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        sub = it.startswith("  "); r = p.add_run(); r.text = ("– " if sub else "• ") + C(it.strip()); r.font.size = Pt(size - 4 if sub else size)
        p.level = 1 if sub else 0; p.space_after = Pt(8)
    return tf

def pic(s, path, x, y, w=None, h=None):
    im = Image.open(path); ar = im.width / im.height
    if w and h:
        if w / h > ar: w = h * ar
        else: h = w / ar
    elif w: h = w / ar
    else: w = h * ar
    s.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))

def cap(s, text, x, y, w, size=12, color=GREY):
    tf = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(0.5)).text_frame; tf.word_wrap = True
    r = tf.paragraphs[0].add_run(); r.text = text; r.font.size = Pt(size); r.font.color.rgb = color; r.font.italic = True

def table(s, df, x, y, w, size=11):
    t = s.shapes.add_table(len(df) + 1, len(df.columns), Inches(x), Inches(y), Inches(w), Inches(0.3 * (len(df) + 1))).table
    for j, c in enumerate(df.columns):
        t.cell(0, j).text = str(c).replace("_", " ")
    for i, (_, row) in enumerate(df.iterrows(), 1):
        for j, v in enumerate(row):
            t.cell(i, j).text = ("-" if pd.isna(v) else f"{v:.3f}") if isinstance(v, float) else str(v)
    for r in t.rows:
        for c in r.cells:
            for p in c.text_frame.paragraphs:
                for rn in p.runs: rn.font.size = Pt(size)

t2 = T("T2_ocr_baseline_and_preprocessing"); t7 = T("T7_rejection_aurc"); t7b = T("T7b_paired_delta_aurc"); t6 = T("T6_readability_test"); t13 = T("T13_guidance"); t11 = T("T11_latency_stages"); t12 = T("T12_memory_and_sizes"); t10 = T("T10_localisation"); t9 = T("T9_generalisation_leave_one_source_out"); t8 = T("T8_rejection_operating_points")
g = lambda df, col, **kw: df[(df[list(kw)] == pd.Series(kw)).all(axis=1)].iloc[0][col]
rap = g(t2, "test_exact", engine="rapidocr", input="detected ROI, raw"); tes = g(t2, "test_exact", engine="tesseract", input="detected ROI, raw")
S = {r["strategy"][:2]: r for _, r in t7.iterrows()}; mem = {r["item"]: r["value_mb"] for _, r in t12.iterrows()}; lat = {r["stage"]: r for _, r in t11.iterrows()}; gd = t13.iloc[0]

# 1 title
s = slide("Wearable Computing Course Project", "Welcome. This project is a simulation-based study of a wrist-worn assistant that reads a hallmark inscription, estimates how trustworthy its own reading is, and tells the wearer how to retake a bad capture. Two disclosures up front: no hardware was built, and all images are synthetic. And it reads characters only; it never claims authenticity or purity.")
def _t(txt, y, size, bold=False, color=NAVY, h=0.6):
    tf = s.shapes.add_textbox(Inches(0.6), Inches(y), Inches(12.1), Inches(h)).text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; r = p.add_run(); r.text = txt; r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color
_t("Design of a Smart Wearable System for Gold Jewellery Hallmark Recognition and Readability Assessment", 1.2, 30, True, h=1.5)
_t("Wearable Computing (BCSE315L) course project", 2.95, 18, False, GREY)
_t("Priyanka Lingesan, Riddhi Solanki, Pranathi Kaparthi, Krishnaraj N", 3.7, 22, True, RGBColor(0x22,0x22,0x22))
_t("Vellore Institute of Technology, Vellore, India", 4.3, 18, False, GREY)
cap(s, "SIMULATION ONLY: no physical prototype | SYNTHETIC hallmark-style inscriptions | reads characters; NOT a purity, authenticity or BIS-certification check", 0.6, 5.5, 12.1, 16, RED)
# 2
s = slide("Introduction and Motivation", "Hallmarks are small and low contrast. OCR engines return a confident string even when it is wrong, so a silent misread costs more than a retake. A wrist camera keeps both hands free and sees held objects at a useful scale (Ohnishi et al.), and finger-worn readers show that feedback on alignment and focus helps capture (FingerReader).")
bullets(s, ["Gold jewellery carries small hallmark-style inscriptions: engraved / stamped / embossed / laser-marked", "Hard to read by eye: tiny, low contrast, worn, glare", "Failure mode: confident but wrong OCR output; a silent misread costs more than a retake", "Wrist camera: hands free, close-up view [2]; feedback helps capture [3]", "Reading a mark is NOT verifying gold purity, authenticity or BIS certification", "Design target: transcription RELIABILITY, not only accuracy"], size=19)
# 3
s = slide("Problem Statement", "Formally: given a frame we output a transcription, a calibrated score and a decision. Correct means whitespace-insensitive exact match. The score should estimate the probability the transcription is right, and the threshold is chosen for a target accepted-error rate. Explicitly out of scope: purity, authenticity, standards compliance.")
bullets(s, ["Input: frame x with a hallmark-style inscription y (unknown to the system)", "Output: transcription ŷ, calibrated score p(x), decision", "  ACCEPT if p(x) ≥ τ  |  RETAKE + hint  |  NO MARK", "Correct: c = 1[ŷ = y] (whitespace-insensitive exact match)", "Goal: keep accepted-error rate below a target at useful coverage", "Out of scope: authenticity, purity, BIS certification, hallmark-standard compliance"])
# 4
s = slide("Objectives", "Nine objectives, O1 to O9; O7 to O9 are the wearable interface, electronics and image acquisition. The central research question is O3: does combining image-quality assessment with OCR uncertainty reduce incorrectly accepted transcriptions compared to raw OCR confidence?")
bullets(s, ["O1  Reproducible, labelled SYNTHETIC benchmark, item-level split", "O2  Benchmark OCR engines and preprocessing", "O3  Does quality + OCR-uncertainty beat raw OCR confidence?", "O4  Calibrated, risk-targeted acceptance; measure threshold transfer", "O5  Recapture guidance evaluated against known causes", "O6  Simulator that runs the REAL pipeline", "O7  Wrist unit <-> companion interface: one HTTP POST, receiver tested", "O8  Wrist electronics + camera/illumination design; firmware compiled and booted in Wokwi (no camera there)", "O9  Image acquisition: OpenCV webcam + image upload feeding the pipeline"])
# 5
s = slide("Literature Review (verified sources only)", "The paper cites twenty verified sources, including three hardware and simulator documentation pages for the wearable design. Closest to our task: goldsmith's-mark retrieval in silverware, which identifies marks by retrieval rather than reading characters. For OCR: Tesseract and PP-OCR. For confidence: calibration, maximum-probability baselines, scene-text calibration. Selective prediction: Chow, El-Yaniv, Geifman. Quality: no-reference gradient and contrast statistics. No peer-reviewed work on OCR of engraved hallmarks was found in our bounded search.")
bullets(s, ["Mark analysis: goldsmith's-mark retrieval in silverware [1]", "OCR: Tesseract [4], PP-OCR [5]; scene-text surveys [6][7]", "Confidence: over-confident networks [9], MSP baseline [10], scene-text calibration [8]", "Selective prediction: Chow [13], El-Yaniv [12], Geifman [11], survey [14]", "Image quality: no-reference gradient and contrast statistics [15][18]", "No verified peer-reviewed work on OCR of engraved hallmarks found"], size=19)
# 6
s = slide("Research Gap and Contribution", "The gap is a combination: quality assessment, OCR uncertainty, calibrated abstention, and recapture advice for engraved inscriptions on a wearable. This is a statement about our bounded search, not proof of absence; we claim no novelty beyond this combination.")
bullets(s, ["Gap: no verified work combining quality + OCR uncertainty + calibrated abstention + recapture advice for engraved text", "Contributions:", "  Synthetic generator with per-factor labels", "  OCR benchmark + preprocessing ablation", "  Calibrated separated rejector with risk-controlled thresholds", "  Rule-based recapture guidance, evaluated on known causes", "  Simulator running the real pipeline", "  Acquisition app: webcam (OpenCV) + upload -> same pipeline", "  Wrist camera + companion design, one-request HTTP interface, Wokwi firmware check", "Novelty not claimed beyond this combination"], size=19)
# 7 concept
s = slide("Wearable Concept: Wrist Camera + Companion", "The system has two parts. The wrist unit is one Seeed XIAO ESP32S3 Sense board with its proposed camera module (OV5640 with autofocus, unconfirmed until a kit is received) as the primary sensor, a white LED for illumination, a push button and a small OLED. The companion is a laptop running the Python pipeline, which does all recognition. When the button is pressed the unit lights the LED, captures a JPEG, sends it in one HTTP POST over Wi-Fi and shows the three-line text reply. Be clear about status: the physical design is proposed and was not built; the Python pipeline and the HTTP receiver are implemented; the firmware was only compiled and booted in Wokwi, which has no camera part; and the receiver was tested with a Python client, not with the device.")
bullets(s, ["Wrist unit: XIAO ESP32S3 Sense + proposed camera module (OV5640 AF, unconfirmed; primary sensor), white LED (illumination only), button, OLED", "Companion laptop: Python pipeline does ALL recognition (quality, localisation, 2 OCR engines, readability, rejection, guidance)", "Link: one HTTP POST of the JPEG over Wi-Fi; 3-line text reply shown on the OLED", "Status labels used throughout:", "  PROPOSED design: physical wrist unit, camera, LED driver (not built)", "  IMPLEMENTED: Python pipeline + HTTP receiver (synthetic images)", "  SIMULATED: firmware compile + boot in Wokwi (NO camera part exists)", "  TESTED: HTTP receiver with a Python client only"], size=18)
# 8 architecture
s = slide("System Architecture", "Read the figure by section. Section A, the proposed wrist unit: the LED lights the hallmark, the proposed camera module (OV5640 with autofocus, unconfirmed) on the XIAO ESP32S3 Sense is the sensor, the same board sends the JPEG in one HTTP POST over Wi-Fi. Section B, the companion, which is implemented: acquisition, quality assessment, localisation, parallel OCR with RapidOCR and Tesseract, OCR uncertainty with the Random Forest readability class, calibrated rejection with ExtraTrees and isotonic calibration, and result plus guidance. The reply comes back in the same HTTP response as three lines of text and the board shows it on its OLED. The wrist block is proposed and not built.")
pic(s, D("architecture_integrated.png"), 0.6, 1.1, w=5.4)
bullets(s, ["Camera = primary sensor; LED = illumination only", "Recognition runs only on the companion laptop", "Wearable: one HTTP POST, 3-line text reply", "Wrist unit = PROPOSED, not built"], x=6.6, y=1.5, w=6.3, size=18)
# 9 camera
s = slide("Camera and Illumination Design", "We compared the XIAO ESP32S3 Sense, the AI-Thinker ESP32-CAM, the ESP32 DevKit-C V4 with a camera breakout, the Raspberry Pi camera and a USB macro camera. The XIAO ESP32S3 Sense is selected: the camera sits on the board-to-board connector and the board has eight megabytes of PSRAM and headers for the OLED, button and drivers. The proposed camera is the OV5640 autofocus module the vendor lists for the Sense, but the vendor also says boards may ship with an OV5640 or an OV3660, and older pages describe an OV2640, so the fitted module is unconfirmed. No field of view or focus range is listed, so the figures on this slide are an illustrative placeholder taken from the OV2640 Arducam page, not OV5640 values: about 23 millimetres field of view at 30 millimetres, about 68 pixels per millimetre. All optical values must be measured on the delivered module. A USB macro camera on the companion is the fallback. Wokwi cannot simulate a camera, so this is a drawing and the experiments use synthetic images.")
pic(s, D("camera_sensing_schematic_slide.png"), 0.3, 1.15, w=9.3); bullets(s, ["Proposed: XIAO ESP32S3 Sense + OV5640 AF; vendor says OV5640 or OV3660 may ship, so UNCONFIRMED [25]", "FOV and focus range: not listed by vendor", "Placeholder estimate from OV2640 [23], NOT OV5640 values: ~23 mm FOV, ~68 px/mm at 30 mm", "Illumination LED: D0/GPIO1 via NPN stage (not the sensor)", "Fallback: USB macro camera on the laptop", "NOT simulated in Wokwi; NOT built"], x=9.7, y=1.3, w=3.5, size=14)
# 9a architecture decision + verification
s = slide("Wearable Camera: Architecture Decision", "The earlier circuit had no camera, which was a gap. A DVP camera needs fourteen signals: eight data lines, the clock, pixel clock, vertical and horizontal sync, and two for the camera I2C bus. A DevKit-C V4 is not a camera board and would have little I/O left, and we did not verify that its module has the PSRAM that large JPEG frames need. The AI-Thinker ESP32-CAM leaves only six GPIOs free, each shared with the microSD socket or the flash LED, has no USB port and wants a five volt supply of at least two amps, so it cannot also run an OLED, a button and an LED driver. The XIAO ESP32S3 Sense carries the ESP32-S3 and the camera on one small board, so one board both acquires the image and runs the interface. The camera pins are fixed by the board; our I/O is OLED on D4 and D5, button on D1 and illumination on D0. The image goes to the companion by one HTTP POST over Wi-Fi. All of this is a proposed design; nothing was built.")
_rows = pd.DataFrame([["Camera (proposed OV5640 AF, unconfirmed)", "board-to-board connector; no external wiring", "NOT TESTED"],
 ["SSD1306 OLED", "D4 = SDA (GPIO5), D5 = SCL (GPIO6), 3V3, GND", "boot only in Wokwi"],
 ["CAPTURE button", "D1 (GPIO2) to GND, internal pull-up", "boot only in Wokwi"],
 ["White LED stage", "D0 (GPIO1) -> 1 k -> NPN base; LED + resistor from 5 V", "PROPOSED"],
 ["Power", "USB-C 5 V (power bank); no battery design", "PROPOSED"],
 ["Link", "Wi-Fi 2.4 GHz, one HTTP POST to /api/wearable/upload", "receiver tested (Python client)"]], columns=["Part", "Connection", "Status"])
table(s, _rows, 0.4, 1.2, 12.5, 14)
bullets(s, ["Why not DevKit-C V4: 14 DVP signals, no camera connector, PSRAM unverified", "Why not ESP32-CAM: only 6 spare GPIOs, shared with SD/flash LED [26]", "Selected: XIAO ESP32S3 Sense, 8 MB PSRAM, single board [25]", "Whole unit is PROPOSED, NOT BUILT, NOT TESTED; the full wiring diagram is Fig. 2 of the paper"], x=0.5, y=4.9, w=12.3, size=16)
s = slide("Wearable Camera: Verified vs Proposed", "This slide separates what was actually done from what is proposed. Done: a literature and vendor-page search that fixed the board, camera and pin map; a short firmware (camera capture, LED, button, OLED, one HTTP POST) was compiled for the XIAO ESP32-S3 in the Wokwi build service and booted in the simulator; the camera probe fails there with not supported, as expected, because Wokwi has no camera part. The HTTP receiver on the companion was tested with a Python client. Not done: no physical board, no camera frame, no HTTP POST from the firmware, no button press or OLED screen verified in Wokwi, no round trip to the companion, no power measurement, no focus or field-of-view measurement. The laptop webcam is a separate implemented path, tested only with a test video, and is not evidence for the wearable camera.")
bullets(s, ["DONE: board/camera/pin selection from vendor docs [25]", "SIMULATED: firmware compiles for XIAO ESP32-S3 and boots in Wokwi", "EXPECTED FAILURE: camera probe 0x106 (Wokwi has no camera part [27])", "TESTED (companion side): HTTP receiver, Python client", "NOT DONE: hardware, camera frame, firmware POST, round trip, power, optics", "Laptop webcam = separate path; NOT evidence of wearable integration"], size=18)
# 9b wrist layout
s = slide("Proposed Wrist Unit: Electronics Layout", "This is the proposed wrist unit, a design that was not built. One XIAO ESP32S3 Sense board carries the proposed camera module (OV5640 with autofocus, unconfirmed), which is the sensor, on its board-to-board connector. A white LED lights the hallmark through a transistor stage and is not a sensor. A button on D1 starts a capture and an OLED on D4 and D5 shows the result. The camera takes fixed pins; our I/O uses D0, D1, D4 and D5 and avoids GPIO3, a strapping pin. Nothing here is built or measured.")
pic(s, D("wrist_unit_layout.png"), 0.4, 1.1, h=5.7); bullets(s, ["Camera = primary sensor (proposed OV5640 AF module; unconfirmed)", "White LED = illumination only (NPN stage, 5 V)", "OLED D4/D5, button D1, LED D0", "Board runs capture + UI + comms; NO OCR", "PROPOSED: not built; Wokwi mirrors only button, LED, OLED"], x=9.2, y=1.5, w=4.0, size=15)
# 9c acquisition workflow
s = slide("Image Acquisition Workflow (Implemented)", "This is the part that was missing and is now implemented: real image acquisition for the pipeline. There are two implemented software sources. First, a laptop webcam or USB camera through OpenCV, with live preview, camera selection, a capture button and error handling for no camera or a disconnect. Second, image upload, which matters because a normal webcam cannot resolve millimetre-high hallmarks. Both store the image on disk, validate it, show a preview with a retake option, and then use one function that reads the stored file back and runs the same pipeline. The proposed wrist camera and its HTTP sender are a design only. One honest limit: no physical webcam was available, so the webcam code was tested with a recorded test video.")
pic(s, D("acquisition_workflow.png"), 0.4, 1.05, h=5.9); bullets(s, ["Webcam (OpenCV): preview, capture, errors", "Upload: PNG/JPEG/BMP/WebP/TIFF", "Validate -> preview -> Retake / Process", "ONE entry point: process_stored()", "Webcam tested with a TEST VIDEO only (no camera in the sandbox)"], x=8.6, y=1.5, w=4.6, size=15)
# 9d screenshots: webcam path
s = slide("Application Demo: Webcam Path", "These are real screenshots of the running application. In the left one the live preview shows the camera source, the frame was captured, saved and processed, and the result shows the transcription, calibrated probability against the threshold, both OCR readings, per-stage timings and the file hash. In the right one a glare frame was rejected with the hint 'Glare on mark: tilt wrist, lower LED'. Important: the camera source in these screenshots is a recorded test video of synthetic frames, because no camera was available in the environment. They demonstrate the software path, not a physical webcam or real jewellery.")
pic(s, F("fig_app_screenshots.png"), 0.4, 1.3, w=12.5)
cap(s, "Real screenshots (headless Chromium). Camera source = recorded TEST VIDEO of synthetic frames; no physical webcam. (a) accepted; (b) RETAKE.", 0.4, 6.6, 12.5, 12, RED)
# 9e upload
s = slide("Application Demo: Image Upload and Errors", "The upload path takes an image file, validates it and runs exactly the same pipeline. On the left the uploaded close-up was read and accepted. On the right a corrupt file is refused with a clear message and the Process button stays disabled. In the tests, a webcam frame and an uploaded file with identical pixels produced identical results, and the stored file's hash equals the uploaded bytes, which shows that the pipeline processes the actual input. The uploaded test image is a synthetic image saved as a file; no real jewellery photograph was processed.")
pic(s, F("fig_app_upload.png"), 0.3, 1.2, w=7.2); pic(s, F("fig_app_upload_error.png"), 7.7, 1.2, w=5.3)
cap(s, "Real screenshots. Left: upload result (SYNTHETIC test image, not a jewellery photograph). Right: corrupt upload refused.", 0.4, 6.6, 12.5, 12, RED)
# 9f app architecture + tests
s = slide("Software Application and Tests", "The application is a Flask server with a browser interface. A camera manager runs the OpenCV capture in a thread and serves the preview; a capture store saves and validates every image; and one function reads the stored file back and calls the existing recognition pipeline unchanged. A wearable endpoint accepts a JPEG and returns a three-line text reply. Twenty-four automated tests pass, covering acquisition, the wearable endpoint and a headless-browser test of every control. The webcam tests use a recorded test video; no physical camera was tested.")
pic(s, D("software_app_architecture.png"), 0.4, 1.15, w=8.0); bullets(s, ["27 automated tests pass", "Webcam rows use a TEST VIDEO, not a camera", "Same pixels via webcam or upload -> identical result", "Corrupt / blank / tiny / unsupported files refused", "Disconnect detected; capture refused", "Every control clicked in headless Chromium"], x=8.6, y=1.3, w=4.6, size=14)
# 10 comms
s = slide("Wearable HTTP Interface", "There is one exchange. The wrist unit POSTs the JPEG to slash api slash wearable slash upload. The companion stores the bytes, validates them, runs the same process-stored function as the webcam and upload paths, and replies in plain text with three lines: READ OK, RETAKE or NO MARK; the transcription or the hint; and the readability label. Bad images get a 400 or 422 reply starting with BAD IMAGE. There is no broker, no topics and no device state. What was tested: a Python client sending JPEG bytes; the reply equals a direct pipeline call, the stored file is byte-identical, and bad bodies are rejected. What was not tested: the camera, the firmware POST and any real Wi-Fi link.")
bullets(s, ["POST /api/wearable/upload, body = JPEG, Content-Type image/jpeg", "Reply (text, 3 lines): READ OK | RETAKE | NO MARK", "  line 2: transcription (READ OK) or recapture hint", "  line 3: readability label", "Bad body: 400/422, first line BAD IMAGE; error: 500, first line ERROR", "Same process_stored() entry point as webcam and upload", "TESTED: Python client (4 automated tests); no hardware", "NOT tested: camera capture, firmware POST, Wi-Fi; plain HTTP, no TLS/authentication"], size=17)
# 10b comm architecture
s = slide("Communication Architecture and Test Status", "This diagram shows the one HTTP request from the wrist unit to the companion and states the status of each acquisition source. The laptop webcam feeds the pipeline and was tested only with a test video. Image upload is implemented and tested. The wearable camera is a proposal: the HTTP receiver was tested with a Python client, but the ESP32 sender and the camera were never built or run. I do not claim the wearable path is integrated.")
pic(s, D("comm_architecture.png"), 0.4, 1.1, w=9.4); bullets(s, ["One HTTP POST over Wi-Fi", "Webcam: implemented; test video only", "Upload: implemented and tested", "Wearable camera: NOT built/tested", "Receiver tested with Python client"], x=10.0, y=1.4, w=3.1, size=14)
# 10b2 wokwi circuit
s = slide("Wokwi Project Circuit", "This is the circuit of the Wokwi project in the hardware folder: the XIAO ESP32-S3 board, an SSD1306 OLED on D4 and D5, the capture button on D1 to ground, and the white LED on D0 through a 220 ohm resistor. It was redrawn from the project's diagram dot json file; it is not a screenshot of the Wokwi site, which could not be opened when the figure was made. Wokwi has no camera part, so the camera is not simulated. The transistor LED driver of the proposed design is also not in Wokwi, where a resistor drive stands in for it.")
pic(s, D("wokwi_circuit.png"), 0.4, 1.1, h=5.75); bullets(s, ["Parts: XIAO ESP32-S3, SSD1306 OLED, button, 220 Ω resistor, white LED", "OLED: D4 = SDA, D5 = SCL, 3V3, GND", "Button: D1 to GND (internal pull-up)", "LED: D0 via 220 Ω (Wokwi has no NPN part)", "Redrawn from diagram.json; NOT a Wokwi screenshot", "No camera part in Wokwi: camera NOT simulated"], x=9.0, y=1.3, w=4.1, size=14)
# 10c ESP32 feedback
s = slide("Wokwi Firmware Check (No Camera)", "This is a real screenshot of the serial output from the Wokwi simulator. The wrist firmware, about eighty lines, was loaded on Wokwi's XIAO ESP32-S3 board with an OLED, a button and a white LED. It compiled and booted. The camera probe fails with not supported, because Wokwi has no camera part, and the firmware reports camera init failed. That is the expected result and it is the only thing this run shows. The button press, the OLED screens, the Wi-Fi connection of this firmware, the HTTP POST and any round trip to the companion were not verified. The earlier Wokwi projects that used a messaging protocol were removed.")
pic(s, D("wokwi_xiao_run.jpg"), 0.6, 1.1, h=5.6)
bullets(s, ["Wokwi XIAO ESP32-S3 + SSD1306 OLED + button + LED", "Observed: compile, boot, camera probe fails (ESP_ERR_NOT_SUPPORTED)", "Expected: Wokwi has no camera part [27]", "NOT verified: button, OLED screens, Wi-Fi POST, any frame, round trip", "No claim that Wokwi tested the camera path"], x=6.4, y=1.4, w=6.7, size=17)
# 9
s = slide("Dataset (100 % synthetic)", "1440 procedurally generated images from 240 fictitious inscriptions. Split by item: 144, 48, 48 items. Per-factor labels come from the generator parameters, and the readability label is a generator-defined proxy, not human judgement. These images are not photographs of real jewellery.")
pic(s, F("fig_dataset_examples.png"), 0.4, 1.15, w=8.2); bullets(s, ["240 items × 6 acquisitions = 1440 images", "Split by ITEM: 144 / 48 / 48", "Designed to resemble gold-jewellery hallmark-style markings", "NOT real photographs; NOT official BIS samples", "Readability = generator-defined proxy", "Results = synthetic benchmark only"], x=8.8, y=1.3, w=4.3, size=16)
# 9g pipeline roles
s = slide("Companion Pipeline and Model Roles", "The companion runs the existing pipeline unchanged. Validation and resize, image-quality assessment with 21 features, contour-based localisation and ROI extraction. Then two OCR engines in parallel: RapidOCR on the raw grayscale ROI is the primary reading and Tesseract on the red channel is the secondary. OCR-uncertainty features feed an ExtraTrees rejector with isotonic calibration, compared with a threshold tau; a Random Forest on quality features gives the readability class; Gradient Boosting is the compared alternative and is not deployed; and rule-based guidance explains rejections.")
pic(s, D("companion_pipeline.png"), 0.4, 1.1, w=8.3); bullets(s, ["Primary OCR: RapidOCR (raw gray)", "Secondary OCR: Tesseract (red channel)", "Rejector: ExtraTrees + isotonic calibration", "Readability: Random Forest on quality features", "Gradient Boosting: compared, NOT deployed", "Guidance: rule-based"], x=8.9, y=1.4, w=4.3, size=15)
s = slide("OCR and ML Workflow", "Which model does what. Two OCR engines read the ROI. Their confidences, lengths and disagreement form OCR-uncertainty features, which are combined with the 21 quality features. A Random Forest on the quality features predicts the readability class, with Gradient Boosting as a compared alternative. An ExtraTrees base model on quality plus OCR uncertainty is calibrated with isotonic regression on out-of-fold scores, giving the probability p that the transcription is correct; the system accepts when p is at least the Clopper-Pearson upper-bound threshold. All models were trained on the 1440 synthetic images with an item-level split.")
pic(s, D("ocr_ml_workflow.png"), 1.2, 1.1, h=5.8)
# 10
s = slide("Image-Processing Pipeline", "Localisation uses the horizontal anisotropy of brushed metal: gradient energy then blob merging. It reaches IoU at least 0.5 on about three quarters of test images in six milliseconds, versus the PP-OCR detector at 133 milliseconds. Enhancement stages were ablated: they did not help.")
pic(s, D("d06_localise_enhance_slide.png"), 0.4, 1.2, w=7.8, h=5.6); table(s, t10[["method", "iou_ge_0_5", "latency_ms_median"]], 8.4, 1.5, 4.5, 12); cap(s, "Localisation (test). full = full-frame baseline", 8.4, 3.4, 4.5)
# 11
s = slide("OCR Methodology", f"Two engines, neither fine-tuned. RapidOCR on the raw ROI reaches exact match {rap:.3f}; Tesseract {tes:.3f}. RapidOCR often drops spaces, so strict exact is much lower and WER is not meaningful; our primary metric ignores whitespace. Classical enhancement lowered accuracy.")
table(s, t2[["engine", "input", "test_CER", "test_exact"]], 0.6, 1.3, 7.2, 11); pic(s, F("fig_ablation.png"), 8.0, 1.3, w=5.0)
cap(s, "Ablation: enhancement stages did not help these engines (negative result, synthetic data).", 8.0, 4.4, 5)
# 12
s = slide("Readability Classification", f"Seven classifiers compared by grouped cross-validation over development items; test used once. Quality-only random forest: accuracy {t6.iloc[0]['accuracy']:.3f}, macro-F1 {t6.iloc[0]['f1_macro']:.3f}. Adding OCR uncertainty gives {t6.iloc[1]['f1_macro']:.3f}, a difference within cross-validation spread. The label is the generator's proxy.")
pic(s, F("fig_confusion_quality_only.png"), 0.6, 1.2, h=4.6); pic(s, F("fig_confusion_quality_ocr_unc.png"), 6.8, 1.2, h=4.6)
cap(s, "Test confusion matrices (rows: generator proxy label). Quality-only left; quality + OCR-uncertainty right.", 0.6, 6.0, 12)
# 13
s = slide("Confidence-Based Rejection and Recapture", "Separated rejector: a base model is selected by grouped out-of-fold AURC, then isotonic-calibrated on out-of-fold scores. Thresholds are chosen on development data, empirically or with a Clopper-Pearson bound. When a capture is rejected, the largest standardised quality deficit selects the hint.")
pic(s, D("d08_rejection_calibration_slide.png"), 0.4, 1.2, w=5.4, h=5.7); pic(s, D("d09_recapture_guidance_slide.png"), 6.0, 2.0, w=7.0, h=3.5)
# 14
s = slide("Original Simulator (Synthetic Camera)", "This is the original browser simulator, kept for the controlled demonstrations. Python, OpenCV, scikit-learn, Tesseract, RapidOCR ONNX, Flask. The simulator exposes a capture endpoint that renders a synthetic image under a chosen condition and runs the real pipeline, plus an upload endpoint. The OLED, LED and camera in the browser simulator are simulated and labelled as such. The companion application wraps the same analyse_image function.")
pic(s, D("d11_simulator_architecture_slide.png"), 0.4, 1.2, w=7.6, h=5.6); pic(s, os.path.join(ROOT, "figures", "oled_example.png"), 8.4, 1.3, w=4.4) if os.path.exists(os.path.join(ROOT, "figures", "oled_example.png")) else None
bullets(s, ["Simulated camera = synthetic renderer (not webcam)", "Real pipeline + saved models", "27 automated tests pass overall"], x=8.4, y=4.4, w=4.6, size=15)
# 15
s = slide("Experimental Methodology", "Development equals train plus validation items. Model selection, calibration and thresholds use development data only, with grouped cross-validation by item. The test split, 48 items and 288 images, is evaluated once. Uncertainty is quantified with an item-level cluster bootstrap. We also run leave-one-source-out.")
pic(s, D("d10_evaluation_design.png"), 0.4, 1.3, w=12.4)
# 16
s = slide("Results: OCR by Condition", f"RapidOCR exact {rap:.3f}, Tesseract {tes:.3f} overall. Accuracy falls with glare, occlusion and combined degradations; severity sweeps show graceful decline under blur and lighting and collapse at extreme levels.")
pic(s, F("fig_ocr_by_condition.png"), 0.4, 1.2, w=7.6); pic(s, F("fig_sweeps.png"), 8.1, 1.2, w=5.0)
# 17
s = slide("Results: Rejection", f"Raw OCR confidence has AURC {S['S1']['AURC']:.3f} and ECE {S['S1']['ECE']:.3f}. The learned OCR-uncertainty rejector has AURC {S['S3']['AURC']:.3f}; the paired difference excludes zero. Adding quality features does not change AURC measurably. Quality alone is not significantly better than raw confidence.")
pic(s, F("fig_risk_coverage_calibration.png"), 0.4, 1.15, w=7.6)
dd = t7b.copy(); dd["comparison"] = dd["comparison"].str.extract(r"^(S\d)")[0] + " vs " + dd["comparison"].str.extract(r"minus\s+(S\d)")[0]
table(s, dd[["comparison", "delta_AURC", "CI95"]], 8.2, 1.4, 4.8, 11); cap(s, "Paired ΔAURC (negative favours the first).", 8.2, 3.2, 4.8)
# 18
s = slide("Results: Thresholds, Guidance, System", f"Dev-selected thresholds do not transfer exactly: S5 at a 5 percent target accepted 87 with 5 errors. Guidance top-1 hit rate {gd['top1_hit_rate']:.3f} versus {gd['random_cause_hit_rate']:.3f} random. Latency is on a sandbox CPU, not a Pi. Peak memory {mem['peak RSS: full_dual']:.0f} MB.")
bullets(s, ["S5 @5 % target: 87 accepted, 5 errors (5.7 %); coverage 0.30", "Dev thresholds do not transfer exactly; 48 test items only", f"Guidance top-1 hit {gd['top1_hit_rate']:.3f} vs random {gd['random_cause_hit_rate']:.3f} (n={int(gd['n_rejected_with_flagged_factor'])})", f"Leave-one-source-out: learned rejector beats raw confidence on all 3 sources", f"Latency (sandbox CPU): median {lat['total_ms']['median_ms']:.0f} ms, p95 {lat['total_ms']['p95_ms']:.0f} ms", f"Peak RSS {mem['peak RSS: full_dual']:.0f} MB (not measured on Pi)"], size=19)
# 19
s = slide("Discussion", "Three findings. A learned OCR-uncertainty score, especially engine disagreement, rejects errors far better than raw confidence. Quality features add nothing measurable to rejection here, probably because OCR outputs already summarise degradation; their value is explanatory. Classical enhancement did not help modern recognisers.")
bullets(s, ["Learned OCR-uncertainty >> raw OCR confidence", "Quality features: no extra AURC gain here; they drive guidance", "Enhancement hurt RapidOCR (negative result)", "Threshold transfer is the practical weak point"])
# 20
s = slide("Limitations", "Be explicit: synthetic data only; proxy labels from generator parameters; small test split; off-the-shelf engines; no user study; no hardware built; wearable camera never run (not simulable in Wokwi); device-to-companion link never run; latency measured on another CPU; and the development process looked at dev results while refining the generator.")
bullets(s, ["Synthetic data only: no real gold jewellery imaged", "Labels defined from generator parameters", "Small test split (48 items): wide CIs", "Off-the-shelf OCR, no fine-tuning", "No hardware built; wearable camera never run; camera and transistor not simulable in Wokwi", "Device <-> companion link never run; HTTP receiver tested only with a Python client", "No user study; no Pi measurements", "Results do NOT establish real-jewellery performance"], size=19)
# 21
s = slide("Conclusion and Future Work", "A calibrated rejector on OCR-uncertainty features substantially improves reliability over raw confidence in this simulation; quality features support explainable hints but did not improve rejection. Next step: real photographs with provenance, fine-tuning, a built wrist unit with the macro camera, and a firmware-to-companion link that sends a real captured frame.")
bullets(s, ["On the synthetic benchmark: calibrated OCR-uncertainty rejector beats raw confidence (ΔAURC −0.09, CI excl. 0)", "Quality features → explainable recapture hints; no extra AURC", "Design: proposed wrist camera unit + implemented Python companion + one-request HTTP receiver tested with a Python client", "Future: real annotated photographs, fine-tuned recogniser, build the wrist unit, send a real frame from the device, authenticated link, user study"], size=19)
# 22
s = slide("References", "These are the twenty references cited in the paper, in the paper's numbering; full entries are in the paper. Each was checked against its page.")
_by = {r["n"]: r for r in refs.REFS}
_cited = json.load(open(os.path.join(ROOT, "paper", "cite_order.json")))
_lst = [f"[{i}] " + refs.ieee(_by[n]) for i, n in enumerate(_cited, 1)]
for _x, _items in ((0.35, _lst[:10]), (6.8, _lst[10:])):
    tf = s.shapes.add_textbox(Inches(_x), Inches(1.1), Inches(6.2), Inches(5.8)).text_frame; tf.word_wrap = True
    for _k, _it in enumerate(_items):
        _p = tf.paragraphs[0] if _k == 0 else tf.add_paragraph(); _r = _p.add_run(); _r.text = _it; _r.font.size = Pt(8.5); _p.space_after = Pt(4)
out = os.path.join(ROOT, "slides", "hallmark_wearable_slides.pptx"); prs.save(out); print(out, len(prs.slides))
json.dump(NOTES, open(os.path.join(ROOT, "slides", "notes.json"), "w"))
