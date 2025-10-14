import streamlit as st
from utils.comfy_api import Comfy
from utils.file_util import find_new_file_name
from random import randint

WORKFLOW = "sdxlturbo_example.json"

def generate_image(WORKFLOW, prompt, neg_prompt, width, height, seed):
    try:
        comfy_client = Comfy(WORKFLOW)  # ComfyUI client instance
        print("Connected to ComfyUI Client!")
        img = comfy_client.get_image(prompt, neg_prompt, width, height, seed)
        return img
    except Exception as e:
        st.error(f"Error generating image, check terminal output {e}")
        return None

st.title("ComfyUI API powered image generator")

prompt = st.text_input("Prompt","")
neg_prompt = st.text_input("Negative prompt","")
width = st.number_input("Width (pixels)", 1, 2000, 512)
height = st.number_input("Height (pixels)", 1, 2000, 512)
seed = st.number_input("Seed (leave empty for random)",0,999999999,None)

if st.button("Generate image"):
    if not prompt:
        st.warning("No prompt entered!")
        pass
    else:
        if not seed:
            seed = randint(1,999999999)
            print(f"Random seed set: {seed}")
            with st.spinner("Image generating..."):
                img = generate_image(WORKFLOW, prompt, neg_prompt, width, height, seed)
                if img:
                    st.image(img)
                    filename = find_new_file_name(f"{prompt[:14]}.png")
                    with open(img, "rb") as file:
                        st.download_button(
                            label="Download image",
                            data=file,
                            file_name=filename,
                            mime="image/png",
                        )
                else:
                    st.error("Error generating image, check terminal output")
