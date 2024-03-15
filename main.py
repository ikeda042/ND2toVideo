import nd2reader
import numpy as np
import os
import cv2
from PIL import Image, ImageDraw, ImageFont


def process_image(array):
    """
    画像処理関数：正規化とスケーリングを行う。
    """
    array = array.astype(np.float32)  # Convert to float
    array -= array.min()  # Normalize to 0
    array /= array.max()  # Normalize to 1
    array *= 255  # Scale to 0-255
    return array.astype(np.uint8)


def add_scale_bar(image_path, scale_length_um=10) -> Image.Image:
    """
    画像にスケールバーを追加する関数。
    """

    # Metaparameters
    pixel_size_um = 0.108

    # Load the image
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    width, height = img.size
    bar_width_pixels = scale_length_um / pixel_size_um

    bar_height = 10
    bar_x = width - bar_width_pixels - 50
    bar_y = height - bar_height - 70
    draw.rectangle(
        [bar_x, bar_y, bar_x + bar_width_pixels, bar_y + bar_height], fill="white"
    )

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


def extract_nd2(file_name: str, target_view: int):
    """
    指定した視野のnd2ファイルを連番画像として出力する。
    """
    try:
        os.mkdir("nd2totiff")
    except FileExistsError:
        pass
    try:
        os.mkdir("nd2totiff_processed")
    except FileExistsError:
        pass

    with nd2reader.ND2Reader(file_name) as images:
        # 利用可能な軸とサイズをチェック
        print(f"Available axes: {images.axes}")
        print(f"Sizes: {images.sizes}")

        if "v" not in images.axes:
            raise ValueError(
                "The specified ND2 file does not contain 'v' axis for multiple views."
            )

        images.iter_axes = "t"  # タイムラプス用の軸を設定
        images.bundle_axes = "yx"  # 'c' 軸がない場合の標準設定
        images.default_coords["v"] = target_view  # 特定の視野を選択

        for n, img in enumerate(images):
            array = np.array(img)
            array = process_image(array)
            image = Image.fromarray(array)
            image.save(f"nd2totiff/{n}.tif")

    for i in range(
        len(
            [
                os.path.join("nd2totiff/", f)
                for f in os.listdir("nd2totiff/")
                if f.endswith(".tif")
            ]
        )
    ):
        img = add_scale_bar(f"nd2totiff/{i}.tif", 10)
        img.save(f"nd2totiff_processed/{i}.tif")
    convert_to_video()


def convert_to_video() -> None:
    """
    連番画像を動画に変換する関数。
    """
    tiff_directory = "nd2totiff_processed/"

    output_video_path = "timelapse_5fps.avi"

    tiff_files = [
        os.path.join(tiff_directory, f)
        for f in os.listdir(tiff_directory)
        if f.endswith(".tif")
    ]
    tiff_files = [f"{tiff_directory}/{n}.tif" for n in range(len(tiff_files)) if n > 4]

    first_image = Image.open(tiff_files[0])
    frame_width, frame_height = first_image.size

    out = cv2.VideoWriter(
        output_video_path,
        cv2.VideoWriter_fourcc("M", "J", "P", "G"),
        5,
        (frame_width, frame_height),
    )

    for tiff_file in tiff_files:
        img = Image.open(tiff_file)
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        out.write(img)

    out.release()


if __name__ == "__main__":
    extract_nd2("timelapse.nd2", target_view=15)
