#!/usr/bin/env python3

import shutil
import requests
import base64
from datetime import datetime

outdir = "./out/"

data = {
  "enable_hr": "false",
  "denoising_strength": 0,
  "firstphase_width": 0,
  "firstphase_height": 0,
  "hr_scale": 2,
  "hr_upscaler": "string",
  "hr_second_pass_steps": 0,
  "hr_resize_x": 0,
  "hr_resize_y": 0,
  "prompt": "red hair, tall, woman, kneeling, wet hair, swimsuit",
  "styles": [
  ],
  "seed": -1,
  "subseed": -1,
  "subseed_strength": 0,
  "seed_resize_from_h": -1,
  "seed_resize_from_w": -1,
  "batch_size": 1,
  "n_iter": 1,
  "steps": 25,
  "cfg_scale": 8,
  "width": 512,
  "height": 512,
  "restore_faces": "false",
  "tiling": "false",
  "negative_prompt": "((((ugly)))), (((duplicate))), ((morbid)), ((mutilated)), extra fingers, mutated hands, ((poorly drawn hands)), ((poorly drawn face)), (((mutation))), (((deformed))), blurry, ((bad anatomy)), (((bad proportions))), ((extra limbs)), cloned face, (((disfigured))), gross proportions, (malformed limbs), ((missing arms)), ((missing legs)), (((extra arms))), (((extra legs))), mutated arms, (((long neck))), melting faces, long neck, flat color, flat shading, (bad legs), one leg, extra leg, (bad face), (bad eyes), ((bad hands, bad feet, missing fingers, cropped:1.0)), worst quality, jpeg artifacts, signature, (((watermark))), (username), blurry, ugly, old, wide face, ((fused fingers)), ((too many fingers)), amateur drawing, odd, fat, out of frame, (cloned face:1.3), (mutilated:1.3), (deformed:1.3), (gross proportions:1.3), (disfigured:1.3), (mutated hands:1.3), (bad hands:1.3), (extra fingers:1.3), long neck, extra limbs, broken limb, asymmetrical eyes, necklace, drawn, ((mutilated)), [out of frame], mutated hands, Photoshop, tiling, poorly drawn hands, poorly drawn feet, poorly drawn face, out of frame, mutation, mutated, extra limbs, extra legs, extra arms, disfigured, deformed, cross-eye, body out of frame, blurry, bad art, bad anatomy, 3d render",
  "eta": 0,
  "s_churn": 0,
  "s_tmax": 0,
  "s_tmin": 0,
  "s_noise": 1,
  "override_settings": {
    "sd_model_checkpoint": "protogenV22.E0YS.safetensors [16e33692]"
  },
  "override_settings_restore_afterwards": "false",
  "script_args": [],
  "sampler_name": "DPM++ SDE Karras",
  "sampler_index": "DPM++ SDE Karras"
}

url = 'https://user:aiIsReallyCool!@ai.benshoshan.com/sdapi/v1/txt2img'

r = requests.post(url, stream=True, json=data)
if r.status_code == 200:
    data = r.json()
    image_date = datetime.now().strftime("%Y-%m-%dT%H%M")
    image_name = data['parameters']['prompt'].replace(" ","_")
    filename = outdir + image_date + "+" + image_name + ".png"
    imageData = data['images'][0]
    image = base64.b64decode(imageData)
    out_file = open(filename, 'wb')
    out_file.write(image)
    out_file.close()
else:
    print("Something went wrong: [{status}]".format(status=r.status_code))

del r
