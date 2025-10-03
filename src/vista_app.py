import streamlit as st
from PIL import Image
from image_metadata import ImageMetadata
import os
import tempfile
from streamlit_modal import Modal
from image_to_blog import ImageToBlog
from ai_detection import AIDetection
from st_copy_to_clipboard import st_copy_to_clipboard

st.title('VISTA Blog Generator')
st.write("Upload images one at a time in the desired order to generate a human-like blog.")

uploaded_files = st.file_uploader("Upload images...", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

if 'images_dict' not in st.session_state:
    st.session_state.images_dict = {}

if uploaded_files:
    images = []
    for uploaded_file in uploaded_files:
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name
            images.append((uploaded_file.name, temp_file_path))
            st.session_state.images_dict[uploaded_file.name] = ImageMetadata(temp_file_path)

    num_cols = min(len(images), 4)

    rows = [images[i:i + num_cols] for i in range(0, len(images), num_cols)]

    for row_images in rows:
        cols = st.columns(len(row_images))
        for col, (filename, file_path) in zip(cols, row_images):
            with Image.open(file_path) as image:
                col.image(image, use_column_width=True)
                col.caption(filename)
                modal = Modal(f"Details for {filename}", key=f"modal_{filename}")
                if col.button(f"View Details {filename}"):
                    modal.open()
                if modal.is_open():
                    with modal.container():
                        st.image(image, use_column_width=True)
                        img_metadata = ImageMetadata(file_path)
                        st.write("**Timestamp:**", img_metadata.time if img_metadata.time else "Not available")
                        st.write("**Latitude:**", img_metadata.lat if img_metadata.lat else "Not available")
                        st.write("**Longitude:**", img_metadata.lon if img_metadata.lon else "Not available")
                        st.write("**Location:**", img_metadata.loc if img_metadata.loc else "Not available")

            # Remove the temporary file and clean up images_dict
            os.remove(file_path)
            # if filename in st.session_state.images_dict:
            #     del st.session_state.images_dict[filename]  # Remove from session state
    if st.button("**GENERATE BLOG**", type="primary"):
        test = ImageToBlog()
        with st.spinner("Generating Image Descriptions..."):
            test.add_images(st.session_state.images_dict)
        with st.spinner("Generating Response..."):
            test.generate_response()
        # with st.spinner("Merging responses...."):
        #     test.merge_responses()
        st.write(test.response)
        st.write(test.fine_tune_response)
        st_copy_to_clipboard(test.response)
        with st.spinner("Loading AI Probability score..."):
            st.write(f"AI Probability Score: {AIDetection.getPercentage(test.response)}")
