#
# Used for detecting the feature of AED device, like position and color
# Created by haodong liu
#
import cv2
import numpy as np
from matplotlib import pyplot as plt
import util
import flash_detetor
import time
import color_filter
import stage_pre_main

TAG = "feature_detector"

#
# This is an for
#
area_orange_btn_x = []
area_orange_btn_y = []
global_detected_org_x = 0
global_detected_org_y = 0
global_detected_org_size = 0
last_detected_org_x = 0
last_detected_org_y = 0
last_detected_org_size = 0

# Global variables
static_org_btn_var = 70
dynamic_org_btn_var_x = 200
dynamic_org_btn_var_y = 200
dynamic_org_size = 0
orange_btn_size_min = 1000
orange_btn_size_max = 3000
confidence_counter = 0
position_failed_counter = 0


#
# must be called before using detect_stage_area to set value for orange button size
#
def pre_size_estimate(size_min,size_max):
    global orange_btn_size_min
    global orange_btn_size_max
    orange_btn_size_min = size_min
    orange_btn_size_max = size_max


# def shape_detect(c):
#     shape = "unidentified"
#     peri = cv2.arcLength(c,True)
#     approx = cv2.approxPolyDP(c,0.04 * peri,True)
#     print approx

#
# def angle_cos(p0, p1, p2):
#     d1, d2 = (p0-p1).astype('float'), (p2-p1).astype('float')
#     return abs(np.dot(d1, d2) / np.sqrt( np.dot(d1, d1)*np.dot(d2, d2) ))

def reset():
    global last_detected_org_size
    global last_detected_org_x
    global last_detected_org_y
    last_detected_org_size = 0
    last_detected_org_x = 0
    last_detected_org_y = 0

#
# to estimate the area size of the target is within the range
#
def area_estimate(area,org_size,type):
    area_size_1 = 0
    area_size_2 = 0
    #orange button
    if(type == 1):
        area_size_1 = org_size * 0.8;
        area_size_2 = org_size * 1.5;
    #person hand
    elif type == 2:
        area_size_1 = 12000
        area_size_2 = 120000
    if area > area_size_1 and area < area_size_2:
        return True
    return False


def estimate_org_area_coor(area_size,org_size,x,y,org_x,org_y):
    if abs(x - org_x) > 80:
        return False
    if abs(y - org_y) > 80:
        return False
    if area_size < org_size + 1000 and area_size > org_size - 1000:
        return True
    return False



def estimate_orange_area(area_size,org_size):

    if area_size < org_size + 500 + dynamic_org_size and area_size > org_size - 500 - dynamic_org_size:
        return True
    return False


def determine_orange_btn(array,detected_org_x,detected_org_y):

    to_return1 = []
    min_dis = 100000000
    for cnt1 in array:
            x1, y1, w1, h1 = cv2.boundingRect(cnt1)
            total_x = static_org_btn_var + dynamic_org_btn_var_x
            total_y = static_org_btn_var + dynamic_org_btn_var_y
            if x1 > detected_org_x - total_x and x1 < detected_org_x + total_x:
                if y1 > detected_org_y - total_y and y1 < detected_org_y + total_y:
                    dis = np.abs(x1 - detected_org_x) ** 2 + np.abs(y1 - detected_org_y) ** 2
                    if dis < min_dis:
                        min_dis = dis
                        to_return1 = cnt1
    return to_return1


def determine_yellow_plug(cnts,btn_x,btn_y):
    slope_left = 1
    slope_right = 2
    for cnt in cnts:
        x, y, w, h = cv2.boundingRect(cnt)
        if x != btn_x:
            slope = float(np.abs(y - btn_y)) / float(np.abs(x - btn_x))
            print "slope",str(slope), str(x), str(y)
            if slope > slope_left and slope < slope_right:
                return 1
    return 0


# def detect_start_btn(image1,image2):
#
#     #res1,res2 = color_filter.filter_green(image1,image2)
#     #util.show_two_image(image1,image2)
#     #set it as 300, 550 as testing
#     return 200,550


def detect_hand(image1,image2):

    image1 = cv2.convertScaleAbs(image1)
    image2 = cv2.convertScaleAbs(image2)
    res1, res2 = color_filter.filter_orange(image1, image2)
    # transfer HSV to Binary image for contour detection
    tmp1 = cv2.cvtColor(res1, cv2.COLOR_HSV2BGR)
    tmp2 = cv2.cvtColor(res2, cv2.COLOR_HSV2BGR)
    black1 = cv2.cvtColor(tmp1, cv2.COLOR_BGR2GRAY)
    black2 = cv2.cvtColor(tmp2, cv2.COLOR_BGR2GRAY)
    ret1, thresh1 = cv2.threshold(black1, 0, 255, cv2.THRESH_BINARY)
    ret2, thresh2 = cv2.threshold(black2, 0, 255, cv2.THRESH_BINARY)
    cnts1, hierarchy = cv2.findContours(thresh1.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts2, hierarchy = cv2.findContours(thresh2.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    # cnts1 and cnts2 contain the contour result
    hand_candidate_1 = []
    hand_candidate_2 = []
    #util.show_image("hand",res2,640,320)
    x2 = 0
    y2 = 0
    for cnt in cnts1:
        area0 = cv2.contourArea(cnt)
        cnt_len = cv2.arcLength(cnt, True)
        cnt = cv2.approxPolyDP(cnt, 0.02 * cnt_len, True)
        if area_estimate(area0, 2):
            print area0
            x1, y1, w1, h1 = cv2.boundingRect(cnt)
            print x1, y1, w1, h1
            hand_candidate_1.append(cnt)
    #print "------------first"
    for cnt in cnts2:
        cnt_len = cv2.arcLength(cnt, True)
        area0 = cv2.contourArea(cnt)
        cnt = cv2.approxPolyDP(cnt, 0.02 * cnt_len, True)
        if area_estimate(area0, 2):
            print area0
            x2, y2, w2, h2 = cv2.boundingRect(cnt)
            print x2, y2, w2, h2
            hand_candidate_2.append(cnt)
    #print '------------second'
    return x2, y2



def detect_orange_btn(image1, image2, org_pos_x, org_pos_y, org_size, show_type = 0):

    global dynamic_org_size
    global last_detected_org_size

    print org_pos_x,org_pos_y,org_size

    if last_detected_org_size != 0:
        dynamic_org_size = org_size - last_detected_org_size
    last_detected_org_size = org_size

    res1,res2 = color_filter.filter_orange(image1,image2)
    #tmp1 = cv2.cvtColor(res1, cv2.COLOR_HSV2BGR)
    tmp2 = cv2.cvtColor(res2, cv2.COLOR_HSV2BGR)
    #black1 = cv2.cvtColor(tmp1, cv2.COLOR_BGR2GRAY)
    black2 = cv2.cvtColor(tmp2, cv2.COLOR_BGR2GRAY)
    #ret1, thresh1 = cv2.threshold(black1, 0, 255, cv2.THRESH_BINARY)
    ret2, thresh2 = cv2.threshold(black2, 0, 255, cv2.THRESH_BINARY)
    #cnts1, hierarchy = cv2.findContours(thresh1.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts2, hierarchy = cv2.findContours(thresh2.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    # cnts1 and cnts2 contain the contour result
    #org_btn_candidate_1 = []
    org_btn_candidate_2 = []

    #util.debug_print(TAG,"detect_orange_btn img1")
    # for cnt in cnts1:
    #     area0 = cv2.contourArea(cnt)
    #     cnt_len = cv2.arcLength(cnt, True)
    #     cnt = cv2.approxPolyDP(cnt, 0.02 * cnt_len, True)
    #     if estimate_orange_area(area0, org_size):
    #         x1, y1, w1, h1 = cv2.boundingRect(cnt)
    #         util.debug_print(TAG, "size1 " + str(area0) + " x " + str(x1) +" y "+ str(y1))
    #         org_btn_candidate_1.append(cnt)

    util.debug_print(TAG,"detect_orange_btn img2")
    for cnt in cnts2:
        cnt_len = cv2.arcLength(cnt, True)
        #area0 = cv2.contourArea(cnt)
        cnt = cv2.approxPolyDP(cnt, 0.02 * cnt_len, False)
        area0 = cv2.contourArea(cnt)
        if area0 > 1000:
            x1, y1, w1, h1 = cv2.boundingRect(cnt)
            util.debug_print(TAG, "test " + str(area0) + " x " + str(x1) + " y " + str(y1))
        if estimate_orange_area(area0, org_size):
            x1, y1, w1, h1 = cv2.boundingRect(cnt)
            util.debug_print(TAG, "size2 " + str(area0) + " x " + str(x1) +" y "+ str(y1))
            org_btn_candidate_2.append(cnt)

    if len(org_btn_candidate_2) == 0:
        # thinking if is because size variant too much
        for cnt in cnts2:
            cnt_len = cv2.arcLength(cnt, True)
            # area0 = cv2.contourArea(cnt)
            cnt = cv2.approxPolyDP(cnt, 0.02 * cnt_len, False)
            area0 = cv2.contourArea(cnt)
            x1, y1, w1, h1 = cv2.boundingRect(cnt)
            if estimate_org_area_coor(area0, org_size,x1,y1,org_pos_x,org_pos_y):
                org_btn_candidate_2.append(cnt)

    #cnt1 = determine_orange_btn(org_btn_candidate_1, org_pos_x, org_pos_y)
    cnt2 = determine_orange_btn(org_btn_candidate_2, org_pos_x, org_pos_y)

    if show_type == 1:
        util.show_two_image(image2,res2)
    if show_type == 2:
        util.show_image("orange_btn_1",image2)
        util.show_image("orange_btn_2",res2)

    #if len(cnt1) == 0 or len(cnt2) == 0:
    if len(cnt2) == 0:
        return org_pos_x, org_pos_y,org_size,False
    x2, y2, w2, h2 = cv2.boundingRect(cnt2)
    area0 = cv2.contourArea(cnt2)
    return x2,y2,area0,True



def detect_yellow_plug(image1, image2, org_pos_x, org_pos_y, org_size, show_type = 0):

    util.debug_print(TAG,"detect_yellow_plug "+str(org_pos_x)+" "+str(org_pos_y))
    print org_pos_x,org_pos_y
    global position_failed_counter
    #
    # if last_detected_org_x == 0 and last_detected_org_y == 0:
    #     dynamic_org_btn_var_x = 0
    #     dynamic_org_btn_var_y = 0
    # else:
    #     dynamic_org_btn_var_x = abs(org_pos_x - last_detected_org_x)
    #     dynamic_org_btn_var_y = abs(org_pos_y - last_detected_org_y)
    #     if dynamic_org_btn_var_x == 0 and dynamic_org_btn_var_y == 0:
    #         position_failed_counter += 1
    #     else:
    #         position_failed_counter = 0
    # last_detected_org_x = org_pos_x
    # last_detected_org_y = org_pos_y

    x2, y2, org_size, is_success = detect_orange_btn(image1, image2, org_pos_x, org_pos_y, org_size, show_type)
    if is_success == False:
        return 0, org_pos_x, org_pos_y, org_size

    if position_failed_counter > 10:
        #find the orange button again
        is_prepared = stage_pre_main.prepare(image1,image2)
        if is_prepared:
            x2,y2,org_size = stage_pre_main.retrieve_org_btn_params()
        return 0,x2,y2, org_size

    res1,res2 = color_filter.filter_orange(image1,image2)
    # # transfer HSV to Binary image for contour detection
    #tmp1 = cv2.cvtColor(res1, cv2.COLOR_HSV2BGR)
    tmp2 = cv2.cvtColor(res2, cv2.COLOR_HSV2BGR)
    # black1 = cv2.cvtColor(tmp1, cv2.COLOR_BGR2GRAY)
    black2 = cv2.cvtColor(tmp2, cv2.COLOR_BGR2GRAY)
    # ret1, thresh1 = cv2.threshold(black1, 0, 255, cv2.THRESH_BINARY)
    ret2, thresh2 = cv2.threshold(black2, 0, 255, cv2.THRESH_BINARY)
    # cnts1, hierarchy = cv2.findContours(thresh1.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts2, hierarchy = cv2.findContours(thresh2.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    # # cnts1 and cnts2 contain the contour result
    # org_btn_candidate_1 = []
    org_btn_candidate_2 = []

    # for cnt in cnts1:
    #     area0 = cv2.contourArea(cnt)
    #     cnt_len = cv2.arcLength(cnt, True)
    #     cnt = cv2.approxPolyDP(cnt, 0.02 * cnt_len, True)
    #     if area_estimate(area0,1):
    #         print area0
    #         x1, y1, w1, h1 = cv2.boundingRect(cnt)
    #         print x1,y1,w1,h1
    #         org_btn_candidate_1.append(cnt)
    util.debug_print(TAG,"detect_yellow_plug")
    for cnt in cnts2:
        cnt_len = cv2.arcLength(cnt, True)
        area0 = cv2.contourArea(cnt)
        cnt = cv2.approxPolyDP(cnt, 0.02 * cnt_len, True)
        if area_estimate(area0, org_size,  1):
            print area0
            x1, y1, w1, h1 = cv2.boundingRect(cnt)
            print x1, y1, w1, h1
            org_btn_candidate_2.append(cnt)

    #cnt1 = determine_orange_btn(org_btn_candidate_1,org_pos_x,org_pos_y)
    #cnt2 = determine_orange_btn(org_btn_candidate_2,org_pos_x,org_pos_y)

    # if length of cnt1 == 0 or length of cnt2 == 0, means two image detect orange btn wrong
    #if len(cnt1) == 0 or len(cnt2) == 0:
     #   return 0,org_pos_x,org_pos_y

    #x1, y1, w1, h1 = cv2.boundingRect(cnt1)
    #result1 = determine_yellow_plug(org_btn_candidate_1,x1,y1)
    #x2, y2, w2, h2 = cv2.boundingRect(cnt2)
    result2 = determine_yellow_plug(org_btn_candidate_2,x2,y2)

    #if result1 == 1 and result2 == 1:
    if result2 == 1:
        global confidence_counter
        confidence_counter += 1
    if confidence_counter > 10:
        cv2.imwrite("plug.jpg",image2)
        cv2.imwrite("plug-gray.jpg",res2)
        return 1,x2,y2, org_size
    return 0,x2,y2, org_size
