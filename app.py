import os
import uuid
import open_clip
import torch
from flask import Flask, request, render_template, send_from_directory
from PIL import Image
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
CLIPPED_FOLDER = 'image_scraper/images/clipped'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 初始化OpenCLIP模型
model = open_clip.create_model('ViT-B-32', pretrained='openai')
preprocess = open_clip.image_transform(model.visual.image_size, is_train=False)

# 初始化Qdrant客户端
qdrant_client = QdrantClient(host='localhost', port=6333)
collection_name = 'image_vectors'

# 检查集合是否存在，如果不存在则创建
if not qdrant_client.collection_exists(collection_name=collection_name):
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=rest.VectorParams(size=model.visual.output_dim, distance=rest.Distance.COSINE),
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    if file and allowed_file(file.filename):
        filename = save_file(file)
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # 加载图片并进行预处理
        image = Image.open(image_path).convert('RGB')
        image = preprocess(image).unsqueeze(0)  # Add batch dimension

        # 获取图片向量
        with torch.no_grad():
            image_features = model.encode_image(image).numpy().flatten().tolist()

        print(f'图片向量: {image_features}')

        # 在Qdrant中搜索相似图片
        search_result = qdrant_client.search(
            collection_name=collection_name,
            query_vector=image_features,
            limit=5  # 设置返回的结果数量
        )

        # 获取相似图片的文件名
        similar_images = [hit.payload['file_name'] for hit in search_result]

        print(f'搜索结果: {similar_images}')
        
        return render_template('result.html', images=similar_images)
    return "File not allowed", 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/clipped/<filename>')
def clipped_file(filename):
    return send_from_directory(CLIPPED_FOLDER, filename)

def allowed_file(filename):
    return '.' in filename and filename.lower().rsplit('.', 1)[1] in {'png', 'jpg', 'jpeg', 'bmp', 'gif'}

def save_file(file):
    filename = f"{uuid.uuid4()}.{file.filename.rsplit('.', 1)[1].lower()}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    return filename

if __name__ == '__main__':
    app.run(debug=True)
