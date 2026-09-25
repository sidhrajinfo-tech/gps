"""Reference-measured GPS annotation compositor; no network or metadata writes."""
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from functools import lru_cache
import warnings
import math
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

BASE = Path(__file__).resolve().parent
ASSETS = BASE / 'assets'
LOCATION = 'Isarwada, Gujarat, India'
ADDRESS = 'Fjx9+w6r, Gj Sh 8, Isarwada, Gujarat 388180, India'
COORDS = 'Lat 22.501558° Long 72.619438°'
MAX_PIXELS = 24_000_000
MAX_BYTES = 30 * 1024 * 1024

@dataclass(frozen=True)
class Geometry:
    x: int
    y: int
    width: int
    height: int
    scale: float

def calculate_overlay_geometry(width, height):
    # Measured on 1600x1200 reference: band (188,828)-(1412,1174).
    # A single scale prevents stretching; bottom/right offsets use that scale.
    scale = min(width / 1600, height / 1200)
    bw, bh = round(1224 * scale), round(346 * scale)
    return Geometry(width-round(188*scale)-bw, height-round(26*scale)-bh, bw, bh, scale)

@lru_cache(maxsize=256)
def font(size):
    return ImageFont.truetype(str(ASSETS / 'DejaVuSans.ttf'), size)

def text_width(draw, text, f):
    b = draw.textbbox((0, 0), text, font=f)
    return b[2] - b[0]

def wrap_text(draw, text, f, max_width):
    """Wrap words, splitting unbroken tokens without dropping characters."""
    lines, line = [], ''
    for word in text.split():
        candidate = (line + ' ' + word).strip()
        if text_width(draw, candidate, f) <= max_width:
            line = candidate
            continue
        if line:
            lines.append(line)
        line = ''
        for char in word:
            if line and text_width(draw, line + char, f) > max_width:
                lines.append(line)
                line = ''
            line += char
    if line:
        lines.append(line)
    return lines or ['']

def fit_text(draw, text, width, height, start_size, max_lines=1, min_size=12):
    """Fit complete text or raise an actionable error; never silently truncate."""
    for size in range(int(start_size), min_size-1, -1):
        f = font(size)
        lines = wrap_text(draw, text, f, width) if max_lines > 1 else [text]
        line_height = math.ceil(size * 1.16)
        if len(lines) <= max_lines and len(lines)*line_height <= height and all(text_width(draw, line, f) <= width for line in lines):
            return f, lines, line_height
    raise ValueError('Template text is too long to fit legibly. Shorten the location or address in overlay.py.')

def validate_assets():
    for name in ['gps.jpeg', 'map.jpeg', 'DejaVuSans.ttf']:
        if not (ASSETS/name).is_file():
            raise ValueError(f'Missing template file: assets/{name}. Restore the complete assets folder.')
    for name in ['gps.jpeg', 'map.jpeg']:
        try:
            with Image.open(ASSETS/name) as im:
                im.verify()
        except (OSError, ValueError) as exc:
            raise ValueError(f'Template image {name} is damaged. Restore it from the ZIP.') from exc
    font(20)

def load_photo(data):
    if len(data) > MAX_BYTES:
        raise ValueError('Please choose a file smaller than 30 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as im:
                if im.format not in {'JPEG','PNG','WEBP'}:
                    raise ValueError('Choose a JPG, PNG or WebP photograph.')
                if im.width * im.height > MAX_PIXELS:
                    raise ValueError('Please resize the photograph to 24 megapixels or fewer.')
                if min(im.size) < 320:
                    raise ValueError('Both image dimensions must be at least 320 pixels for a readable overlay.')
                if getattr(im, 'is_animated', False):
                    raise ValueError('Please upload a still photograph instead of an animation.')
                # Honor orientation for display; source bytes/EXIF are never changed.
                oriented = ImageOps.exif_transpose(im).convert('RGBA')
                background = Image.new('RGBA', oriented.size, 'white')
                background.alpha_composite(oriented)
                result = background.convert('RGB')
                result.info.clear()
                return result
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError('This image cannot be read safely. Please upload a valid JPG, PNG or WebP.') from exc

def draw_overlay(photo, chosen_date, chosen_time, opacity=0.66, location=LOCATION, address=ADDRESS, coords=COORDS):
    validate_assets()
    if any(len(field) > 2048 for field in (location, address, coords)):
        raise ValueError('Template text is too long. Use at most 2048 characters per field.')
    if not 0 <= opacity <= 1:
        raise ValueError('Opacity must be between 0 and 1.')
    g = calculate_overlay_geometry(*photo.size)
    if min(photo.size) < 320 or photo.width*photo.height > MAX_PIXELS:
        raise ValueError('Use dimensions of at least 320 pixels and at most 24 megapixels.')
    # Render at >= 2x reference size, then downsample only once for smooth edges.
    q = max(2, math.ceil(g.scale))
    layer = Image.new('RGBA', (1224*q, 346*q))
    d = ImageDraw.Draw(layer)
    def rect(box, radius, fill):
        d.rounded_rectangle(tuple(round(v*q) for v in box), radius=radius*q, fill=fill)
    rect((317,56,1223,345), 16, (0,0,0,round(opacity*255)))
    # Preserve full image content/aspect, with rounded outer clipping only.
    def asset(name, box, radius):
        with Image.open(ASSETS/name) as source:
            resized = ImageOps.contain(source.convert('RGBA'), (box[2]*q,box[3]*q), Image.Resampling.LANCZOS)
        mask = Image.new('L',resized.size)
        ImageDraw.Draw(mask).rounded_rectangle((0,0,resized.width-1,resized.height-1),radius=radius*q,fill=255)
        resized.putalpha(mask)
        x=box[0]*q+(box[2]*q-resized.width)//2
        y=box[1]*q+(box[3]*q-resized.height)//2
        layer.alpha_composite(resized,(x,y))
    asset('map.jpeg',(0,56,290,290),14)
    asset('gps.jpeg',(962,0,262,54),10)
    rect((854,19,947,49),6,(35,35,35,235))
    d.text((865*q,24*q),'',font=font(19*q),fill='white',anchor='lt')
    records=[]
    def text(text, box, size, lines=1):
        x,y,w,h=box
        f, rows, step=fit_text(d,text,w*q,h*q,size*q,lines,12*q)
        for i,row in enumerate(rows):
            pos=(x*q,y*q+i*step)
            d.text(pos,row,font=f,fill='white',anchor='lt')
            b=d.textbbox(pos,row,font=f,anchor='lt')
            assert b[0]>=317*q and b[2]<=1224*q and b[3]<=346*q
            records.append(b)
        return max(text_width(d,row,f) for row in rows)/q
    title_width=text(location,(339,86,700,64),60)
    # Vector flag avoids missing emoji glyphs across Windows/Linux.
    fx=min(339+title_width+18,1124); fy=89
    for i,color in enumerate(['#FF9933','white','#138808']):
        d.rectangle((fx*q,(fy+16*i)*q,(fx+70)*q,(fy+16*(i+1))*q),fill=color)
    cx,cy=(fx+35)*q,(fy+24)*q
    d.ellipse((cx-7*q,cy-7*q,cx+7*q,cy+7*q),outline='#000080',width=q)
    for a in range(24):
        theta=a*math.pi/12
        d.line((cx,cy,cx+7*q*math.cos(theta),cy+7*q*math.sin(theta)),fill='#000080',width=max(1,q//2))
    text(address,(339,155,857,90),40,2)
    text(coords,(339,246,857,45),40)
    dt=datetime.combine(chosen_date,chosen_time)
    weekday=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][dt.weekday()]
    stamp=f'{weekday}, {dt:%d/%m/%Y} {dt.hour%12 or 12:02d}:{dt.minute:02d} {"AM" if dt.hour<12 else "PM"} GMT +05:30'
    text(stamp,(339,291,857,45),40)
    layer=layer.resize((g.width,g.height),Image.Resampling.LANCZOS)
    result=photo.convert('RGBA')
    result.alpha_composite(layer,(g.x,g.y))
    result=result.convert('RGB')
    result.info.clear()
    return result

def export_image(image, fmt):
    buf=BytesIO()
    clean=Image.new('RGB',image.size)
    clean.paste(image)
    clean.save(buf,format=fmt,**({'quality':97,'subsampling':0} if fmt=='JPEG' else {}))
    return buf.getvalue()
