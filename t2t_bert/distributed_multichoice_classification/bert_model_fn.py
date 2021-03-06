import sys, os
from distributed_encoder.bert_encoder import bert_encoder
from model_io import model_io
from task_module import classifier
import tensorflow as tf
from metric import tf_metrics

def model_fn_builder(
					model_config,
					num_labels,
					init_checkpoint,
					model_reuse=None,
					load_pretrained=True,
					model_io_fn=None,
					optimizer_fn=None,
					model_io_config={},
					opt_config={},
					exclude_scope="",
					not_storage_params=[],
					target="a",
					label_lst=None):

	def model_fn(features, labels, mode):

		if target:
			input_ids = features["input_ids_{}".format(target)]
			input_mask = features["input_mask_{}".format(target)]
			segment_ids = features["segment_ids_{}".format(target)]
		else:
			input_ids = features["input_ids"]
			input_mask = features["input_mask"]
			segment_ids = features["segment_ids"]

		input_shape = bert_utils.get_shape_list(input_ids, expected_rank=3)
		batch_size = input_shape[0]
		choice_num = input_shape[1]
		seq_length = input_shape[2]

		if target:
			real_features = {
				"input_ids_{}".format(target):tf.reshape(input_ids, [batch_size*choice_num, seq_length]),
				"input_mask_{}".format(target):tf.reshape(input_mask, [batch_size*choice_num, seq_length]),
				"segment_ids_{}".format(target):tf.reshape(segment_ids, [batch_size*choice_num, seq_length]),
				"label_ids":features["label_ids"]
			}
		else:
			real_features = {
				"input_ids":tf.reshape(input_ids, [batch_size*choice_num, seq_length]),
				"input_mask":tf.reshape(input_mask, [batch_size*choice_num, seq_length]),
				"segment_ids":tf.reshape(segment_ids, [batch_size*choice_num, seq_length]),
				"label_ids":features["label_ids"]
			}

		if mode == tf.estimator.ModeKeys.TRAIN:
			dropout_prob = model_config.dropout_prob
		else:
			dropout_prob = 0.0

		model = bert_encoder(model_config, real_features, labels,
							mode, target, reuse=model_reuse)

		if model_io_config.fix_lm == True:
			scope = model_config.scope + "_finetuning"
		else:
			scope = model_config.scope

		with tf.variable_scope(scope, reuse=reuse):
			(loss, 
				per_example_loss, 
				logits) = classifier.multi_choice_classifier(model_config,
											model.get_pooled_output(),
											num_labels,
											label_ids,
											dropout_prob)

		tvars = model_io_fn.get_params(scope, 
								not_storage_params=not_storage_params)
		if load_pretrained:
			model_io_fn.load_pretrained(tvars, 
										init_checkpoint,
										exclude_scope=exclude_scope)
		model_io_fn.set_saver(var_lst=tvars)

		if mode == tf.estimator.ModeKeys.TRAIN:
			model_io_fn.print_params(tvars, string=", trainable params")
			update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
			with tf.control_dependencies(update_ops):
				train_op = optimizer_fn.get_train_op(loss, tvars, 
								opt_config.init_lr, 
								opt_config.num_train_steps)

				estimator_spec = tf.estimator.EstimatorSpec(mode=mode, 
								loss=loss, train_op=train_op)
				return {
							"estimator_spec":estimator_spec, 
							"train":{
										"loss":loss, 
										"logits":logits,
										"train_op":train_op
									}
						}
		elif mode == tf.estimator.ModeKeys.PREDICT:
			print(logits.get_shape(), "===logits shape===")
			pred_label = tf.argmax(logits, axis=-1, output_type=tf.int32)
			prob = tf.nn.softmax(logits)
			max_prob = tf.reduce_max(prob, axis=-1)
			
			estimator_spec = tf.estimator.EstimatorSpec(
									mode=mode,
									predictions={
												'pred_label':pred_label,
												"max_prob":max_prob
								  	},
									export_outputs={
										"output":tf.estimator.export.PredictOutput(
													{
														'pred_label':pred_label,
														"max_prob":max_prob
													}
												)
								  	}
						)
			return {
						"estimator_spec":estimator_spec 
					}

		elif mode == tf.estimator.ModeKeys.EVAL:
			def metric_fn(per_example_loss,
						logits, 
						label_ids):
				"""Computes the loss and accuracy of the model."""
				sentence_log_probs = tf.reshape(
					logits, [-1, logits.shape[-1]])
				sentence_predictions = tf.argmax(
					logits, axis=-1, output_type=tf.int32)
				sentence_labels = tf.reshape(label_ids, [-1])
				sentence_accuracy = tf.metrics.accuracy(
					labels=label_ids, predictions=sentence_predictions)
				sentence_mean_loss = tf.metrics.mean(
					values=per_example_loss)
				sentence_f = tf_metrics.f1(label_ids, 
										sentence_predictions, 
										num_labels, 
										label_lst, average="macro")

				eval_metric_ops = {
									"f1": sentence_f,
									"loss": sentence_mean_loss,
									"acc":sentence_accuracy
								}

				return eval_metric_ops

			eval_metric_ops = metric_fn( 
							per_example_loss,
							logits, 
							label_ids)
			
			estimator_spec = tf.estimator.EstimatorSpec(mode=mode, 
								loss=loss,
								eval_metric_ops=eval_metric_ops)
			return {
						"estimator_spec":estimator_spec, 
						"eval":{
							"per_example_loss":per_example_loss,
							"logits":logits
						}
					}
		else:
			raise NotImplementedError()
	return model_fn