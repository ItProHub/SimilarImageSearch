import os
import shutil
import open_clip
from PIL import Image
import torch
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

# 初始化OpenCLIP模型
model = open_clip.create_model('ViT-B-32', pretrained='openai')
preprocess = open_clip.image_transform(model.visual.image_size, is_train=False)

# 设置图片文件夹路径
source_folder = 'image_scraper/images/unclip'
destination_folder = 'image_scraper/images/clipped'

# 创建目标文件夹，如果不存在
if not os.path.exists(destination_folder):
    os.makedirs(destination_folder)

# 初始化Qdrant客户端
qdrant_client = QdrantClient(host='localhost', port=6333)

# 创建或获取一个集合
collection_name = 'image_vectors'
qdrant_client.recreate_collection(
    collection_name=collection_name,
    vectors_config=rest.VectorParams(size=model.visual.output_dim, distance=rest.Distance.COSINE),
)

# 遍历图片文件夹中的所有图片
for image_name in os.listdir(source_folder):
    image_path = os.path.join(source_folder, image_name)
    
    # 确保文件是图片
    if os.path.isfile(image_path) and image_name.lower().endswith(('png', 'jpg', 'jpeg', 'bmp', 'gif')):
        # 加载图片并进行预处理
        image = Image.open(image_path).convert('RGB')
        image = preprocess(image).unsqueeze(0)  # Add batch dimension

        # 获取图片向量
        with torch.no_grad():
            image_features = model.encode_image(image).numpy().flatten().tolist()

        # 生成UUID作为ID
        point_id = str(uuid.uuid4())

        # 打印调试信息
        point = rest.PointStruct(
            id=point_id,
            vector=image_features,
            payload={'file_name': image_name}
        )
        print(f'Attempting to insert point: {point}')
        
        # 将向量存储到Qdrant
        try:
            response = qdrant_client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            print(f'Successfully stored image: {image_name} in Qdrant')
        except Exception as e:
            print(f'Failed to store image: {image_name} in Qdrant')
            print(e)

        # 移动图片到目标文件夹
        try:
            shutil.move(image_path, os.path.join(destination_folder, image_name))
            print(f'Successfully moved image: {image_name} to {destination_folder}')
        except Exception as e:
            print(f'Failed to move image: {image_name} to {destination_folder}')
            print(e)
