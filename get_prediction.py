from keras.preprocessing.image import img_to_array, load_img
import numpy as np

def get_prediction(img, model):
    test_image = load_img(img, target_size=(150, 150))
    test_image = img_to_array(test_image)
    test_image = np.expand_dims(test_image, axis=0)
    result = model.predict(test_image)
    return result[0][0]
