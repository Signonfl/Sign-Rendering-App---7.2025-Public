import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import math
import base64

st.title("Custom Sign Design App")

# Step 1: Upload building photo
uploaded_file = st.file_uploader("Upload photo of the building", type=["jpg", "jpeg", "png"])
if uploaded_file:
    building_img = Image.open(uploaded_file)
    st.image(building_img, caption="Uploaded Building Photo", use_column_width=True)

    # Step 2: Scale the photo using known dimensions
    st.header("Scale the Photo")
    st.write("Enter the real-world height (in inches) of a known object in the photo (e.g., door = 80\"). Then, provide pixel coordinates for two points on that object.")
    real_height = st.number_input("Real height (inches)", min_value=1.0, value=80.0)
    point1_x = st.number_input("Point 1 X (pixels)", min_value=0, value=0)
    point1_y = st.number_input("Point 1 Y (pixels)", min_value=0, value=0)
    point2_x = st.number_input("Point 2 X (pixels)", min_value=0, value=100)
    point2_y = st.number_input("Point 2 Y (pixels)", min_value=0, value=100)

    if st.button("Calculate Scale"):
        pixel_dist = math.hypot(point2_x - point1_x, point2_y - point1_y)
        if pixel_dist > 0:
            ppi = pixel_dist / real_height
            st.session_state.ppi = ppi
            st.success(f"Scale calculated: {ppi:.2f} pixels per inch")
        else:
            st.error("Points must be different.")

    # Step 3: Design the sign
    if 'ppi' in st.session_state:
        st.header("Design the Sign")
        sign_text = st.text_input("Sign text", "Your Sign Here")
        font_size_real = st.number_input("Sign height (inches)", min_value=1.0, value=48.0)
        font_name = st.selectbox("Font", ["arial.ttf", "times.ttf", "courier.ttf"])  # Add more fonts if needed
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
            dim_bbox = draw.textbbox((0, 0), dim_text, font=ImageFont.truetype("arial.ttf", 20))
            dim_width = dim_bbox[2] - dim_bbox[0]
            draw.text(((sign_img.width - dim_width) / 2, text_height + 15), dim_text, font=ImageFont.truetype("arial.ttf", 20), fill="#000000")

            st.image(sign_img, caption="Sign Preview", use_column_width=False)

            # Download sign as PNG
            buf = io.BytesIO()
            sign_img.save(buf, format="PNG")
