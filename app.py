from datetime import datetime, timezone, timedelta
import logging
import streamlit as st
from overlay import load_photo, draw_overlay, export_image, validate_assets, LOCATION, ADDRESS, COORDS

st.set_page_config(page_title='GPS Overlay Studio',page_icon='📷',layout='wide')
st.title('GPS Overlay Studio')
st.caption('Your photograph. A consistent reference layout. Full-resolution downloads.')
st.info('Generated annotation • Date and time are manually entered, not verified camera metadata. Every export is visibly marked EDITED.')
try:
    validate_assets()
except (ValueError, OSError) as exc:
    st.error(str(exc)); st.stop()
now=datetime.now(timezone(timedelta(hours=5,minutes=30)))
with st.sidebar:
    st.header('PHOTO')
    uploaded=st.file_uploader('Upload photograph',type=['jpg','jpeg','png','webp'],help='Still images, up to 30 MB and 24 megapixels.')
    st.header('DATE')
    chosen_date=st.date_input('Annotation date',value=now.date())
    st.header('TIME')
    chosen_time=st.time_input('Annotation time (India, GMT +05:30)',value=now.time().replace(second=0,microsecond=0,tzinfo=None))
    st.header('TEMPLATE')
    st.success('Header, map and font ready')
    with st.expander('Fixed reference fields'):
        st.write(LOCATION); st.write(ADDRESS); st.write(COORDS)
        st.caption('The fixed map and coordinates do not represent the uploaded photo’s verified location.')
    st.header('OPTIONS')
    opacity=st.slider('Panel opacity',40,85,66,format='%d%%')/100
if uploaded is None:
    st.info('Choose a photograph in the sidebar to begin.')
    st.stop()
try:
    photo=load_photo(uploaded.getvalue())
    result=draw_overlay(photo,chosen_date,chosen_time,opacity)
    left,right=st.columns(2)
    with left:
        st.subheader('Original'); st.image(photo,width='stretch')
    with right:
        st.subheader('Generated'); st.image(result,width='stretch')
    st.caption(f'{result.width:,} × {result.height:,} pixels • Original upload unchanged • Export contains no EXIF/GPS metadata')
    a,b=st.columns(2)
    a.download_button('Download JPG',export_image(result,'JPEG'),'gps_overlay_edited.jpg','image/jpeg',width='stretch')
    b.download_button('Download PNG',export_image(result,'PNG'),'gps_overlay_edited.png','image/png',width='stretch')
except ValueError as exc:
    st.error(str(exc))
except Exception:
    logging.exception('Overlay generation failed')
    st.error('The photograph could not be processed. Try a smaller image or restore the template assets.')
