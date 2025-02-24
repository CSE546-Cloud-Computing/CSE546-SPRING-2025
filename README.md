## Face Recognition Model Repository with Inference Code and Pretrained Weights

### Folder structure:
 - facenet_pytorch: This is a repository for Inception Resnet (V1) models in pytorch, pretrained on VGGFace2 and CASIA-Webface. 
 - face_recognition.py: Model Inference code 
 - data.pt: Saved model weights 

### Prerequisites
  - You need to install the PyTorch CPU version to use the code.
    ```
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    ```

### Sample Output:

```
(cse546) kjha9@en4113732l:~/git/Project-1/part-2/model$ python3 face_recognition.py ../../face_images_1000/test_000.jpg
Paul
(cse546) kjha9@en4113732l:~/git/Project-1/part-2/model$
