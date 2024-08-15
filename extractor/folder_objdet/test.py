import torch
from ultralytics import YOLO
# Load the file
model = YOLO("D:\\stuff\\9 RFEX-website-master\\RFEX-website-master\\extractor\\folder_objdet\\model.pt")
pt_file = torch.load(model)


# Print the head of the file
print(pt_file[:5])