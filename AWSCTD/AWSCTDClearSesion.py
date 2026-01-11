from tensorflow.python.keras.backend import set_session
from tensorflow.python.keras.backend import clear_session
from tensorflow.python.keras.backend import get_session
import tensorflow as tf
import gc

# Reset Keras Session
def reset_keras():
	sess = get_session()
	clear_session()
	sess.close()
	sess = get_session()

	print(gc.collect()) # if it's done something you should see a number being outputted

	# use the same config as you used to create the session
	config = tf.compat.v1.ConfigProto()
	config.gpu_options.per_process_gpu_memory_fraction = 1
	config.gpu_options.visible_device_list = "0"
	set_session(tf.compat.v1.Session(config=config))