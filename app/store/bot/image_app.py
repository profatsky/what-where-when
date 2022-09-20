from textwrap import wrap
from io import BytesIO

from PIL import Image, ImageFont, ImageDraw


def get_img_to_send(img: Image) -> bytes:
    """Преобразование Image в bytes"""
    bio = BytesIO()
    img.save(bio, format="png")
    bio.seek(0)
    return bio.getvalue()


def create_image(image_path: str, text: str, author_name: str = None) -> bytes:
    """Создание картинки"""
    background_img = Image.open(image_path)
    draw = ImageDraw.Draw(background_img)
    main_font = ImageFont.truetype("assets/fonts/VelaSans-ExtraBold.ttf", size=24)

    if author_name is not None:
        name_font = ImageFont.truetype("assets/fonts/VelaSans-SemiBold.ttf", size=16)
        draw.text((40, 20), text=f"Автор вопроса: {author_name}", font=name_font, fill="#858362")

    offset = 200
    for line in wrap(text, width=40):
        draw.text((310, offset), line, font=main_font, fill="#F7F6A8", anchor="mm")
        offset += 30

    return get_img_to_send(background_img)
