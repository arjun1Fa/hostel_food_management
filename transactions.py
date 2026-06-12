from paddleocr import PaddleOCR as pd
import paddle

import os
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_pir_api"] = "0"

def read_transaction(file_name):
   
    oc=pd(use_textline_orientation=True,lang='en',device='cpu',enable_mkldnn=False)
    result=oc.predict(file_name)
    print(result[0]["rec_texts"])



filename=r"C:\mealsync\images\gpay\1.jpeg"
print("Paddle file:", paddle.__file__)
print("Version:", paddle.__version__)
print(dir(paddle)[:30])

print(hasattr(paddle, "device"))
read_transaction(filename)