import glob
import os
from PIL import Image

INPUT_DIR = 'thumbs'
OUTPUT_DIR = 'anime_dataset'


def get_dir(path):
    dirs = []
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path, item)):
            dirs.append(os.path.join(path, item))

    return dirs


def get_image_path(path):
    return glob.glob(os.path.join(path, '*.png'))


def copy_images(path):

    dir_paths = get_dir(path)
    for d in dir_paths:
        images = get_image_path(d)

        for img_path in images:
            img = Image.open(img_path)
            image_name = img_path.split('/')[-1]
            image_name = image_name.split('.')[0] + ".jpg"

            img.save(os.path.join(OUTPUT_DIR, image_name))

if __name__ == '__main__':
    copy_images(INPUT_DIR)
