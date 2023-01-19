import configparser

## Loading config file
def load_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    
    cache_path = config.get("DATA_PATH", "cache_path")
    feature_path = config.get("DATA_PATH", "feature_path") + config.get("DATA_PATH", "feature_file_ext")
    uploaded_path = config.get("DATA_PATH", "uploaded_path")
    pdf_image_path = config.get("DATA_PATH", "pdf_image_path")
    
    return (cache_path, feature_path, uploaded_path)

import numpy as np
from PIL import Image
from feature_extractor import FeatureExtractor
from datetime import datetime
from flask import Flask, request, render_template
from keras_preprocessing import image as kimage

app = Flask(__name__)
fe = FeatureExtractor()

# Define Cosine Similarity function
def cosine_similarity(query, X):
    norm_2_query = np.sqrt(np.sum(query*query))
    norm_2_X = np.sqrt(np.sum(X*X, axis=-1))
    return np.sum(query*X, axis=-1)/(norm_2_query*norm_2_X)

(cache_path, feature_path, uploaded_path) = load_config("./config.ini")

import shutil

# Define result of retrieving image
def retrieval_images(query_vector, image_feature_list, source_path_feature_list):
    values = cosine_similarity(query_vector, image_feature_list) # caculate cosine similarity between query and features in database
    id_s = np.argsort(-values)[:20] # Getting top 20 nearest results
    return_list = []
    for id in id_s:
        file = path_feature_list[id]
        # copied_file = cache_path + pathlib.Path(file).name
        copied_file = cache_path + file.replace('\\', '_')
        shutil.copy2(file, copied_file)
        return_list.append((round(values[id]*100, 2), file, copied_file, source_path_feature_list[id]))
    return return_list

data = np.load(feature_path)
path_feature_list = data["array_1"]
image_feature_list = data["array_2"]
source_path_feature_list = data["array_3"]

@app.route("/", methods = ["GET", "POST"])

def index():
    print(source_path_feature_list)
    if request.method == "POST":
        file = request.files["query_img"]
        
        # Save query image from Flask server into static/image_uploaded/
        img = Image.open(file.stream)
        uploaded_file = uploaded_path + datetime.now().isoformat().replace(":", ".") + "_" + file.filename
        img.save(uploaded_file)
        
        # Load query image and FeatureExtractor
        query = kimage.load_img(uploaded_file, target_size=(224, 224))
        query = kimage.img_to_array(query, dtype = np.float32)
        query_vector = fe.extract(query[None, :])  
        
        scores = retrieval_images(query_vector, image_feature_list, source_path_feature_list)
        return render_template("index.html", query_path = uploaded_file, scores = scores)
    
    return render_template("index.html")


if __name__ == "__main__":
    app.run()