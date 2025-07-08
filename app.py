# app.py

import os
import io
from flask import Flask, request, jsonify, render_template
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

app = Flask(__name__)

# --- 模型加载 ---
# 自动获取当前脚本所在目录，保证无论从哪里运行都能找到模型权重
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'saved_models', 'garbage_classifier_mobilenet_v2.pth')
NUM_CLASSES = 2
# 定义类别名称 (必须与训练时文件夹顺序一致)
CLASS_NAMES = ['不可回收垃圾', '可回收垃圾']

# 加载模型结构
model = models.mobilenet_v2(weights=None)
num_ftrs = model.classifier[1].in_features
model.classifier[1] = nn.Linear(num_ftrs, NUM_CLASSES)

# 加载训练好的权重
# 使用 map_location=torch.device('cpu') 确保在没有GPU的机器上也能运行
model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu')))
model.eval()  # 设置为评估模式，这非常重要！

# --- 图像预处理 ---
# 定义与验证时相同的图像变换
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def process_image(image_bytes):
    """处理上传的图像文件"""
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    return transform(image).unsqueeze(0)

# --- Flask 路由 ---
@app.route('/', methods=['GET'])
def index():
    """渲染主页"""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'no file uploaded'}), 400

    file = request.files['file']
    try:
        img_bytes = file.read()
        tensor = process_image(img_bytes)

        with torch.no_grad():
            outputs = model(tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            confidence, predicted_idx = torch.max(probabilities, 1)
            
        predicted_class = CLASS_NAMES[predicted_idx.item()]
        confidence_score = confidence.item()

        return jsonify({
            'class_name': predicted_class,
            'confidence': f'{confidence_score:.2%}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
