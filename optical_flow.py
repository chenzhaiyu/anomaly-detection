# Author: Zhangkai 2018

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import numpy as np
from PIL import Image
import time
import pyflow
import cv2

# rtmp://live.hkstv.hk.lxdns.com/live/hks

NEW_FRAME_SAVE_PATH="result/New_Frame.png"
FIRST_FRAME_SAVE_PATH="result/First_Frame.png"


def save_frame(is_first_frame,frame):
    """
    save frame

    :param is_first_frame: bool type(true or false).
    :param frame: np.array. video frame to be saved.
    :return: None
    """

    frame=cv2.resize(frame,(int(400/frame.shape[0]*frame.shape[1]),400),interpolation=cv2.INTER_LINEAR)
    cv2.imwrite(NEW_FRAME_SAVE_PATH,frame)
    if is_first_frame:
        cv2.imwrite(FIRST_FRAME_SAVE_PATH,frame)


def detect_motion(first_frame_path, current_frame_path,thresh,updateThresh=False):
    """
    :param first_frame_path: string. save path of first frame
    :param current_frame_path: string. save path of current frame
    :param thresh: double. warning threshold
    :param updateThresh: bool. Whether to update threshold. Default is false.
    :return:
        thresh: double. the updated thresh
        True/False: bool. whether there is distinct motion
    """

    # convert uchar to float(0-1)
    tim1 = Image.open(first_frame_path)
    tim2 = Image.open(current_frame_path)
    im1=tim1.resize((400,int(400/tim1.size[0]*tim1.size[1])))
    im2=tim2.resize((400,int(400/tim2.size[0]*tim2.size[1])))
    im1=np.array(im1)
    im2=np.array(im2)
    im1 = im1.astype(float) / 255.
    im2 = im2.astype(float) / 255.

    # Flow Options
    alpha = 0.012
    ratio = 0.75
    min_width = 20
    outer_frame_per_iteration = 7
    inner_frame_per_iteration = 1
    sor_iterations = 30
    color_type = 0  # 0 or default:RGB, 1:GRAY (but pass gray image with shape (h,w,1))

    # optical flow estimation
    s = time.time()
    u, v, image_to_write = pyflow.coarse2fine_flow(
        im1, im2, alpha, ratio, min_width, outer_frame_per_iteration, inner_frame_per_iteration,
        sor_iterations, color_type)
    e = time.time()
    print('Time Taken: %.2f seconds for image of size (%d, %d, %d)' % (
        e - s, im1.shape[0], im1.shape[1], im1.shape[2]))
    flow = np.concatenate((u[..., None], v[..., None]), axis=2)

    # calculate changed distance
    change_map=np.sqrt(u*u+v*v)
    print("max change is %f"%change_map.max())

    # save the optical flow image
    hsv = np.zeros(im1.shape, dtype=np.uint8)
    hsv[:, :, 0] = 255
    hsv[:, :, 1] = 255

    # convert Kartesian coordinates to polar coordinates
    mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    hsv[..., 0] = ang * 180 / np.pi / 2
    hsv[..., 2] = cv2.normalize(mag, None, 0, 150, cv2.NORM_MINMAX)
    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    new_rgb=cv2.resize(rgb,(1300,int(1100.0/rgb.shape[1]*rgb.shape[0])),interpolation=cv2.INTER_LINEAR)
    cv2.imwrite('result/flow.png', new_rgb)
    # cv2.imwrite('examples/car2Warped_new.jpg', image_to_write[:, :, ::-1] * 255)

    if np.any(change_map>thresh):
        if not updateThresh:
            print("warning")
            print("displacement has over the threshold")
            return thresh, True
        else:
            thresh=change_map.max()*1.2
            return thresh, False
    return thresh, False


if __name__=="__main__":
    pass
