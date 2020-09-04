import os, random

start_path = 'D:/FireDetector/dataset'

image_files = [file for file in os.listdir(start_path) if file.endswith('.jpg') or file.endswith('.png')]

num_image = len(image_files)

for i in range(int(num_image*0.15)):
    x = random.choice(image_files)
    os.rename('D:/FireDetector/dataset/{0}'.format(x),'D:/FireDetector/dataset/test/{0}'.format(x))
    image_files.remove(x)

for i in range(int(num_image*0.7)):
    x = random.choice(image_files)
    os.rename('D:/FireDetector/dataset/{0}'.format(x),'D:/FireDetector/dataset/train/{0}'.format(x))
    image_files.remove(x)

for i in range(int(num_image*0.15)):
    x = random.choice(image_files)
    os.rename('D:/FireDetector/dataset/{0}'.format(x),'D:/FireDetector/dataset/validate/{0}'.format(x))
    image_files.remove(x)