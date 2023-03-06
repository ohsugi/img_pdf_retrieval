import PIL
import pillow_avif  # Do not remove this to read AVIF format
import cv2
import tqdm
from config_reader import ConfigReader 
import pathlib
import os
from datetime import datetime
import shutil
import dlib

def get_data_path(path):
    data_path = pathlib.Path(path)
    if not data_path.exists():
        if not data_path.parent.exists():
            get_data_path(data_path.parent)
        data_path.mkdir(exist_ok=True)
    return path

import numpy as np  # manipulating array
from keras_preprocessing import image as kimage # read image, resize image               
from feature_extractor import FeatureExtractor

# Path of image folder
def path_and_image_nparray(path):
    images_np = np.zeros(shape=(1, 224, 224, 3))
    images_path = []
    
    try:
        img = kimage.load_img(path, target_size = (224, 224))   # resize image to 224x224x3
        images_np[0] = kimage.img_to_array(img, dtype = np.float32) # change uint8 => float32 [0, 1] for easy caculating
        images_path.append(path)
        
    except Exception:
        print("error: ", path)
    
    return np.array(images_path), images_np # return path of image and array of that image

def get_file_ext(file):
    return pathlib.Path(file).suffix.lower()

import glob
def get_file_list(folder_list, type_list):
    file_list = []
    for folder in folder_list:
        files = glob.glob(folder + "**", recursive=True)
        for file in files:
            if get_file_ext(file) in type_list:
                file_list.append(file)
    return file_list

from pdf2image import convert_from_path
def copy_pdf2image(file):
    pages = []
    try:
        pages = convert_from_path(str(file), 150)
    except Exception:
        print("Error: ", file)
    
    pdf_filename_body = pathlib.Path(file).stem
    
    image_file_list = []
    for i, page in enumerate(pages):
        pdf_file_name = config.pdf_image_path + pdf_filename_body + "_{:02d}".format(i + 1) + ".png"
        page.save(pdf_file_name, "PNG")
        image_file_list.append(pdf_file_name)
    return image_file_list

def has_face(detector, image_path):
    detected = 0
    try:
        pil_image = PIL.Image.open(image_path, mode='r', formats=None)
        # detected = detector(cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2GRAY), 1)
        detected = detector.detectMultiScale(cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2GRAY), 1.05, 5)
    except:
        return False
    return len(detected) > 0

if __name__ == "__main__":
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    config = ConfigReader()
    
    fe = FeatureExtractor()
    
    path_feature_list = []
    image_feature_list = []
    source_path_feature_list = []
    i = 0

    with tqdm.tqdm(config.get_indexing_file_list()) as pbar_main:
        pbar_main.set_description("Indexing image files")
        # detector = dlib.get_frontal_face_detector()
        detector = cv2.CascadeClassifier("./haarcascade_frontalface_default.xml")

        for file in pbar_main:
            i += 1
            target_file_list = []
            if get_file_ext(file) == ".pdf":
                target_file_list = copy_pdf2image(file)
            else:
                target_file_list.append(file)

            for target_file in target_file_list:
                if config.face_filtering and has_face(detector, target_file):
                    shutil.move(target_file, config.face_included_images_path)
                    continue

                image_path, image_np = path_and_image_nparray(target_file)
                if not image_path in path_feature_list:
                    path_feature_list.extend(image_path)
                    image_feature_list.extend(fe.extract(image_np))
                    src_file_list = []
                    src_file_list.append(file)
                    source_path_feature_list.extend(np.array(src_file_list))

    config.last_checked = datetime.now().strftime('%m/%d/%Y %H:%M %p')

    # Save feature
    np.savez_compressed(config.feature_path, array_1 = np.array(path_feature_list), array_2 = np.array(image_feature_list), array_3 = np.array(source_path_feature_list))

