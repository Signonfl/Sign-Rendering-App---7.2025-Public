import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import math
import base64
from streamlit_drawable_canvas import st_canvas

st.title("Custom Sign Design App")

# Define font paths (using liberation fonts as alternatives)
font_paths = {
    "Arial-like (Liberation Sans)": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "Times-like (Liberation Serif)": "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "Courier-like (Liberation Mono)": "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"
}

# Step 1: Upload building photo
uploaded_file = st.file_uploader("Upload photo of the building", type=["jpg", "jpeg", "png"])
if uploaded_file:
    building_img = Image.open(uploaded_file)
    st.image(building_img, caption="Uploaded Building Photo", use_column_width=True)

    # Step 2: Scale the photo using known dimensions
    st.header("Scale the Photo")
    st.write("Draw a line on the image below to select the height of a known object (e.g., a door). Then enter its real height in inches.")
    
    # Drawable canvas for selecting points
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Semi-transparent orange for drawing
        stroke_width=3,
        stroke_color="#FF0000",  # Red line
        background_image=building_img,
        update_streamlit=True,
        height=building_img.height if building_img.height < 600 else 600,  # Limit height for usability
        drawing_mode="line",
        key="canvas"
    )

    real_height = st.number_input("Real height of selected object (inches)", min_value=1.0, value=80.0)

    if st.button("Calculate Scale") and canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]
        if len(objects) > 1:  # Background is object 0, drawn line is object 1
            line = objects[1]
            if line["type"] == "line":
                x1, y1 = line["x1"], line["y1"]
                x2, y2 = line["x2"], line["y2"]
                pixel_dist = math.hypot(x2 - x1, y2 - y1)
                if pixel_dist > 0:
                    # Adjust for canvas scaling if image was resized
                    scale_factor = building_img.width / canvas_result.image_data.width
                    pixel_dist *= scale_factor
                    ppi = pixel_dist / real_height
                    st.session_state.ppi = ppi
                    st.success(f"Scale calculated: {ppi:.2f} pixels per inch")
                else:
                    st.error("Draw a line with length > 0.")
            else:
                st.error("Please draw a line on the image.")
        else:
            st.error("Please draw a line on the image.")

    # Step 3: Design the sign
    if 'ppi' in st.session_state:
        st.header("Design the Sign")
        sign_text = st.text_input("Sign text", "Your Sign Here")
        font_size_real = st.number_input("Sign height (inches)", min_value=1.0, value=48.0)
        font_choice = st.selectbox("Font", list(font_paths.keys()))
        font_name = font_paths[font_choice]
        color = st.color_picker("Text color", "#000000")
        stroke = st.checkbox("Add stroke (outline)")
        stroke_color = st.color_picker("Stroke color", "#FFFFFF") if stroke else None
        letter_spacing = st.slider("Letter spacing (pixels)", 0, 20, 0)

        # Render sign graphic
        if sign_text:
            pixel_height = font_size_real * st.session_state.ppi
            font = ImageFont.truetype(font_name, int(pixel_height))

            # Calculate text size
            draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
            bbox = draw.textbbox((0, 0), sign_text, font=font, spacing=letter_spacing)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            sign_img = Image.new("RGBA", (text_width + 20, text_height + 20), (0, 0, 0, 0))
            draw = ImageDraw.Draw(sign_img)

            # Draw stroke if enabled
            if stroke:
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        if dx == 0 and dy == 0:
                            continue
                        draw.text((10 + dx, 10 + dy), sign_text, font=font, fill=stroke_color, spacing=letter_spacing)

            # Draw main text
            draw.text((10, 10), sign_text, font=font, fill=color, spacing=letter_spacing)

            # Attach measurements
            real_width = text_width / st.session_state.ppi
            dim_text = f"Height: {font_size_real}\" Width: {real_width:.2f}\""
            dim_font = ImageFont.truetype(font_paths["Arial-like (Liberation Sans)"], 20)
            dim_bbox = draw.textbbox((0, 0), dim_text, font=dim_font)
            dim_width = dim_bbox[2] - dim_bbox[0]
            draw.text(((sign_img.width - dim_width) / 2, text_height + 15), dim_text, font=dim_font, fill="#000000")

            st.image(sign_img, caption="Sign Preview", use_column_width=False)

            # Download sign as PNG
            buf = io.BytesIO()
            sign_img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            href = f'<a href="data:image/png;base64,{b64}" download="sign.png">Download Sign Graphic</a>'
            st.markdown(href, unsafe_allow_html=True)

        # Step 4: Overlay on building
        st.header("Overlay Sign on Building")
        position_x = st.slider("Horizontal position (%)", 0, 100, 50)
        position_y = st.slider("Vertical position (%)", 0, 100, 50)
        scale_factor = st.slider("Sign scale (%)", 50, 200, 100) / 100

        if st.button("Generate Overlay"):
            overlay_img = building_img.copy()
            sign_resized = sign_img.resize((int(sign_img.width * scale_factor), int(sign_img.height * scale_factor)))
            pos_x = int((position_x / 100) * (overlay_img.width - sign_resized.width))
            pos_y = int((position_y / 100) * (overlay_img.height - sign_resized.height))
            overlay_img.paste(sign_resized, (pos_x, pos_y), sign_resized)
            st.image(overlay_img, caption="Final Rendering", use_column_width=True)

            # Download final image
            buf = io.BytesIO()
            overlay_img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            href = f'<a href="data:image/png;base64,{b64}" download="rendering.png">Download Final Rendering</a>'
            st.markdown(href, unsafe_allow_html=True)

# Note: For more advanced drag-and-drop, consider integrating JavaScript via Streamlit components.