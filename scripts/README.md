# Vector figure reproduction

Figure generation is optional post-processing of retained results, not an experiment or part of certificate checking. It needs Python 3.10+, Matplotlib, and FontTools (a Matplotlib dependency).

```sh
python -m pip install matplotlib fonttools
python scripts/plot_figures.py
```

The native outputs are in `artifact/figures/`. To copy identical PDFs into a full project's sibling paper, add `--paper-figures ../paper/figures`. A paper-only package can compile its shipped figure PDFs without Python.

The producer reads the original rational `results/sensitivity/coverage_slice.csv` and `noise_sweep.csv`, not a new channel simulation. Coverage keeps all 13 rows and the original 0–10 displayed rank range. Noise keeps all 17 points, the coincident coset/oracle series, and the existing `noise-python.pdf` name. `paper/figures/draw_noise.py` forwards to this producer.

The text family is Times New Roman (the IEEE body family). On Windows the producer discovers `times.ttf`, `timesi.ttf`, and `timesbd.ttf` under the system Fonts directory. Elsewhere it tries installed Times New Roman, then the metrics-compatible Liberation Serif, then bundled STIXGeneral as a documented Times-style fallback. Install Times New Roman when exact family matching is required; no proprietary font file is redistributed.

PDF text is embedded with `pdf.fonttype=42`; `text.usetex` and unembedded PDF core fonts are disabled. Curves, markers, axes, and text remain vector objects. The canvas and axis rectangles are explicit PDF-point dimensions measured from the current manuscript plots; saving does not crop or rasterize them. Captions and float placement remain in the TeX source.
