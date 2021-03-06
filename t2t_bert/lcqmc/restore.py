import sys,os
sys.path.append("..")

import numpy as np
import tensorflow as tf
from bunch import Bunch
from data_generator import tokenization
from data_generator import hvd_distributed_tf_data_utils as tf_data_utils
from model_io import model_io
from example import feature_writer, write_to_tfrecords
import json

flags = tf.flags

FLAGS = flags.FLAGS

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

## Required parameters

flags.DEFINE_string(
	"meta", None,
	"The config json file corresponding to the pre-trained BERT model. "
	"This specifies the model architecture.")

flags.DEFINE_string(
	"input_checkpoint", None,
	"Input TF example files (can be a glob or comma separated).")

flags.DEFINE_string(
	"output_checkpoint", None,
	"Input TF example files (can be a glob or comma separated).")

flags.DEFINE_string(
	"log_directory", None,
	"Input TF example files (can be a glob or comma separated).")

flags.DEFINE_string(
	"output_meta_graph", None,
	"Input TF example files (can be a glob or comma separated).")

def main(_):

	graph = tf.Graph()
	with graph.as_default():
		import json

		sess = tf.Session(config=tf.ConfigProto(allow_soft_placement=True, 
                                        log_device_placement=True))
				
		saver = tf.train.import_meta_graph(FLAGS.meta, clear_devices=True)
		# saver = tf.train.import_meta_graph(FLAGS.meta)
		print("==succeeded in loading meta graph==")
		saver.restore(sess, FLAGS.input_checkpoint)
		print("==succeeded in loading model==")
		saver.save(sess, FLAGS.output_checkpoint)
		print("==succeeded in restoring model==")
		saver.export_meta_graph(FLAGS.output_meta_graph, clear_devices=True)

if __name__ == "__main__":
	tf.app.run()


