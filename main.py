import sys
import threading
import time

from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi import FastAPI, Request, status
import urllib

from pydantic import BaseModel
import cv2
import base64
import pickle
import json

camera = cv2.VideoCapture(0)
camera.set(3, 176)
camera.set(4, 144)
app = FastAPI()
frames = []
new_frames = []


class Msg(BaseModel):
    msg: str


def im2json(im):
    """Convert a Numpy array to JSON string"""
    imdata = pickle.dumps(im)
    jstr = json.dumps({"image": base64.b64encode(imdata).decode('ascii')})
    return jstr


def json2im(jstr):
    """Convert a JSON string back to a Numpy array"""
    load = json.loads(jstr)
    imdata = base64.b64decode(load['image'])
    im = pickle.loads(imdata)
    return im


def set_camera(ip):
    global camera
    global Reading
    global change
    global new_frames
    new_frames.clear()
    camera.release()
    Reading = False
    change = True
    camera = cv2.VideoCapture(ip)
    return 'done'


ipcam = ''

Reading = False
change = False

def read_cam():
    global frames
    global new_frames
    global camera
    global Reading
    global change
    i = 0
    if not Reading:
        while True:
            Reading = True
            suc, frame = camera.read()
            if suc:
                new_frames.clear()
                new_frames.append(frame)
                i = i = 1
            if change:
                change = False
                break
                # raise Exception('Change Required'+ipcam)

    Reading = False
    read_cam()

@app.on_event("startup")
async def startup_event():
    x = threading.Thread(target=read_cam)
    x.start()

@app.get("/")
async def root():
    global new_frames
    try:
        import io
        from starlette.responses import StreamingResponse
        # print('frames', new_frames[0])
        cv2img = new_frames[len(new_frames) - 1]
        print(sys.getsizeof(new_frames))
        res, im_png = cv2.imencode(".png", cv2img)
        return StreamingResponse(io.BytesIO(im_png.tobytes()), media_type="image/png")
    except:
        return {'LESA'}


@app.get("/path")
async def demo_get():
    return {"message": "This is /path endpoint, use a post request to transform the text to uppercase"}


@app.post("/path")
async def demo_post(inp: Msg):
    return {"message": inp.msg.upper()}


@app.get("/path/{path_id:path}")
async def demo_get_path_id(path_id: str):
    global ipcam
    global new_frames
    ipcam = path_id
    set_camera(ipcam)
    try:
        print(sys.getsizeof(new_frames))
        return RedirectResponse('/')
    except:
        return {'No Redirect'}
