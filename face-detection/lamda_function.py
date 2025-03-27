import os
import json
import boto3
import base64
import requests
import numpy as np
from facenet_pytorch import MTCNN
from PIL import Image, ImageDraw, ImageFont

class face_detection:
    def __init__(self):
        self.mtcnn          = MTCNN(image_size=240, margin=0, min_face_size=20) # initializing mtcnn for face detection

    def face_detection_func(self, test_image_path, output_path):

        # Step-1: Read the image
        img     = Image.open(test_image_path).convert("RGB")
        img     = np.array(img)
        img     = Image.fromarray(img)

        key = os.path.splitext(os.path.basename(test_image_path))[0].split(".")[0]

        # Step:2 Face detection
        face, prob = self.mtcnn(img, return_prob=True, save_path=None)

        if face != None:

            os.makedirs(output_path, exist_ok=True)

            face_img = face - face.min()  # Shift min value to 0
            face_img = face_img / face_img.max()  # Normalize to range [0,1]
            face_img = (face_img * 255).byte().permute(1, 2, 0).numpy()  # Convert to uint8

            # Convert numpy array to PIL Image
            face_pil        = Image.fromarray(face_img, mode="RGB")
            face_img_path   = os.path.join(output_path, f"{key}_face.jpg")

            # Save face image
            face_pil.save(face_img_path)
            return face_img_path

        else:
            print(f"No face is detected")
            return
