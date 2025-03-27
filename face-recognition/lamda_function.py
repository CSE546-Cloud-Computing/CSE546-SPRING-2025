import os
import time
import json
import boto3
import torch
import base64
import numpy as np
from facenet_pytorch import MTCNN
from PIL import Image, ImageDraw, ImageFont

class face_recognition:

    def face_recognition_func(self, model_path, model_wt_path, face_img_path):

        # Step 1: Load image as PIL
        face_pil = Image.open(face_img_path).convert("RGB")
        key      = os.path.splitext(os.path.basename(face_img_path))[0].split(".")[0]

        # Step 2: Convert PIL to NumPy array (H, W, C) in range [0, 255]
        face_numpy = np.array(face_pil, dtype=np.float32)  # Convert to float for scaling

        # Step 3: Normalize values to [0,1] and transpose to (C, H, W)
        face_numpy /= 255.0  # Normalize to range [0,1]

        # Convert (H, W, C) → (C, H, W)
        face_numpy = np.transpose(face_numpy, (2, 0, 1))

        # Step 4: Convert NumPy to PyTorch tensor
        face_tensor = torch.tensor(face_numpy, dtype=torch.float32)

        saved_data = torch.load(model_wt_path)  # loading resnetV1_video_weights.pt

        self.resnet = torch.jit.load(model_path) # this uses the model trace. resnetV1.pt

        if face_tensor != None:
            emb             = self.resnet(face_tensor.unsqueeze(0)).detach()  # detech is to make required gradient false
            embedding_list  = saved_data[0]  # getting embedding data
            name_list       = saved_data[1]  # getting list of names
            dist_list       = []  # list of matched distances, minimum distance is used to identify the person

            for idx, emb_db in enumerate(embedding_list):
                dist = torch.dist(emb, emb_db).item()
                dist_list.append(dist)

            idx_min = dist_list.index(min(dist_list))
            return name_list[idx_min]
        else:
            print(f"No face is detected")
            return
