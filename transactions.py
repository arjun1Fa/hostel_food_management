from paddleocr import PaddleOCR as pd
import paddle
import cv2

import os
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_pir_api"] = "0"
oc=pd(use_textline_orientation=True,lang='en',device='cpu',enable_mkldnn=False)

def read_transaction(file_name):
    pre_image=preprocess_image(file_name)
    result=oc.predict(pre_image)
    return result[0]["rec_texts"]


def preprocess_image(file_name):
    img=cv2.imread(file_name)
    
    pre_image = cv2.GaussianBlur(img, (3,3), 0)
    return pre_image


