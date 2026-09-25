import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from datetime import date, time, datetime

st.set_page_config(page_title="GPS Overlay Maker", layout="wide")

st.title("GPS-style Photo Overlay Maker")
st.caption("Uses the supplied GPS Camera and map graphics as a fixed template. Date/time are editable; the exported image is marked EDITED.")

BASE = os.path.dirname(os.path.abspath(__file__))
GPS_PATH = os.path.join(BASE, "gps.jpeg")
MAP_PATH = os.path.join(BASE, "map.jpeg")

# Fixed template values taken from the supplied reference image.
LOCATION = "Isarwada, Gujarat, India 🇮🇳"
ADDRESS = "FjX9+w6r, Gj Sh 8, Isarwada, Gujarat 388180, India"
COORDS = "Lat 22.501558° Long 72.619438°"

def font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def fit_font(draw, text, max_width, start_size, min_size):
    size = start_size
    while size > min_size:
        f = font(size)
        if draw.textbbox((0, 0), text, font=f)[2] <= max_width:
            return f
        size -= 1
    return font(min_size)

def wrap_text(draw, text, max_width, f, max_lines=2):
    words = text.split()
    lines, line = [], ""
    for word in words:
        test = word if not line else line + " " + word
        if draw.textbbox((0, 0), test, font=f)[2] <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    if len(lines) > max_lines:
        # Keep the text inside the panel.
        lines = lines[:max_lines]
        while draw.textbbox((0, 0), lines[-1] + "…", font=f)[2] > max_width and len(lines[-1]) > 1:
            lines[-1] = lines[-1][:-1]
        lines[-1] += "…"
    return lines

def make_overlay(photo, chosen_date, chosen_time):
    photo = photo.convert("RGBA")
    W, H = photo.size

    # Scale reference layout from the supplied 1600x1200 image.
    sx, sy = W / 1600.0, H / 1200.0
    S = min(sx, sy)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    # Main translucent rounded panel (reference: approximately x=445,y=778 to x=1245,y=1033)
    left, top = int(445*sx), int(778*sy)
    right, bottom = int(1245*sx), int(1035*sy)
    radius = int(14*S)
    d.rounded_rectangle((left, top, right, bottom), radius=radius, fill=(0, 0, 0, 178))

    # GPS Map Camera header asset from the supplied reference.
    gps = Image.open(GPS_PATH).convert("RGBA")
    # Reference header is about 228x47 px; preserve its aspect ratio.
    header_w = int(228*sx)
    header_h = int(47*sy)
    gps = gps.resize((header_w, header_h), Image.Resampling.LANCZOS)
    header_x = right - header_w
    header_y = top - int(48*sy)
    overlay.alpha_composite(gps, (header_x, header_y))

    # Map thumbnail asset from the supplied reference.
    map_im = Image.open(MAP_PATH).convert("RGBA")
    map_w, map_h = int(255*sx), int(255*sy)
    map_im = map_im.resize((map_w, map_h), Image.Resampling.LANCZOS)

    # Keep the map just outside/overlapping the left edge like the reference.
    map_x = int(165*sx)
    map_y = int(778*sy)
    # Rounded clipping mask.
    mask = Image.new("L", (map_w, map_h), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, map_w, map_h), radius=int(14*S), fill=255)
    overlay.paste(map_im, (map_x, map_y), mask)

    # Text area inside panel.
    pad_x, pad_y = int(22*sx), int(21*sy)
    text_left = left + pad_x
    text_width = right - left - 2*pad_x

    # Location line.
    loc_font = fit_font(d, LOCATION, text_width, int(42*S), int(24*S))
    d.text((text_left, top + int(18*sy)), LOCATION, font=loc_font, fill="white")

    # Address, automatically constrained to the box.
    addr_font = font(int(26*S))
    addr_lines = wrap_text(d, ADDRESS, text_width, addr_font, max_lines=2)
    y = top + int(70*sy)
    for line in addr_lines:
        d.text((text_left, y), line, font=addr_font, fill="white")
        y += int(29*sy)

    # Coordinates.
    coord_font = font(int(26*S))
    d.text((text_left, top + int(170*sy)), COORDS, font=coord_font, fill="white")

    # Editable date/time.
    dt = datetime.combine(chosen_date, chosen_time)
    date_text = dt.strftime("%A, %d/%m/%Y %I:%M %p GMT +05:30")
    d.text((text_left, top + int(207*sy)), date_text, font=coord_font, fill="white")

    # Small in-image transparency/edited notice.
    # This prevents a manually changed timestamp from being presented as an authentic camera record.
    tag = "EDITED"
    tag_font = font(max(12, int(14*S)), bold=True)
    tb = d.textbbox((0, 0), tag, font=tag_font)
    tw, th = tb[2]-tb[0], tb[3]-tb[1]
    tx = right - tw - int(14*S)
    ty = bottom - th - int(10*S)
    d.rounded_rectangle((tx-int(7*S), ty-int(4*S), tx+tw+int(7*S), ty+th+int(4*S)),
                         radius=int(5*S), fill=(150, 25, 25, 220))
    d.text((tx, ty), tag, font=tag_font, fill="white")

    return Image.alpha_composite(photo, overlay).convert("RGB")

st.sidebar.header("1. Upload Photo")
uploaded = st.sidebar.file_uploader("Choose any JPG/PNG/WebP", type=["jpg","jpeg","png","webp"])

st.sidebar.header("2. Date & Time")
chosen_date = st.sidebar.date_input("Date", value=date.today())
chosen_time = st.sidebar.time_input("Time", value=time(10, 49))

st.sidebar.info("Location, map, GPS Camera graphic and coordinates stay fixed to the supplied reference template.")

if uploaded:
    photo = Image.open(uploaded)
    result = make_overlay(photo, chosen_date, chosen_time)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original")
        st.image(photo, use_container_width=True)
    with col2:
        st.subheader("Generated")
        st.image(result, use_container_width=True)

    buf = BytesIO()
    result.save(buf, format="JPEG", quality=95, subsampling=0)
    st.download_button(
        "Download JPG",
        data=buf.getvalue(),
        file_name="gps_overlay_edited.jpg",
        mime="image/jpeg"
    )
else:
    st.info("Upload a photo to begin.")
