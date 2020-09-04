from keras.models import load_model
from threading import Thread
from keras.preprocessing.image import img_to_array, load_img, array_to_img
import numpy as np
import cv2
import time
import psycopg2 as sq
import requests



our_model = load_model('neural_network/fire_detector_model.h5')
our_model._make_predict_function()
TELEGRAM_USERNAME = 'nestoor22'
SECONDS_BY_PHOTO = 10

SEND_MESSAGE_URL = 'https://api.telegram.org/bot800792656:AAF3UcFpElvjeG3q3b-Q9JjRVSEn_c_Y6JE/'\
                   'sendMessage?chat_id={0}&text=Chance\tof\tfire:\t\t{1}\nCheck\tphoto:\t\t/check'

database = sq.connect('postgres://lzfllcfvvyspsq:ce5e2cb0b0e63af2a6afef0a4077018567ce8638750d9f7'
                      '56c76b86e78255a9c@ec2-54-247-85-251.eu-west-1.compute.amazonaws.com:5432'
                      '/ddmeddrk3fhuln', sslmode='require')
cursor = database.cursor()
try:
    cursor.execute("""SELECT chat_id FROM telegram_user WHERE username = %s""", (TELEGRAM_USERNAME,))
    chat_id = cursor.fetchone()[0]
    cursor.execute("""SELECT chat_id FROM telegram_user WHERE user_referrer = %s""", (chat_id,))
    refferal_ids = cursor.fetchall()
except:
    chat_id = 0
    refferal_ids = []
    database.rollback()
    print("Please, start bot")

class CameraVision(object):
    def __init__(self):
        self.capture = cv2.VideoCapture(0)
        self.cam_live = True

    def start_cam(self):
        self.cam_live = True
        Thread(target=self.show_camera).start()

    def show_camera(self):
        while self.cam_live:
            _, frame = self.capture.read()
            cv2.imshow('FireDetector', frame)
            key = cv2.waitKey(1)
            if (key == 27) or (cv2.getWindowProperty('FireDetector', 1) < 1):
                self.cam_live = False
        cv2.destroyWindow("FireDetector")
        self.cam_live = False

    def save_check_photo(self):
        send_photo_sql = """UPDATE telegram_user SET img = (%s) WHERE chat_id = (%s)"""
        flag, frame = self.capture.read()
        cv2.imwrite('check_photo.jpg', frame)
        im = open('check_photo.jpg', 'rb').read()
        blob_value = sq.Binary(im)
        try:
            cursor.execute(send_photo_sql, (blob_value, chat_id))
            if len(refferal_ids) > 0:
                for id in refferal_ids:
                    cursor.execute(send_photo_sql, (blob_value, id[0]))
            database.commit()
        except:
            database.rollback()

    def check_photo(self):
        while True and self.cam_live:
            time.sleep(SECONDS_BY_PHOTO)
            self.save_check_photo()
            self.make_prediction()

    def start_check_photo(self):
        x = Thread(target=self.check_photo)
        x.daemon = True
        x.start()

    @staticmethod
    def make_prediction():
        # CLASS 0 - FIRE
        # CLASS 1 - NOT FIRE
        test_image = load_img('check_photo.jpg', target_size=(150, 150, 3))
        test_image = img_to_array(test_image)/255
        test_image = np.expand_dims(test_image, axis=0)
        result = 1 - float("{:.2f}".format(our_model.predict(test_image)[0][0]))
        if result > 0.5 and chat_id != 0:
            requests.post(SEND_MESSAGE_URL.format(chat_id, result))
            if len(refferal_ids) > 0:
                for id in refferal_ids:
                    requests.post(SEND_MESSAGE_URL.format(id[0], result))
        return



if __name__ == '__main__':
    x = CameraVision()
    x.start_cam()
    x.start_check_photo()
