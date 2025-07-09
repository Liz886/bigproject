# train.py

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
from torchvision import datasets, models, transforms
import os
import time


print("PyTorch Version: ", torch.__version__)
print("Torchvision Version: ", torchvision.__version__)

# 1. 定义超参数和数据路径
# 自动获取当前脚本所在目录，保证无论从哪里运行都能找到数据集
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(BASE_DIR, 'dataset')
# 模型将保存到这个文件
MODEL_PATH = os.path.join(BASE_DIR, 'saved_models', 'garbage_classifier_mobilenet_v2.pth')
NUM_CLASSES = 2
BATCH_SIZE = 32
NUM_EPOCHS = 15 # 训练轮次

# 2. 数据预处理和增强
# 定义训练和验证集的数据变换
data_transforms = {
    'train': transforms.Compose([
        transforms.RandomResizedCrop(224), # 随机裁剪并缩放到224x224
        transforms.RandomHorizontalFlip(),   # 随机水平翻转
        transforms.ToTensor(),               # 转换为张量
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]) # 标准化
    ]),
    'val': transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
}

# 3. 加载数据
print("Initializing Datasets and Dataloaders...")
# 使用ImageFolder自动从文件夹结构中加载数据
image_datasets = {x: datasets.ImageFolder(os.path.join(data_dir, x), data_transforms[x]) for x in ['train', 'val']}
 # 创建数据加载器，macOS/Windows建议num_workers=0，Linux可用更高
dataloaders = {x: torch.utils.data.DataLoader(image_datasets[x], batch_size=BATCH_SIZE, shuffle=True, num_workers=0) for x in ['train', 'val']}
dataset_sizes = {x: len(image_datasets[x]) for x in ['train', 'val']}
class_names = image_datasets['train'].classes
print("Class names: ", class_names)

# 4. 设置设备 (GPU优先)
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print("Using device: ", device)

# 5. 定义模型 (迁移学习)
# 加载一个预训练的MobileNetV2模型
model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
# 冻结所有预训练的层
for param in model.parameters():
    param.requires_grad = False

# 替换最后的全连接层，以匹配我们的类别数量 (2类)
num_ftrs = model.classifier[1].in_features
model.classifier[1] = nn.Linear(num_ftrs, NUM_CLASSES)
model = model.to(device)

# 6. 定义损失函数和优化器
criterion = nn.CrossEntropyLoss()
# 只优化我们新添加的分类器层的参数
optimizer = optim.Adam(model.classifier[1].parameters(), lr=0.001)

# 7. 训练和验证
def train_model(model, criterion, optimizer, num_epochs=25):
    since = time.time()
    best_acc = 0.0

    for epoch in range(num_epochs):
        print(f'Epoch {epoch}/{num_epochs - 1}')
        print('-' * 10)

        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()
            else:
                model.eval()

            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]

            print(f'{phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                print(f"New best validation accuracy: {best_acc:.4f}. Saving model...")
                torch.save(model.state_dict(), MODEL_PATH)

    time_elapsed = time.time() - since
    print(f'Training complete in {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s')
    print(f'Best val Acc: {best_acc:4f}')


if __name__ == "__main__":
    train_model(model, criterion, optimizer, num_epochs=NUM_EPOCHS)
