import os
# Setting environment variables
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["KERAS_BACKEND"] = "jax"
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import keras
import warnings
warnings.filterwarnings("ignore")


def resize_for_inference(input_image):
    image = np.array(input_image)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mask = np.zeros(image.shape[:2], np.uint8)

    height, width = image.shape[:2]
    rect = (10, 10, width - 20, height - 20) 
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    cv2.grabCut(image_rgb, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)

    binary_mask = np.where((mask == 2) | (mask == 0), 0, 255).astype('uint8')

    resized_mask = cv2.resize(binary_mask, (720, 960), interpolation=cv2.INTER_AREA)

    target_size = (224, 224)
    final_resized_mask = cv2.resize(resized_mask, target_size, interpolation=cv2.INTER_AREA)

    final_resized_mask = np.expand_dims(final_resized_mask, axis=-1)

    return final_resized_mask

st.title("Body Measurement Predictor")
st.write("Upload an image to predict body measurements.")
uploaded_image = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if 'loaded_model' not in st.session_state:
    with st.spinner("Model is getting loaded. Please wait..."):
        try:
            st.session_state.loaded_model = keras.saving.load_model("hf://datasciencesage/bodym_measurement_model")
            st.success("Model loaded successfully!")
        except Exception as e:
            st.error(f"Error loading model: {e}")


if uploaded_image is not None:
    image = Image.open(uploaded_image)
    st.image(image, caption="Uploaded Image", use_column_width=True)

    with st.spinner("DOING IMAGE PREPROCESSING.....PLEASE WAIT..."):
        resized_image = resize_for_inference(image)
        single_image_expanded = np.expand_dims(resized_image, axis=0)
    
    with st.spinner("INFERENCE IS BEING DONE.....PLEASE WAIT..."):
        single_image_expanded = np.expand_dims(resized_image, axis=0)

        predicted_values = st.session_state.loaded_model.predict(single_image_expanded)[0]
    columns = ['ankle', 'arm-length', 'bicep', 'calf', 'chest',
               'forearm', 'height', 'hip', 'leg-length', 'shoulder-breadth',
               'shoulder-to-crotch', 'thigh', 'waist', 'wrist']



    st.write("Predicted Body Measurements:")
    for body_type, measurement in zip(columns, predicted_values):
        st.write(f"{body_type}: {measurement:.2f} cm")
