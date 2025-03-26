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
```

### FAQ

- Cloning the model branch gives issues.
  
```
kjha9@en4113732l:~/git/test-git$ git clone -b model git@github.com:CSE546-Cloud-Computing/CSE546-SPRING-2025.git
Cloning into 'CSE546-SPRING-2025'...
remote: Enumerating objects: 269, done.
remote: Counting objects: 100% (269/269), done.
remote: Compressing objects: 100% (236/236), done.
remote: Total 269 (delta 48), reused 220 (delta 17), pack-reused 0 (from 0)
Receiving objects: 100% (269/269), 27.63 MiB | 23.27 MiB/s, done.
Resolving deltas: 100% (48/48), done.
Filtering content: 100% (2/2), 107.67 MiB | 34.53 MiB/s, done.
Encountered 5 files that should have been pointers, but weren't:
        data.pt
        facenet_pytorch/custom/data.pt
        facenet_pytorch/data/onet.pt
        facenet_pytorch/data/pnet.pt
        facenet_pytorch/data/rnet.pt
```

  - **Solution** Try the following sequence of command
    - git lfs uninstall
    - git reset --hard
    - git lfs install
    - git lfs pull
