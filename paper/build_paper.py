"""Builds the IEEE-style conference paper (DOCX) from results/tables and literature/refs.py. All numbers come from the generated tables."""
import os, sys, json, re
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "literature")); import refs
T = lambda n: pd.read_csv(os.path.join(ROOT, "results", "tables", n + ".csv"))
F = lambda n: os.path.join(ROOT, "figures", n)
D = lambda n: os.path.join(ROOT, "diagrams", n)

doc = Document()
st = doc.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(9.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
sec = doc.sections[0]; sec.page_width = Inches(8.5); sec.page_height = Inches(11)
sec.left_margin = sec.right_margin = Inches(0.75); sec.top_margin = Inches(0.8); sec.bottom_margin = Inches(0.8)

def cols(section, n):
    sp = section._sectPr; c = sp.find(qn("w:cols"))
    if c is None:
        c = OxmlElement("w:cols"); sp.append(c)
    c.set(qn("w:num"), str(n)); c.set(qn("w:space"), "360")

CITE_FILE = os.path.join(ROOT, "paper", "cite_order.json")
_prev = json.load(open(CITE_FILE)) if os.path.exists(CITE_FILE) else []
_seen = []
def _c(t):
    """IEEE numbering by first appearance: raw ids in the source text are renumbered using the order found on the previous run."""
    def sub(m):
        n = int(m.group(1))
        if n not in _seen: _seen.append(n)
        return f"[{_prev.index(n) + 1 if n in _prev else n}]"
    return re.sub(r"\[(\d{1,2})\]", sub, t)

_cite = _c

def para(text="", bold=False, italic=False, size=None, align=None, after=4, style=None, keep=False, raw=False):
    p = doc.add_paragraph(style=style); r = p.add_run(text if raw else _c(text)); r.bold = bold; r.italic = italic
    if size: r.font.size = Pt(size)
    if align == "c": p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align != "l": p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(after); p.paragraph_format.space_before = Pt(0)
    if keep: p.paragraph_format.keep_with_next = True
    return p

EQ = [0]
def eq(text):
    EQ[0] += 1
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text + f"      ({EQ[0]})"); r.italic = True
    p.paragraph_format.space_after = Pt(4)

def wide(path, caption, width=7.0):
    """Full-width (two-column-spanning) figure, as IEEE 'figure*'."""
    s1 = doc.add_section(WD_SECTION.CONTINUOUS); cols(s1, 1)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(path, width=Inches(width)); p.paragraph_format.space_after = Pt(1); p.paragraph_format.keep_with_next = True
    para(caption, size=8, align="c", after=6)
    s2 = doc.add_section(WD_SECTION.CONTINUOUS); cols(s2, 2)

SEC = [0]
def H(title):
    SEC[0] += 1
    roman = ["I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII","XIII","XIV","XV","XVI","XVII","XVIII","XIX","XX","XXI","XXII","XXIII","XXIV"][SEC[0]-1]
    p = para(f"{roman}. {title.upper()}", bold=True, size=9.5, align="c", after=3, keep=True); p.paragraph_format.space_before = Pt(6)
def SH(title):
    para(title, italic=True, after=2, keep=True, align="l")

def table(df, caption, widths=None, size=7.5):
    para(caption, size=8, align="c", after=2, keep=True)
    t = doc.add_table(rows=1, cols=len(df.columns)); t.style = "Table Grid"
    for i, c in enumerate(df.columns):
        cell = t.rows[0].cells[i]; cell.text = ""; r = cell.paragraphs[0].add_run(str(c).replace("_", " ")); r.bold = True; r.font.size = Pt(size)
    for _, row in df.iterrows():
        cells = t.add_row().cells
        for i, v in enumerate(row):
            if isinstance(v, float):
                s = "-" if pd.isna(v) else f"{v:.3f}"
            else:
                s = str(v)
            cells[i].text = ""; r = cells[i].paragraphs[0].add_run(_cite(s)); r.font.size = Pt(size)
    t.autofit = False
    for _i, _c in enumerate(t.columns): _c.width = Inches(3.4 / len(df.columns))
    wcol = Inches(3.4 / len(df.columns))
    for _ri, row in enumerate(t.rows):
        for c in row.cells:
            c.width = wcol
            if _ri < len(t.rows) - 1:
                for _p in c.paragraphs: _p.paragraph_format.keep_with_next = True
            for p in c.paragraphs:
                p.paragraph_format.space_after = Pt(0); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def fig(path, caption, width=3.3):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(path, width=Inches(width)); p.paragraph_format.space_after = Pt(1); p.paragraph_format.keep_with_next = True
    para(caption, size=8, align="c", after=5)

# ---------------- numbers from artefacts ----------------
rj = json.load(open(os.path.join(ROOT, "results", "rejection_results.json")))
t2 = T("T2_ocr_baseline_and_preprocessing"); t7 = T("T7_rejection_aurc"); t7b = T("T7b_paired_delta_aurc"); t9 = T("T9_generalisation_leave_one_source_out")
t6 = T("T6_readability_test"); t13 = T("T13_guidance"); t11 = T("T11_latency_stages"); t12 = T("T12_memory_and_sizes"); t10 = T("T10_localisation")
t4 = T("T4_enhancement_ablation"); t3 = T("T3_ocr_by_condition"); t8 = T("T8_rejection_operating_points"); t8b = T("T8b_rejection_operating_points_ucb")
def g(df, col, **kw):
    m = df
    for k, v in kw.items(): m = m[m[k] == v]
    return m.iloc[0][col]
rap = g(t2, "test_exact", engine="rapidocr", input="detected ROI, raw"); rapc = g(t2, "test_CER", engine="rapidocr", input="detected ROI, raw")
tes = g(t2, "test_exact", engine="tesseract", input="detected ROI, raw"); tesr = g(t2, "test_exact", engine="tesseract", input="detected ROI, red")
S = {r["strategy"][:2]: r for _, r in t7.iterrows()}
mem = {r["item"]: r["value_mb"] for _, r in t12.iterrows()}
lat = {r["stage"]: r for _, r in t11.iterrows()}
gd = t13.iloc[0]
ci = lambda s: s["AURC_CI"]

# ---------------- front matter ----------------
title = "Design of a Smart Wearable System for Gold Jewellery Hallmark Recognition and Readability Assessment"
para(title, bold=True, size=14, align="c", after=3)
para("Priyanka Lingesan, Riddhi Solanki, Pranathi Kaparthi, Krishnaraj N", bold=True, align="c", after=1, size=10.5)
para("Vellore Institute of Technology, Vellore, India", italic=True, align="c", after=1, size=9)
para("priyanka.lingesan2023@vitstudent.ac.in, riddhi.solanki2023@vitstudent.ac.in, pranathi.k2023@vitstudent.ac.in, krishnaraj.n@vit.ac.in", align="c", after=6, size=8)
cols(sec, 1)
ns = doc.add_section(WD_SECTION.CONTINUOUS); cols(ns, 2)

p = para("", after=3); r = p.add_run("Abstract—"); r.bold = True; r.italic = True
p.add_run(
 f"Gold jewellery often carries small engraved, stamped or laser-marked hallmark inscriptions that are hard to read by eye. "
 f"We design and simulate a smart wearable system that reads such inscriptions and estimates whether its own reading can be trusted. "
 f"The proposed wrist unit (a Seeed XIAO ESP32S3 Sense board with its camera, a white LED, a button and an OLED) sends one JPEG to a companion computer in a single HTTP POST. "
 f"The companion runs a Python pipeline of image-quality assessment, localisation, two OCR engines (RapidOCR and Tesseract), readability classification and calibrated rejection with recapture hints, and replies with three lines of text. "
 f"The system reads characters only; it does not verify gold purity, authenticity or BIS certification. "
 f"On a synthetic benchmark of 1440 images (240 fictitious items, item-level split), RapidOCR reached exact match {rap:.3f} versus {tes:.3f} for Tesseract, and a learned rejector on OCR-uncertainty features cut the area under the risk–coverage curve from {S['S1']['AURC']:.3f} (raw confidence) to {S['S3']['AURC']:.3f}. "
 f"No hardware was built: the wearable camera is an untested proposal, its firmware was only compiled and booted in the Wokwi simulator (which has no camera), and the HTTP receiver was tested with a Python client. A laptop-webcam path and an image-upload path feed the same pipeline.").italic = True
p = para("", after=5); r = p.add_run("Keywords—"); r.bold = True; r.italic = True
p.add_run("wearable computing, hallmark recognition, readability assessment, OCR, selective classification, ESP32.").italic = True

# ---------------- I ----------------
H("Introduction")
para("Hallmarks on gold jewellery are small, low-contrast and easily degraded by wear, glare and blur. OCR engines return a confident string even when it is wrong, so a silent misread costs more than a retake. A wrist-worn camera keeps both hands free and sees held objects at useful scale [2], and finger-worn readers show that feedback about alignment and focus helps users capture text [3]. We therefore design a wrist camera unit paired with a companion computer that reads the inscription, estimates how trustworthy the reading is, and tells the wearer how to retake a poor capture.")
para("We do not verify gold. The assistant reads visible characters only; it makes no statement about purity, composition, authenticity or BIS certification. All data are synthetic, and no hardware was built. Contributions: (1) a reproducible synthetic hallmark-inscription benchmark with per-factor degradation labels and an item-level split; (2) a benchmark of two OCR engines and a preprocessing ablation; (3) a calibrated, separated rejector with recapture guidance, compared against raw confidence; (4) a simple wearable design, one HTTP POST from a camera board to the companion, with a receiver that was tested; and (5) an honest account of what was and was not verified.")

H("Related Work")
para("Closest to our task, goldsmith’s-mark retrieval in silverware matches learned embeddings [1] but neither transcribes characters nor assesses its own reliability; we found no verified work on OCR of engraved hallmarks. Tesseract [4] and PP-OCR [5] are widely used engines, and scene-text surveys report sensitivity to blur and low resolution [6], [7]. Modern networks are over-confident [9], maximum probability is a weak error detector [10], and scene-text recognisers are miscalibrated [8], so we calibrate a learned score instead of trusting engine confidence. The reject option dates to Chow [13], with risk–coverage formulations in [11], [12] and a survey in [14]. For quality we use cheap gradient, contrast and illumination statistics in the spirit of [15], [18].")

# ---------------- III ----------------
H("System Design")
fig(D("architecture_integrated.png"), "Fig. 1. Architecture. Three sources feed one Python pipeline. The wearable unit is proposed and untested; the webcam path was tested with a test video only.", 3.3)
para("Wrist unit (proposed, not built). One Seeed XIAO ESP32S3 Sense board (ESP32-S3R8, 8 MB PSRAM) carries a detachable camera module on the board-to-board connector, so the camera needs no external wiring (Fig. 2). The proposed module is the OV5640 with autofocus that the vendor lists for the Sense; the vendor also states that boards may ship with an OV5640 or an OV3660 (fixed focus) and older pages describe an OV2640, so the fitted module is unconfirmed until a kit is received [25]. The camera is the sensor; the white LED only illuminates the mark. The remaining I/O is an SSD1306 OLED on I²C (D4, D5), a push button on D1 with the internal pull-up, and the LED on D0 through an NPN stage, because a white LED’s forward voltage is near the 3.3 V logic level and a GPIO-and-resistor drive would be dim. Power is USB-C 5 V (for example a power bank); battery operation is not designed. Pressing the button lights the LED, captures a JPEG and sends it to the companion; the unit shows the reply on the OLED. It runs no OCR or ML. We chose this board because a DVP camera needs 14 signals, which a DevKit-C-class board with a camera breakout cannot spare, and the AI-Thinker ESP32-CAM leaves only six GPIOs shared with the SD socket and flash LED and has no USB port [26]. No field of view or focus range is listed for these modules, so Fig. 3 uses the OV2640 figures [23] only as an illustrative placeholder (about 23 mm field width at 30 mm), not as OV5640 values; all optical values are estimates and must be measured on the delivered module.")
wide(D("wearable_reference_schematic.png"), "Fig. 2. Proposed wiring reference for the wrist unit. Not built, not powered, not tested. Wokwi has no camera part and mirrors only the button, OLED and LED.", 5.6)
wide(D("camera_sensing_schematic.png"), "Fig. 3. Camera and optical sensing sketch: an illustrative estimate that uses OV2640 figures [23] as a placeholder (not OV5640 values); not a simulation and not a measurement.", 5.0)
para("Interface. The wrist unit POSTs the JPEG to /api/wearable/upload on the companion with the content type image/jpeg. The companion stores the bytes unchanged, validates them (decodable, 64 to 8000 pixels per side, not blank), calls the same processing function as the webcam and upload paths, and answers in plain text with three lines: READ OK, RETAKE or NO MARK; the transcription or the recapture hint; and the readability label. A bad image gets a 400 or 422 reply and a server error a 500; no result is ever invented. There is no broker or device state. The link is plain HTTP on a local network without authentication or TLS.")
para("Companion application. Besides the wearable endpoint, the application supports a laptop webcam (OpenCV capture with live preview, retake and disconnect handling) and image upload; all three store the image, read it back and call one function that reduces the longest side to 640 pixels and runs the unchanged analysis pipeline. Identical pixels give identical results through any path; Fig. 4 shows the application.")
wide(F("fig_app_screenshots.png"), "Fig. 4. Result panel of the running companion application (headless-browser test): (a) accepted reading, (b) rejected capture with recapture guidance. The upload path shows the same panel. The camera source is a recorded test video of SYNTHETIC frames; no physical webcam or real jewellery is shown.", 7.0)

H("Recognition and Rejection Method")
para("Dataset. The benchmark has 1440 procedurally generated 640×400 images of 240 fictitious hallmark-style inscriptions (fineness numerals such as 375, 585 and 916, karat labels, the string “BIS”, a six-character code and a maker-style mark), with six degraded acquisitions per item, split by item into 144/48/48 items for train/validation/test. They are not photographs of real jewellery and carry no meaning about purity (“BIS” is only a string to be read). Examples are in Fig. 5.")
fig(F("fig_dataset_examples.png"), "Fig. 5. Examples from the SYNTHETIC dataset (procedural renderings, not photographs of real jewellery).", 3.3)
para("Pipeline. (1) 21 image-quality features (focus, contrast, illumination, glare, size) are computed; (2) the inscription is localised with a contour method based on the horizontal anisotropy of brushed metal and the region of interest (ROI) is extracted; (3) RapidOCR (PP-OCR recogniser [5]) reads the raw grayscale ROI as the primary reading and Tesseract [4] reads the red channel as the secondary reading; (4) OCR-uncertainty features (confidences, lengths, edit-distance disagreement) are built; (5) a Random Forest on the quality features gives the readability label (readable, partial, unreadable); and (6) a separated rejector, an Extra Trees base model on OCR-uncertainty and quality features with isotonic calibration fitted on out-of-fold scores, gives a probability p that the primary reading is correct. A capture is accepted if p ≥ τ, with τ chosen on development data for a target accepted-error rate (empirically, or by a one-sided Clopper–Pearson bound); otherwise the system asks for a retake and gives a rule-based hint from the largest standardised quality deficit (blur, glare, darkness, uneven light, small size).")
eq("p(x) = C( g( f(x) ) ),   accept  ⇔  p(x) ≥ τ")
para("Metrics. Recognition uses the character error rate CER = Lev(y, ŷ)/|y| and whitespace-insensitive exact match. Selective quality uses the area under the risk–coverage curve (AURC, lower is better), the expected calibration error (ECE) [9] and the paired difference of AURC with a 1000-resample item-level cluster bootstrap. Six rejection strategies are compared: S1 raw OCR confidence, S2 a hand-set quality gate, S3 a learned score on OCR-uncertainty features, S4 on quality features, S5 on both, and S6 adding grammar validity. Model choice, calibration and thresholds use development items only; the test split (48 items, 288 images) is evaluated once.")

# ---------------- V ----------------
H("Results")
para("All experiments ran on a 2-vCPU Intel Xeon at 2.1 GHz (Python 3.13, OpenCV 5.0), not on wearable hardware, and every image is synthetic.")
_t1 = pd.DataFrame([
 ["RapidOCR, raw ROI (primary)", g(t2,"test_CER",engine="rapidocr",input="detected ROI, raw"), g(t2,"test_exact",engine="rapidocr",input="detected ROI, raw")],
 ["Tesseract, red channel", g(t2,"test_CER",engine="tesseract",input="detected ROI, red"), g(t2,"test_exact",engine="tesseract",input="detected ROI, red")],
 ["Tesseract, raw ROI", g(t2,"test_CER",engine="tesseract",input="detected ROI, raw"), g(t2,"test_exact",engine="tesseract",input="detected ROI, raw")]], columns=["Engine / input", "CER", "Exact"])
table(_t1, "TABLE I. OCR baselines on the test split (48 items, 288 images).", size=7.5)
para(f"Recognition. RapidOCR clearly beats Tesseract (exact {rap:.3f}, CER {rapc:.3f} versus {tes:.3f} for Tesseract on the raw ROI); Table I, Fig. 6). Classical enhancement did not help: the full chain lowered RapidOCR exact match from {g(t4,'rapidocr_exact',config='base(raw)'):.3f} to {g(t4,'rapidocr_exact',config='full'):.3f}, so the final design uses raw crops. This is a negative result for these engines on synthetic data, not evidence that enhancement is useless in general. Accuracy falls with glare, occlusion and combined degradations.")
fig(F("fig_ocr_by_condition.png"), "Fig. 6. OCR accuracy by acquisition condition (test, synthetic).", 3.3)
_sel = t7[t7["strategy"].str[:2].isin(["S1", "S3", "S5"])][["strategy", "AURC", "ECE", "AURC_CI"]].copy(); _sel["strategy"] = _sel["strategy"].str[:2]
_sel = _sel.rename(columns={"AURC_CI": "AURC 95 % CI"})
table(_sel, "TABLE II. Rejection quality on the test split (S1 raw confidence, S3 OCR-uncertainty, S5 OCR-uncertainty + quality).", size=7.5)
para(f"Rejection (Table II, Fig. 7). Raw OCR confidence is a poor reject signal (AURC {S['S1']['AURC']:.3f}, ECE {S['S1']['ECE']:.3f}): its confidence is far above observed accuracy. The learned OCR-uncertainty rejector S3 reaches AURC {S['S3']['AURC']:.3f} (ECE {S['S3']['ECE']:.3f}), a paired improvement whose interval excludes zero. Adding quality features (S5) did not change AURC measurably (ΔAURC {t7b.iloc[0]['delta_AURC']:+.3f}, CI {t7b.iloc[0]['CI95']}), so on this synthetic data the useful rejection signal is the disagreement and confidence of the two OCR engines; quality features instead drive the recapture hints and the readability proxy (macro-F1 {g(t6,'f1_macro',feature_set=t6.iloc[0]['feature_set']):.3f} for quality only; 0.826 with OCR-uncertainty features; confusion matrices in Fig. 8).")
fig(F("fig_risk_coverage_calibration.png"), "Fig. 7. Risk–coverage curves and reliability diagram (test, synthetic).", 3.3)
fig(F("fig_confusion_pair.png"), "Fig. 8. Readability confusion matrices on the test split (rows: generator-defined proxy label, not human labels). Left: quality features only (Random Forest); right: quality + OCR-uncertainty features. Synthetic data.", 3.3)
_op = t8[t8["strategy"].str.startswith(("S1","S3","S5"))].copy(); _op["strategy"] = _op["strategy"].str[:2]
_op = _op[_op["target_accepted_error"].isin([0.05, 0.02])].rename(columns={"target_accepted_error":"target","test_coverage":"cov","test_accepted_error":"err","accepted_errors":"n_err"})
table(_op[["strategy","target","tau","cov","err","accepted","n_err"]], "TABLE III. Operating points with development-selected thresholds (test split).", size=7)
para(f"Thresholds and guidance (Table III). Development-selected thresholds do not transfer exactly: S5 at a nominal 5 % target accepted 87 captures with 5 errors (5.7 %), and with 48 test items one mistake moves these rates visibly, so we claim no guarantee. Leave-one-source-out testing kept the ordering (the learned rejector beat raw confidence on every held-out rendering source) while OCR exact match varied from 0.454 to 0.590 across sources. Among {int(gd['n_rejected_total'])} rejected test captures, {int(gd['n_rejected_with_flagged_factor'])} had a generator-flagged degradation; the top-1 hint matched it in {gd['top1_hit_rate']:.3f} of cases versus {gd['random_cause_hit_rate']:.3f} for a random cause (this tests the hint against the injected cause, not a user’s behaviour).")

para(f"System performance (sandbox CPU, not a Pi). Median end-to-end latency was {lat['total_ms']['median_ms']:.0f} ms (p95 {lat['total_ms']['p95_ms']:.0f} ms) and peak memory {mem['peak RSS: full_dual']:.0f} MB; Raspberry-Pi-class latency was not measured.")
para("Software and wearable-path checks. 27 automated tests pass. The webcam path was exercised only with a recorded test video of synthetic frames (no physical webcam was available), and the upload path and browser interface with image files. The HTTP receiver was tested with a Python client: the reply equals a direct pipeline call on the stored pixels, the stored file is byte-identical to the sent one, and empty, non-image and truncated bodies are rejected. The firmware (about 80 lines) was loaded in Wokwi on its XIAO ESP32-S3 board with an OLED, a button and an LED: it compiled and booted (Figs. 9 and 10), and the camera probe failed with ESP_ERR_NOT_SUPPORTED because Wokwi has no camera part [27], after which the firmware printed “camera init failed”. The button, OLED screens, Wi-Fi connection, the POST and any camera frame were not observed, and no frame was ever captured by the wearable camera.")
wide(D("wokwi_circuit.png"), "Fig. 9. Circuit of the Wokwi project (hardware/wokwi_xiao_s3/diagram.json): XIAO ESP32-S3, SSD1306 OLED, button, 220 Ω resistor and white LED. This simplified circuit uses a resistor-driven LED; the proposed unit uses the transistor stage of Fig. 2. Redrawn from diagram.json, not a Wokwi screenshot; Wokwi has no camera part, so the camera is not simulated.", 5.4)
fig(D("wokwi_xiao_run.jpg"), "Fig. 10. Serial output of the firmware in Wokwi (XIAO ESP32-S3): boot, then the expected camera-probe failure. This run shows nothing about the camera.", 2.6)

H("Discussion and Limitations")
para("A learned score built on the disagreement and confidence of two OCR engines rejected errors far better than raw confidence, and calibration removed most of the over-confidence. Image-quality features added nothing measurable to rejection once OCR-uncertainty was available; their value here is explanatory, driving the hints. Keeping all recognition on the companion let the wrist firmware stay at about 80 lines and the interface at one request.")
para("Limitations. (1) All data are synthetic and no real gold jewellery was imaged; real metal, lighting and stamping artefacts are not modelled. (2) Readability and per-factor labels come from generator parameters. (3) The test split has only 48 items, so confidence intervals are wide. (4) OCR engines are used off the shelf. (5) The wrist unit, camera and LED stage are a design only; no physical camera was used, the optical figures are first-order estimates, the device-to-companion link was never exercised, and the interface lacks authentication and TLS. (6) There is no user study. (7) Latency and memory come from a different CPU than the intended device. The assistant must not be presented as a way to verify that jewellery is genuine, of a stated purity or BIS-certified.")

H("Conclusion")
para("We designed a smart wearable assistant that reads hallmark-style inscriptions and says when its reading should not be trusted: a wrist camera unit sends one JPEG over HTTP to a Python pipeline whose calibrated, OCR-uncertainty-based rejector substantially improves reliability over raw confidence on a synthetic benchmark. The camera unit remains an untested proposal. Next steps are to build the unit and measure its optics and focus, send a real captured frame to the companion, and evaluate on real, consented hallmark photographs as a separate study; none of the results here should be read as real-world performance.")

H("References")
_byn = {r["n"]: r for r in refs.REFS}
_order = list(_seen)
for _i, _n in enumerate(_order, 1):
    p = para(f"[{_i}] " + refs.ieee(_byn[_n]), size=7, align="l", after=0, raw=True)
    p.paragraph_format.left_indent = Inches(0.22); p.paragraph_format.first_line_indent = Inches(-0.22)

out = os.path.join(ROOT, "paper", "hallmark_wearable_paper.docx")
doc.core_properties.title = title; doc.core_properties.author = "Priyanka Lingesan, Riddhi Solanki, Pranathi Kaparthi, Krishnaraj N"; doc.core_properties.subject = "Wearable Computing course project (simulation only; reads characters, no purity or BIS claim)"
doc.save(out); json.dump(_order, open(CITE_FILE, "w")); print("saved", out, "sections", SEC[0], "cite order", _order)
