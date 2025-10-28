# Specification: Diagram Extraction Tool for Handwritten Notes

## Purpose
Develop a tool that accepts a handwritten note (PNG) and extracts any *non-handwriting* diagrams/sketches into separate transparent-background PNGs, while leaving the original note untouched. Output also includes a JSON manifest describing detected diagrams.

The notes will come from Apple Notes written with an Apple Pencil.

---

## Functional Requirements

### Input
- Single PNG image
- Handwritten note created in Apple Notes with Apple Pencil
- Portrait or landscape orientation supported

### Output
- Original note (unchanged)
- 0..N PNG files containing detected diagram regions
  - Transparent background
  - Cropped to bounding region
- JSON manifest describing diagram files and positions

### JSON Manifest Format

```json
{
  "original_file": "input_note.png",
  "diagrams": [
    {
      "file": "note_diagram_1.png",
      "bbox": [x, y, w, h],
      "confidence": 0.92
    }
  ]
}
```

If no diagrams are found:

```json
{
  "original_file": "input_note.png",
  "diagrams": [],
  "message": "No diagrams detected"
}
```

---

## Diagram Definition

### Extract as diagram if:
- It is *not handwriting*
- It includes one or more of:
  - Geometric shapes (box, circle, triangle, ellipse)
  - Flow-diagram shapes
  - Arrows / arrowheads
  - UI boxes / mockup shapes
  - Doodles or drawn illustrations
  - Structured shapes or repeated strokes forming a figure
  - Dense scribbles not resembling characters

### Ignore (do not extract) if:
- Handwritten text
- Underlines beneath text
- Handwritten bullets (•, –, *, checkbox marks)
- Simple separators (horizontal/vertical lines)
- Checkmarks used as bullets
- **Any shape touching text** *(if a diagram touches handwriting, do not extract it)*

### Ambiguity rule
If uncertain, classify as handwriting (do not extract).

---

## Detection Rules

### Grouping (Clustering)
- Adjacent shapes **should be clustered** into one diagram
- Clustering threshold: ~25px proximity (configurable)

### Bounding Boxes
- No overlapping bounding boxes
- Each diagram should have a clean, non-overlapping bounding box
- +3px padding around each extracted region to avoid clipping

### Confidence Score
For each diagram, return a confidence value (float 0.0–1.0) representing certainty that the extracted region is *not handwriting*.

---

## Processing Expectations

### Steps
1. Convert image to grayscale
2. Adaptive thresholding
3. Morphological filtering to isolate strokes
4. Contour detection + connected components
5. Filter based on contour size + stroke density
6. Identify handwriting vs shapes via heuristics:
   - Handwriting:
     - thin curved strokes
     - irregular baselines
     - small repeated curvatures (letters)
   - Diagram traits:
     - straight lines
     - perfect curves
     - enclosed shapes
     - strong angular intersections
     - arrowheads
7. Cluster adjacent diagram strokes
8. Reject diagrams touching text
9. Output transparent PNG crops + manifest

### Performance
- Target: process one note in ≤ 3 seconds on modern laptop
- Must preserve line sharpness (no smoothing or blur)
- PNG output must be lossless

---

## Configuration Parameters

| Setting | Default |
|---|---|
Minimum diagram contour area | 750 px
Clustering proximity | 25px
Padding around extracted region | 3px
Max diagrams per note | 10 (configurable)
Dilation kernel | (3×3)
Confidence threshold | return all, consumer filters later

---

## CLI Requirements

### Example command

```bash
python extract_diagrams.py --input note.png --output ./out/
```

### CLI Output
- `note.png` (unchanged)
- `diagram_1.png`
- `diagram_2.png`
- `manifest.json`

---

## File Structure

```
/tool
  /src
    extract_diagrams.py
    utils/
  /examples
    input1.png
    expected_output/
  /tests
  README.md
  requirements.txt
```

---

## Testing

### Provide test images:
- Simple note with boxed diagram
- Multiple shapes close together (cluster)
- No diagrams (handwriting only)
- Diagram touching text (should not extract)
- Doodles vs text differentiation scenario

### Include automated tests for:
- Contour detection logic
- Handwriting rejection logic
- Diagram clustering
- Manifest formatting

---

## Deliverables

- Python 3 code using OpenCV
- CLI executable script
- Unit tests
- Example input/output images
- README with install & usage instructions

---

## Notes to Developer

- Prioritize correctness over aggressive extraction
- Bias toward **not extracting** rather than false positives
- Maintain transparent background for diagram PNGs
- Ensure reproducible results (seed randomness if used)

---

## Future Enhancements (not in current scope)

- OCR of text areas
- Embedded vector export if shapes detected
- GUI tool
- Notebook integration for iterative testing

---
