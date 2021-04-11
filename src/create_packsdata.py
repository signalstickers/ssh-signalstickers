from io import BytesIO
import json
import subprocess
import zipfile

from PIL import Image
import anyio
from signalstickers_client import StickersClient

with open("packs.json", "r") as f:
    packs = json.load(f)

out_zip = zipfile.ZipFile("packs.zip", "a")


packs_info = []

if "packsinfo.json" in out_zip.namelist():
    with out_zip.open("packsinfo.json") as f_packinfo:
        packs_info = json.load(f_packinfo)


def make_asciiart(input_img):
    """
    Adapted from https://github.com/RameshAditya/asciify
    """
    ASCII_CHARS = [" ", ".", ":", ";", "+", "*", "?", "%", "S", "#", "@"]

    def resize(image, new_width):
        """
        method resize():
            - takes as parameters the image, and the final width
            - resizes the image into the final width while maintaining aspect ratio
        """
        new_height = 8
        new_dim = (new_width, new_height)
        new_image = image.resize(new_dim)
        return new_image

    def grayscalify(image):
        """
        method grayscalify():
            - takes an image as a parameter
            - returns the grayscale version of image
        """
        return image.convert("L")

    def modify(image, buckets=25):
        """
        method modify():
            - replaces every pixel with a character whose intensity is similar
        """
        initial_pixels = list(image.getdata())
        new_pixels = [
            ASCII_CHARS[pixel_value // buckets] for pixel_value in initial_pixels
        ]
        return "".join(new_pixels)

    image = Image.open(BytesIO(input_img))
    image = resize(image, 15)
    image = grayscalify(image)

    pixels = modify(image)
    len_pixels = len(pixels)

    # Construct the image from the character list
    new_image = [pixels[index : index + 15] for index in range(0, len_pixels, 15)]

    return "\n".join(new_image)


async def get_pack_thumbnails(pack_id, pack_key):

    async with StickersClient() as client:
        pack = await client.get_pack(pack_id, pack_key)

    thumbs_list = []

    async with anyio.create_task_group() as tg:
        for sticker in pack.stickers:
            thumbs_list.append(make_asciiart(sticker.image_data))

    return thumbs_list, make_asciiart(pack.cover.image_data)


for index, pack in enumerate(packs):

    if f'{pack["meta"]["id"]}.json' in out_zip.namelist():
        continue

    print(".", end="", flush=True)
    pack_index = {
        "title": pack["manifest"]["title"],
        "id": pack["meta"]["id"],
    }

    if pack.get("meta", []).get("tags"):
        pack_index["tags"] = "".join(pack["meta"]["tags"]).lower()

    pack_out = {
        "id": pack["meta"]["id"],
        "key": pack["meta"]["key"],
        "title": pack["manifest"]["title"],
        "author": pack["manifest"]["author"],
    }

    for key in ["source", "original", "animated", "nsfw", "tags"]:
        if pack.get("meta", []).get(key):
            pack_out[key] = pack["meta"][key]

            if key in ["original", "animated", "nsfw"]:
                pack_index[key] = pack["meta"][key]

    try:
        pack_out["thumbs"], pack_index["cover"] = anyio.run(
            get_pack_thumbnails, pack["meta"]["id"], pack["meta"]["key"]
        )
    except:
        # Probably 403 in a sticker pack
        continue

    out_zip.writestr(
        zipfile.ZipInfo(f'{pack["meta"]["id"]}.json'),
        json.dumps(
            pack_out,
            indent=None,
            separators=(",", ":"),
            ensure_ascii=True,
            sort_keys=True,
        ),
        zipfile.ZIP_DEFLATED,
        9,
    )

    packs_info.append(pack_index)


out_zip.close()


# Remove packinfos
try:
    subprocess.run(["zip", "-d", "packs.zip", "packsinfo.json"])
except:
    pass

out_zip = zipfile.ZipFile("packs.zip", "a")

out_zip.writestr(
    zipfile.ZipInfo(f"packsinfo.json"),
    json.dumps(
        packs_info,
        indent=None,
        separators=(",", ":"),
        ensure_ascii=True,
        sort_keys=True,
    ),
    zipfile.ZIP_DEFLATED,
    9,
)

out_zip.close()
