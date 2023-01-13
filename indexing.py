import configparser
import pathlib
import os

def get_data_path(path):
    data_path = pathlib.Path(path)
    if not data_path.exists():
        if not data_path.parent.exists():
            get_data_path(data_path.parent)
        data_path.mkdir(exist_ok=True)
    return path

def load_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    
    cache_path = get_data_path(config.get("DATA_PATH", "cache_path"))
    feature_path = get_data_path(config.get("DATA_PATH", "feature_path"))
    feature_file_ext = get_data_path(config.get("DATA_PATH", "feature_file_ext"))
    uploaded_path = get_data_path(config.get("DATA_PATH", "uploaded_path"))
    pdf_image_path = get_data_path(config.get("DATA_PATH", "pdf_image_path"))
    
    i = 0
    folder_list = []
    try:
        while config.get("FOLDERS", str(i)):
            value = config.get("FOLDERS", str(i))
            folder_list.append(value)
            i += 1
    except configparser.NoOptionError:
        pass
    
    i = 0
    type_list = []
    try:
        while config.get("TYPES", str(i)):
            value = config.get("TYPES", str(i))
            type_list.append(value)
            i += 1
    except configparser.NoOptionError:
        pass
    
    return (cache_path, feature_path, feature_file_ext, uploaded_path, pdf_image_path, folder_list, type_list)


import numpy as np  # manipulating array
from keras_preprocessing import image as kimage   # read image, resize image               
from feature_extractor import FeatureExtractor


# Path of image folder
def path_and_image_nparray(path):
    images_np = np.zeros(shape=(1, 224, 224, 3))
    images_path = []
    
    try:
        img = kimage.load_img(path, target_size = (224, 224)) # resize image to 224x224x3
        images_np[0] = kimage.img_to_array(img, dtype = np.float32) # change uint8 => float32 [0, 1] for easy caculating
        images_path.append(path)
        
    except Exception:
        print("error: ", path)
    
    return np.array(images_path), images_np       # return path of image and array of that image


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
        pdf_file_name = pdf_image_path + pdf_filename_body + "_{:02d}".format(i + 1) + ".png"
        page.save(pdf_file_name, "PNG")
        image_file_list.append(pdf_file_name)
    return image_file_list


if __name__ == "__main__":
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

    (cache_path, feature_path, feature_file_ext, uploaded_path, pdf_image_path, folder_list, type_list) = load_config("./config.ini")
    
    file_list = get_file_list(folder_list, type_list)
    fe = FeatureExtractor()
    
    path_feature_list = []
    image_feature_list = []
    source_path_feature_list = []
    i = 0
    for file in file_list:
        i += 1
        print(f"[{round(i/len(file_list)*100)}%] {i}/{len(file_list)}: {file}")
        target_file_list = []
        if get_file_ext(file) == ".pdf":
            target_file_list = copy_pdf2image(file)
        else:
            target_file_list.append(file)
        for target_file in target_file_list:
            image_path, image_np = path_and_image_nparray(target_file)
            if not image_path in path_feature_list:
                path_feature_list.extend(image_path)
                image_feature_list.extend(fe.extract(image_np))
                src_file_list = []
                src_file_list.append(file)
                source_path_feature_list.extend(np.array(src_file_list))

    # Save feature
    np.savez_compressed(feature_path, array_1 = np.array(path_feature_list), array_2 = np.array(image_feature_list), array_3 = np.array(source_path_feature_list))

