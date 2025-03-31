#__copyright__   = "Copyright 2025, VISA Lab"
#__license__     = "MIT"

FROM python:3.8-slim
WORKDIR ${LAMBDA_TASK_ROOT}

RUN apt-get update && apt-get install -y cmake ca-certificates libgl1-mesa-glx libglib2.0-0 libsm6 libxrender1 libxext6
RUN python3 -m pip install torch==1.9.0+cpu torchvision==0.10.0+cpu -f https://download.pytorch.org/whl/torch_stable.html

#Install the requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN python3 -m pip install -r requirements.txt

RUN mkdir =p /tmp/.cache
ENV TORCH_HOME=/tmp/.cache/torch
ENV XDG_CACHE_HOME=/tmp/.cache/torch

# COPY the code and model weights
COPY resnetV1_video_weights.pt ${LAMBDA_TASK_ROOT}
COPY handler_face_detection.py ${LAMBDA_TASK_ROOT}
COPY handler_face_recognition.py ${LAMBDA_TASK_ROOT}

ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
#CMD ["handler.handler"]
