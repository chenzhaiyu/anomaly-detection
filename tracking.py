#! encoding: UTF-8

import cv2
import yolo_small
import global_manager as gm
import numpy as np
from optical_flow import detect_motion

from optical_flow import FIRST_FRAME_SAVE_PATH,NEW_FRAME_SAVE_PATH

# YOLO config
yolo = yolo_small.YOLO()
yolo.is_show_console = False
yolo.is_show_image = False
yolo.to_image_file = None
yolo.to_text_file = None
yolo.is_write_image = False
yolo.is_write_text = False
yolo.is_return_cvmat = True

# set global variables
HIST_DIFF_THRESHOLD = 0.999
GREY_DIFF_THRESHOLD = 5000
PRE_FRAME_COUNT_THRESHOLD = 280
FRAMES_PER_PATCH = 20


global thresh
thresh = 0


def try_trigger(current_frame, last_frame, frame_count, mode='ABS_DIFFERENCE'):
    """
    set tracking trigger condition
    :param current_frame: current frame
    :param last_frame: last frame
    :param frame_count: current frame count
    :param mode: mode to trigger the detection procedure
    :return: None
    """

    # using the absolute difference as trigger condition
    if mode == 'ABS_DIFFERENCE':
        gray_current_frame = cv2.resize(cv2.blur(cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY), (10, 10)), (300, 200))
        if last_frame is not None:
            gray_last_frame = cv2.resize(cv2.blur(cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY), (10, 10)), (300, 200))
        else:
            gray_last_frame = gray_current_frame

        gray_current_frame=gray_current_frame[20:-20,:]
        gray_last_frame=gray_last_frame[20:-20,:]

        grey_difference = gray_current_frame - gray_last_frame
        grey_difference = cv2.medianBlur(grey_difference, 5)

        cv2.imwrite("precapture/diff.jpg",grey_difference)
        print '---difference: ' + str(np.sum(np.sum(np.abs(grey_difference)), axis=0)) + '---'

        global GREY_DIFF_THRESHOLD

        # reinitialize threshold when pressing the key 't'
        if 0 < frame_count <= FRAMES_PER_PATCH * 2:
            GREY_DIFF_THRESHOLD = 5000

        # update the threshold
        if frame_count < PRE_FRAME_COUNT_THRESHOLD and np.sum(np.sum(np.abs(grey_difference)), axis=0) > GREY_DIFF_THRESHOLD:
            GREY_DIFF_THRESHOLD = np.sum(np.sum(np.abs(grey_difference)), axis=0)
            print '---\nupdate difference threshold: ' + str(GREY_DIFF_THRESHOLD) + '---\n'

        # finally set the threshold
        elif PRE_FRAME_COUNT_THRESHOLD < frame_count <= PRE_FRAME_COUNT_THRESHOLD + FRAMES_PER_PATCH:
            GREY_DIFF_THRESHOLD = int(1.3 * GREY_DIFF_THRESHOLD)
            print '---\nfinal difference threshold: ' + str(GREY_DIFF_THRESHOLD) + '---\n'

        # trigger the trigger
        elif frame_count > PRE_FRAME_COUNT_THRESHOLD and np.sum(np.sum(np.abs(grey_difference)), axis=0) > GREY_DIFF_THRESHOLD:
            gm.global_manager.set_value('trigger', True)
            print '\n---invasion detection triggered!---\n'
            cv2.imwrite('precapture/current.jpeg', gray_current_frame)
            cv2.imwrite('precapture/last.jpeg', gray_last_frame)

        else:
            pass

    # TODO: change the difference
    elif mode == 'MAX_DIFFERENCE':
        gray_current_frame = cv2.resize(cv2.blur(cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY), (10, 10)), (300, 200))
        if last_frame is not None:
            gray_last_frame = cv2.resize(cv2.blur(cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY), (10, 10)), (300, 200))
        else:
            gray_last_frame = gray_current_frame

        gray_current_frame = gray_current_frame[20:-20, :]
        gray_last_frame = gray_last_frame[20:-20, :]

        grey_difference = gray_current_frame - gray_last_frame
        grey_difference = cv2.medianBlur(grey_difference, 5)

        cv2.imwrite("precapture/diff.jpg", grey_difference)
        print '---difference: ' + str(np.sum(np.sum(np.abs(grey_difference)), axis=0)) + '---'

        global MAX_DIFF_THRESHOLD

        # reinitialize threshold when pressing the key 't'
        if 0 < frame_count <= FRAMES_PER_PATCH * 2:
            MAX_DIFF_THRESHOLD = 5000

        # update the threshold
        if frame_count < PRE_FRAME_COUNT_THRESHOLD and np.sum(np.sum(np.abs(grey_difference)),
                                                              axis=0) > MAX_DIFF_THRESHOLD:
            MAX_DIFF_THRESHOLD = np.sum(np.sum(np.abs(grey_difference)), axis=0)
            print '---\nupdate difference threshold: ' + str(MAX_DIFF_THRESHOLD) + '---\n'

        # finally set the threshold
        elif PRE_FRAME_COUNT_THRESHOLD < frame_count <= PRE_FRAME_COUNT_THRESHOLD + FRAMES_PER_PATCH:
            GREY_DIFF_THRESHOLD = int(1.3 * MAX_DIFF_THRESHOLD)
            print '---\nfinal difference threshold: ' + str(MAX_DIFF_THRESHOLD) + '---\n'

        # trigger the trigger
        elif frame_count > PRE_FRAME_COUNT_THRESHOLD and np.sum(np.sum(np.abs(grey_difference)),
                                                                axis=0) > MAX_DIFF_THRESHOLD:
            gm.global_manager.set_value('trigger', True)
            print '\n---invasion detection triggered!---\n'
            cv2.imwrite('precapture/current.jpeg', gray_current_frame)
            cv2.imwrite('precapture/last.jpeg', gray_last_frame)

        else:
            pass

    # using the hist difference as trigger condition
    elif mode == 'HIST_DIFFERENCE':

        # color convert
        gray_current_frame = cv2.medianBlur(cv2.blur(cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY), (10, 10)), 5)
        if last_frame is not None:
            gray_last_frame = cv2.medianBlur(cv2.blur(cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY), (10, 10)), 5)
        else:
            gray_last_frame = gray_current_frame

        gray_current_frame=gray_current_frame[20:-20, :]
        gray_last_frame=gray_last_frame[20:-20, :]

        # calculate adjacent frames
        current_hist = cv2.calcHist(gray_current_frame, [0], None, [100], [0, 255])  # BGR / GRAY
        if last_frame is None:
            gray_last_frame = gray_current_frame
        last_hist = cv2.calcHist(gray_last_frame, [0], None, [100], [0, 255])

        # compare adjacent frames
        hist_difference = cv2.compareHist(current_hist, last_hist, cv2.HISTCMP_CORREL)
        print '---difference between adjacent frames: ' + str(hist_difference) + '---'

        global HIST_DIFF_THRESHOLD

        # reinitialize threshold when pressing the key 't'
        # TODO: wrong use?
        if 0 < frame_count <= FRAMES_PER_PATCH * 2:
            HIST_DIFF_THRESHOLD = 0.999

        # update threshold
        if frame_count < PRE_FRAME_COUNT_THRESHOLD and hist_difference < HIST_DIFF_THRESHOLD:
            HIST_DIFF_THRESHOLD = hist_difference
            print '---\nupdate hist difference threshold: ' + str(HIST_DIFF_THRESHOLD) + '---\n'

        # finally set the threshold
        elif PRE_FRAME_COUNT_THRESHOLD < frame_count <= PRE_FRAME_COUNT_THRESHOLD + FRAMES_PER_PATCH:
            HIST_DIFF_THRESHOLD = 0.99 * HIST_DIFF_THRESHOLD
            print '---\nfinal hist difference threshold: ' + str(HIST_DIFF_THRESHOLD) + '---\n'

        # trigger the trigger
        elif frame_count > PRE_FRAME_COUNT_THRESHOLD and hist_difference < HIST_DIFF_THRESHOLD:
            gm.global_manager.set_value('trigger', True)
            print '\n---invasion detection triggered!---\n'
            cv2.imwrite('precapture/current.jpeg', gray_current_frame)
            cv2.imwrite('precapture/last.jpeg', gray_last_frame)

        else:
            pass

    # using the optical flow method as the trigger condition
    elif mode == 'OPTICAL_FLOW_DIFFERENCE':
        # TODO: improve the anti-noise performance before applying the method
        # print 'Warning: Triggered with none threshold!\n'
        # gm.global_manager.set_value('trigger', True)

        global thresh

        if frame_count == 0:
            cv2.imwrite(FIRST_FRAME_SAVE_PATH, current_frame)

        else:
            cv2.imwrite(NEW_FRAME_SAVE_PATH, current_frame)

            is_update_thresh = False

            if frame_count < PRE_FRAME_COUNT_THRESHOLD:
                is_update_thresh = True
            else:
                print('\nThreshold finally set\n')

            thresh, is_overflow = detect_motion(FIRST_FRAME_SAVE_PATH, NEW_FRAME_SAVE_PATH, thresh,
                                           is_update_thresh)

            print('\nis_over_flow:' + str(is_overflow) +'\n')

            if is_overflow:
                gm.global_manager.set_value('trigger', True)

    else:
        print 'Warning: Triggered with none threshold!\n'
        gm.global_manager.set_value('trigger', True)


def tracking_core(frame, frame_count, DO_DETECTION=True, DO_WRITE_FILES=True, video_save_path='result/'):
    """
    tracking in every loop, using a single frame to do the detection
    :param frame: input frame
    :param frame_count: current frame count
    :param DO_DETECTION: is do detection or not
    :param DO_WRITE_FILES: is write files or not
    :param video_save_path: detected image save path
    :return: None
    """

    # crop the frame
    frame_size = (640, 640*frame.shape[0]/frame.shape[1])
    frame = cv2.resize(frame, frame_size)

    # if frame_count % 1000 == 0:
    #     print 'Reading new frames: ', status

    params = []

    # firstly clear what(label) every loop
    what = []
    gm.global_manager.set_value('what', what)

    confidence = []
    gm.global_manager.set_value('confidence', confidence)

    if frame_count % FRAMES_PER_PATCH == 0:

        # to do detection and triggered
        if DO_DETECTION and gm.global_manager.get_value('trigger'):

            cvmat, results = yolo.detect_from_cvmat(frame)

            for i in range(len(results)):
                # thresholding confidence value
                if results[i][5] and results[i][5] > 0.0:
                    what.append(results[i][0])
                    confidence.append(results[i][5])

            gm.global_manager.set_value('what', what)
            gm.global_manager.set_value('confidence', confidence)
            new_frame = cv2.resize(frame, (1300, int(1100.0 / frame.shape[1] * frame.shape[0])),
                                   interpolation=cv2.INTER_LINEAR)
            if DO_WRITE_FILES:
                cv2.imwrite(video_save_path + "New_Frame.png", new_frame, params)

        # to do the detection but not triggered
        elif DO_DETECTION and not gm.global_manager.get_value('trigger'):

            # judge if trigger or not
            try_trigger(frame, gm.global_manager.get_value('last_frame'), frame_count, mode='ABS_DIFFERENCE')

            # save last frame for comparison
            last_frame = frame
            gm.global_manager.set_value('last_frame', last_frame)
            new_frame = cv2.resize(frame, (1300, int(1100.0 / frame.shape[1] * frame.shape[0])), interpolation=cv2.INTER_LINEAR)
            if DO_WRITE_FILES:
                cv2.imwrite(video_save_path + "New_Frame.png", new_frame, params)

        else:
            pass
        new_frame = cv2.resize(frame, (1300, int(1100.0 / frame.shape[1] * frame.shape[0])), interpolation=cv2.INTER_LINEAR)
        if not DO_DETECTION and DO_WRITE_FILES:
            cv2.imwrite(video_save_path + "New_Frame.png", new_frame, params)


