# -*- coding: utf-8 -*-
import sys,os

import tensorflow as tf
import os
try:
	from .train_eval_sess_fn import train_eval_fn as sess_fn
	from .train_eval_estimator_fn import train_eval_fn as estimator_fn
except:
	from train_eval_sess_fn import train_eval_fn as sess_fn
	from train_eval_estimator_fn import train_eval_fn as estimator_fn

import horovod.tensorflow as hvd

def monitored_sess(FLAGS,
				worker_count, 
				task_index, 
				cluster, 
				is_chief, 
				target,
				init_checkpoint,
				train_file,
				dev_file,
				checkpoint_dir):

	sess_fn(FLAGS,
			worker_count, 
			task_index, 
			is_chief, 
			target,
			init_checkpoint,
			train_file,
			dev_file,
			checkpoint_dir,
			FLAGS.is_debug)

def monitored_estimator(FLAGS,
				worker_count, 
				task_index, 
				cluster, 
				is_chief, 
				target,
				init_checkpoint,
				train_file,
				dev_file,
				checkpoint_dir):
	
	estimator_fn(FLAGS,
				worker_count, 
				task_index, 
				is_chief, 
				target,
				init_checkpoint,
				train_file,
				dev_file,
				checkpoint_dir,
				FLAGS.is_debug)