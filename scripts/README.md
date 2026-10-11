# Downloadable CV

`build_cv.py` generates the English `cv.pdf` from the substantive sections of
`cv/index.html`. It preserves manuscript and coursework status, advisor and
collaborator attribution, contacts, dates, and mathematical notation. The
Chinese CV is maintained as a translation of the same information.

To update the CV:

1. Edit `cv/index.html` and the corresponding `zh/cv/index.html` content.
2. Update both `<time datetime="YYYY-MM-DD">` elements and their visible dates.
3. Update the `?v=YYYYMMDD` suffix on all six PDF links in the two homepages and
   the two CV pages. Keep the file path `cv.pdf` stable for direct links.
4. Generate the PDF:

   ```sh
   python3 -m pip install -r scripts/requirements-cv.txt
   python3 scripts/build_cv.py
   ```

5. Render and inspect every PDF page, including mathematical symbols and page
   breaks. Compare the extracted PDF text with all eight online CV sections.
6. Commit the PDF and matching HTML updates together; confirm the GitHub Pages
   deployment succeeds and all download links serve the committed PDF.

The script uses the fonts bundled with ReportLab and an embedded DejaVu Sans
subset for Greek gamma (`fonts/CVSymbols.ttf`; license in `fonts/LICENSE.txt`).
PDF timestamps come from the visible update date, making
the output reproducible with the pinned dependencies. The layout currently
targets two US Letter pages; inspect pagination if future entries are added.
