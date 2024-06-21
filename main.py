import pims
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
import os

def process_image(array):
    array = array.astype(np.float32)
    array -= array.min()
    array /= array.max()
    array *= 255
    return array.astype(np.uint8)

def add_scale_bar(image_path, scale_length_um=10):
    pixel_size_um = 0.108
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    width, height = img.size
    bar_width_pixels = scale_length_um / pixel_size_um
    bar_height = 10
    bar_x = width - bar_width_pixels - 50
    bar_y = height - bar_height - 70
    draw.rectangle([bar_x, bar_y, bar_x + bar_width_pixels, bar_y + bar_height], fill="white")
    textsize = 50
    try:
        font = ImageFont.truetype("Arial Unicode.ttf", textsize)
    except IOError:
        font = ImageFont.load_default()
    text = f"{scale_length_um} um"
    text_width = draw.textlength(text, font=font)
    text_x = bar_x + (bar_width_pixels - text_width) / 2
    text_y = bar_y + bar_height - 10
    draw.text((text_x, text_y), text, fill="white", font=font)
    return img

def extract_nd2(file_name: str):
    try:
        os.mkdir("nd2totiff")
    except FileExistsError:
        pass
    try:
        os.mkdir("nd2totiff_processed")
    except FileExistsError:
        pass

    images = pims.open(file_name)
    
    # Display available axes and sizes
    print(f"Available axes: {images.sizes.keys()}")
    print(f"Sizes: {images.sizes}")

    for n, img in enumerate(images):
        array = np.array(img)
        array = process_image(array)
        image = Image.fromarray(array)
        image.save(f"nd2totiff/{n}.tif")

    for i in range(len([f for f in os.listdir("nd2totiff/") if f.endswith(".tif")])):
        img = add_scale_bar(f"nd2totiff/{i}.tif", 10)
        img.save(f"nd2totiff_processed/{i}.tif")
    convert_to_video()

def convert_to_video():
    tiff_directory = "nd2totiff_processed/"
    output_video_path = "timelapse_5fps.avi"
    tiff_files = [os.path.join(tiff_directory, f) for f in os.listdir(tiff_directory) if f.endswith(".tif")]
    tiff_files = [f"{tiff_directory}/{n}.tif" for n in range(len(tiff_files)) if n > 4]
    first_image = Image.open(tiff_files[0])
    frame_width, frame_height = first_image.size
    out = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc("M", "J", "P", "G"), 5, (frame_width, frame_height))
    for tiff_file in tiff_files:
        img = Image.open(tiff_file)
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        out.write(img)
    out.release()

if __name__ == "__main__":
    extract_nd2(r"d:\0619ATPtri.nd2")
