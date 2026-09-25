# GPS Overlay Studio

A complete Streamlit photo annotation app rebuilt from the supplied project and measured against the 1600 × 1200 reference. The original gps.jpeg and map.jpeg are included byte-for-byte unchanged. No map service or API key is used.

## Folder structure

```text
gps_overlay/
├── app.py
├── overlay.py
├── requirements.txt
├── README.md
├── test_overlay.py
└── assets/
    ├── gps.jpeg
    ├── map.jpeg
    ├── DejaVuSans.ttf
    └── FONT-LICENSE.txt
```

## Run locally (Windows, macOS or Linux)

Install Python 3.12, extract the ZIP, and open a terminal inside `gps_overlay` (the directory containing app.py).

```sh
python -m venv .venv
```

Activate on Windows:

```bat
.venv\Scripts\activate
```

Activate on macOS/Linux:

```sh
source .venv/bin/activate
```

Then:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL shown in the terminal. Upload a photograph, set date/time and opacity, then download JPG or PNG. Location, address, coordinates and map are fixed reference fields. There is no location lookup.

## Streamlit Community Cloud deployment

1. Create a GitHub repository.
2. Upload the **contents** of `gps_overlay` to its root, including the entire assets folder. Do not upload only the ZIP.
3. Sign in at https://share.streamlit.io/ and connect GitHub.
4. Choose **Create app**, then select your repository and branch.
5. Set **Main file path** to `app.py`. If you uploaded the enclosing folder instead, use `gps_overlay/app.py`.
6. In **Advanced settings**, select Python **3.12**. No secrets are needed.
7. Click **Deploy**. Dependencies install from requirements.txt.
8. Open the resulting app URL and upload a photo. To update it, commit changed project files to the selected branch.

Official deployment instructions: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
Dependency instructions: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies

The source is ready to deploy; no live deployment is included.

## Reference layout and deliberate differences

Measured reference landmarks (pixels on the supplied 1600 × 1200 photo):

| Element | Reference bounds |
|---|---|
| Combined overlay | (188, 828) to (1412, 1174) |
| Information panel | (505, 884) to (1412, 1174) |
| Map allocation | (188, 884), 290 × 290 |
| Header | (1150, 828), 262 × 54 |
| Text left edge | x = 527 |
| Text row tops | y = 914, 983, 1074, 1119 |

The compositor uses one scale `min(width / 1600, height / 1200)` for all geometry. It anchors to the bottom and right with the measured reference offsets. This preserves the map, header and text proportions in landscape, square, portrait and panoramic images. On very wide photos the overlay is intentionally narrower relative to the photo rather than stretched.

The supplied map is 290 × 288 and is contained without stretching/cropping; it is vertically centered in its square allocation. Both JPEG assets retain their original photographic backgrounds and quality limitations. Only their outer corners receive rounded masks. Panel opacity defaults to 66%; it is an estimate because the clean background behind the original translucent panel is unavailable.

A bundled DejaVu Sans font gives consistent rendering across platforms. It is a close substitute, not a claim of pixel-identical typography. A vector Indian flag avoids platform-dependent missing emoji glyphs. EDITED appears beside the header, outside the text rows. These are intentional differences from the reference.

All text is measured with Pillow textbbox. Address text wraps (including unbroken words); font size decreases until the complete text fits its allocated area. Excessively long text is rejected with an explanatory message, never silently clipped or truncated. Fixed template text can be changed in overlay.py; it is deliberately not editable in the UI.

## Image handling and limits

- JPG, PNG and still WebP; up to 30 MB and 24 megapixels.
- Both dimensions must be at least 320 pixels. Very small or extreme-aspect photos have small annotation text; use higher resolution for readability.
- Original image bytes and EXIF are never edited. Display orientation follows EXIF; a portrait encoded sideways therefore has its width/height swapped to the correct visual orientation.
- Exports are fresh rendered images with no EXIF/GPS metadata. Manually entered dates are not verified capture dates.
- Output retains the oriented photograph's full dimensions. JPEG uses quality 97, no chroma subsampling; PNG is lossless.
- Transparent uploads are composited onto white. Animated inputs are rejected.
- No existing watermark or overlay is removed. Use a clean source photo; uploading the reference photo itself adds a second overlay over its existing annotation.
- Fixed map/coordinates are template content, not evidence of the photo's actual location.

## Verification

```sh
python -m unittest -v
```

Automated checks cover 1600×1200, 1920×1080, 1280×720, portrait, square, 2048×1536, 4000×3000, 320×320, and extreme wide/tall images; full-size JPG/PNG encoding and decoding; unchanged source pixels; metadata-free export; long location/address and unbroken words; date/time changes; corrupt/small inputs; EXIF orientation; and asset loading from a different working directory. Rendering assertions check text stays inside the panel. Streamlit AppTest additionally checked startup/restart, date/time controls and the photo workflow with both download buttons. The file uploader was supplied programmatically for that test; a deployed-browser upload was not exercised.

Tested with Streamlit 1.64.0 and Pillow 12.3.0. Dependencies are pinned to those tested versions. Missing or damaged assets are reported in the UI. Cloud deployment has not been performed.
