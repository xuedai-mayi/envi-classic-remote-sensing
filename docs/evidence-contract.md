# Evidence Contract

The run directory `.envi-runs/<run-id>/` contains:

```text
report-evidence.json
report-evidence.md
screenshots/
  001-<stage-id>.png
  002-<stage-id>.png
```

`report-evidence.json` is the machine-readable source of truth. It records:

- SHA-256 hashes for the teacher guide, template and every data file;
- the ordered, frozen stage plan;
- one original PNG per completed stage;
- evidence type, caption, actual action, parameters, window title and dimensions;
- registered output files and hashes;
- final completeness result and failure reasons.

The report layer must resolve images by `stage_id` and verify their hashes. It must not infer meaning from filename order, silently replace an image, or generate a substitute screenshot. Comparisons are document-layout operations over separate original image files, never a new composite bitmap.
