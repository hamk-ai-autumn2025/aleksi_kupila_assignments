import time
import streamlit as st
from utils.comfy_api import Comfy
from utils.file_util import find_new_file_name
from random import randint

WORKFLOW = "sdxlturbo_example.json"

@st.cache_resource
def get_comfy_client(workflow: str):
    client = Comfy(workflow)
    print("Connected to ComfyUI Client!")
    return client

def generate_image(client, prompt, neg_prompt, width, height, seed):
    try:
        img = client.get_image(prompt, neg_prompt, width, height, seed)
        return img
    except Exception as e:
        st.error(f"Error generating image, check terminal output {e}")
        return None

st.title("ComfyUI API powered image generator")

prompt = st.text_input("Prompt","")
neg_prompt = st.text_input("Negative prompt","")
col1, col2 = st.columns(2)
with col1:
    width = st.number_input("Width (pixels)", min_value=64, max_value=4096, value=512, step=8)
with col2:
    height = st.number_input("Height (pixels)", min_value=64, max_value=4096, value=512, step=8)
seed_input = st.number_input("Seed", min_value=0, max_value=999999999, value=0, step=1)
randomize = st.checkbox("Use random seed instead", value=False)

if randomize:
    seed = randint(1, 999999999)
else:
    seed = int(seed_input) 

if st.button("Generate image"):
    start = time.perf_counter()
    if not prompt or not prompt.strip():
        st.warning("No prompt entered!")
        pass
    else:
        print(f"Random seed set: {seed}")
        client = get_comfy_client(WORKFLOW)
        with st.spinner("Image generating..."):
            img = generate_image(client, prompt, neg_prompt, width, height, seed)
            if img:
                st.image(img)
                end = time.perf_counter()
                elapsed = end - start
                st.write(f"Time for generation: {elapsed:.6f} seconds")
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
