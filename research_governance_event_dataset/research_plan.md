# Research Plan: waste room governance event test set

Main question: collect and organize real or near-real image/video sources for a customer-facing waste room governance demo, with categories driven by operational events rather than trash material classes.

Subtopics:
1. Real detection datasets for litter, trash bags, overflow, and illegal dumping that can support YOLO-style object detection.
2. Real or near-real image sources for ground stains, water, reflection, rain, low light, and other false-positive/edge-case conditions.
3. Fixed-camera CCTV or municipal waste site imagery that resembles customer input, including full/overflow bins, people interactions, workers, vehicles, and environmental interference.
4. Test set schema: labels, positive/negative/borderline split, minimum image counts, provenance fields, and acceptance checks.

Synthesis:
Create a repo-level taxonomy and manifest template first. Add public source candidates with URLs and mapping to the seven governance event categories. Use only actual downloadable/traceable samples for training; use unannotated public images only as test candidates until manually labeled.
