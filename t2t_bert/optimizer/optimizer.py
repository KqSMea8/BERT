from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import copy
import json
import math
import re
import six
import tensorflow as tf

from optimizer import optimizer_utils

class Optimizer(object):
	def __init__(self, config, **kargs):
		self.config = config
		self.global_step = tf.train.get_or_create_global_step()

		num_warmup_steps = self.config.num_warmup_steps
		global_steps_int = tf.cast(self.global_step, tf.int32)
		warmup_steps_int = tf.constant(num_warmup_steps, dtype=tf.int32)

		self.decay_global_step = tf.cond(global_steps_int < warmup_steps_int,
									lambda:tf.cast(tf.constant(0), tf.int64),
									lambda:self.global_step-tf.cast(tf.constant(warmup_steps_int), tf.int64))

	def lr_decay_fn(self, init_lr, num_train_steps,
					**kargs):
		lr_decay = self.config.get("lr_decay", "polynomial_decay")
		tf.logging.info(" lr decay method {}".format(lr_decay))
		learning_rate = tf.constant(value=init_lr, shape=[], dtype=tf.float32)
		if lr_decay == "polynomial_decay":
			learning_rate = tf.train.polynomial_decay(
													learning_rate,
													self.decay_global_step,
													num_train_steps,
													end_learning_rate=0.0,
													power=1.0,
													cycle=False)
		elif lr_decay == "cosine_decay":
			learning_rate = tf.train.cosin_decay(
													learning_rate,
													self.decay_global_step,
													num_train_steps,
													alpha=0.0,
													cycle=False)
		elif lr_decay == "exponential_decay":
			decay_rate = self.config.get("lr_decay_rate", 0.999)
			learning_rate = tf.train.exponential_decay(
													learning_rate,
													self.decay_global_step,
													num_train_steps,
													decay_rate=decay_rate,
													staircase=False)
		elif lr_decay == "natural_exp_decay":
			decay_rate = self.config.get("lr_decay_rate", 0.999)
			learning_rate = tf.train.natural_exp_decay(
													learning_rate,
													self.decay_global_step,
													num_train_steps,
													decay_rate=decay_rate,
													staircase=False)
		else:
			learning_rate = learning_rate
		return learning_rate

	def warm_up(self, learning_rate, init_lr, **kargs):
		num_warmup_steps = self.config.num_warmup_steps
		global_steps_int = tf.cast(self.global_step, tf.int32)
		warmup_steps_int = tf.constant(num_warmup_steps, dtype=tf.int32)

		global_steps_float = tf.cast(global_steps_int, tf.float32)
		warmup_steps_float = tf.cast(warmup_steps_int, tf.float32)

		warmup_percent_done = global_steps_float / warmup_steps_float
		warmup_learning_rate = init_lr * warmup_percent_done

		is_warmup = tf.cast(global_steps_int < warmup_steps_int, tf.float32)
		learning_rate = (
				(1.0 - is_warmup) * learning_rate + is_warmup * warmup_learning_rate)
		return learning_rate

	def grad_clip_fn(self, loss, tvars, **kargs):
		grads = tf.gradients(loss, tvars)
		grad_clip = self.config.get("grad_clip", "global_norm")
		tf.logging.info(" gradient clip method {}".format(grad_clip))
		if grad_clip == "global_norm":
			clip_norm = self.config.get("clip_norm", 1.0)
			[grads, _] = tf.clip_by_global_norm(grads, 
								clip_norm=clip_norm)
		elif grad_clip == "norm":
			clip_norm = self.config.get("clip_norm", 1.0)
			grads = [tf.clip_by_norm(grad, clip_norm) for grad in grads]
		elif grad_clip == "value":
			clip_min_value = self.config.get("clip_min_value", -1.0)
			clip_max_value = self.config.get("clip_max_value", 1.0)
			grads = [tf.clip_by_value(grad, clip_norm) for grad in grads]
		else:
			grads = grads
		return grads

	def optimizer_op(self, learning_rate,
							**kargs):
		opt_type = self.config.get("train_op", "adam_decay")
		tf.logging.info(" optimization method {}".format(opt_type))
		if opt_type not in ["adam_decay", "adam"]:
			raise NotImplementedError()
		if opt_type == "adam_decay":
			opt = optimizer_utils.AdamWeightDecayOptimizer(
						learning_rate=learning_rate,
						weight_decay_rate=self.config.get("opt_decay_rate", 0.01),
						beta_1=self.config.get("beta_1", 0.9),
						beta_2=self.config.get("beta_2", 0.999),
						epsilon=self.config.get("epsilon", 1e-6),
						exclude_from_weight_decay=["LayerNorm", "layer_norm", "bias"])
		elif opt_type == "adam":
			opt = tf.train.AdamOptimizer(learning_rate,
										beta1=self.config.get("beta_1", 0.9),
										beta2=self.config.get("beta_2", 0.999),
										epsilon=self.config.get("epsilon", 1e-6))
		return opt

	def get_train_op(self, loss, tvars, init_lr, 
							num_train_steps, **kargs):
		learning_rate = self.lr_decay_fn(init_lr, num_train_steps, **kargs)
		learning_rate = self.warm_up(learning_rate, init_lr, **kargs)
		grads = self.grad_clip_fn(loss, tvars, **kargs)
		opt = self.optimizer_op(learning_rate, **kargs)
		train_op = opt.apply_gradients(
					zip(grads, tvars), global_step=self.global_step)
		new_global_step = self.global_step + 1
		train_op = tf.group(train_op, [self.global_step.assign(new_global_step)])
		return train_op