import sys,os
sys.path.append("..")

from data_generator import tf_data_utils
from data_generator import data_processor
from data_generator.tokenization import WordpieceTokenizer
from data_generator import tokenization
from data_generator import data_feature_classifier

import csv
import json
import collections
import tensorflow as tf
import numpy as np

import random

import pandas as pd
import re, json
from hanziconv import HanziConv
from flash_text import KeywordProcessor

def full2half(s):
	n = []
	for char in s:
		num = ord(char)
		if num == 0x3000:
			num = 32
		elif 0xFF01 <= num <= 0xFF5E:
			num -= 0xfee0
		num = chr(num)
		n.append(num)
	return ''.join(n)

def clean(text):
	text = text.strip()
	text = HanziConv.toSimplified(text)
	text = full2half(text)
	text = re.sub("\\#.*?#|\\|.*?\\||\\[.*?]", "", text)
	text = re.sub("\s*", "", text)
	return text

class RuleMatch(object):
	def __init__(self, config={}):
		self.config = config
		self.rule_match_api = KeywordProcessor()	

	def load(self):
		with open(self.config["rule_path"], "r") as frobj:
			self.rule_data = json.load(frobj)

	def add_rule(self, tokenizer):
		for item in self.rule_data:
			self.rule_match_api.add_keyword(tokenizer.tokenize(item["word"]), [item["label"]])

	def parse(self, sentence_lst, background_label="正常"):
		output_lst = self.rule_match_api.extract_keywords(sentence_lst,
                                                   span_info=True)

		rule_type_lst = [[background_label]]*len(sentence_lst)
		for item in output_lst:
			start_pos = item[1]
			end_pos = item[-1]
			for t in range(start_pos, end_pos):
				rule_type_lst[t] = item[0]

		return rule_type_lst


class BertRuleClassifierProcessor(data_processor.DataProcessor):
	def get_labels(self, label_file):
		import json
		with tf.gfile.Open(label_file, "r") as f:
			label_mappings = json.load(f)
			self.label2id = label_mappings["label2id"]

	def _read_data(self, input_file):
		with tf.gfile.Open(input_file, "r") as f:
			lines = []
			for line in f:
				lines.append(line.strip())
			return lines

	def _create_examples(self, lines,
									LABEL_SPLITTER="__label__"):


		re_pattern = "({}{})".format(LABEL_SPLITTER, "\d.")

		examples = []
		for (i, line) in enumerate(lines):
			guid = i
			element_list = re.split(re_pattern, line)
			text_a = clean(element_list[-1])
			input_labels = clean(element_list[1]).split(LABEL_SPLITTER)[-1]

			text_a = tokenization.convert_to_unicode(text_a)
			input_labels = [label.strip() for label in input_labels if label.strip() in list(self.label2id.keys())]
			
			examples.append(data_feature_classifier.InputExample(
					guid=guid,
					text_a=text_a,
					text_b=None,
					label=input_labels
				))
		return examples

	def get_train_examples(self, train_file):
		lines = self._read_data(train_file)
		examples = self._create_examples(lines)
		random.shuffle(examples)
		return examples

	def get_dev_examples(self, dev_file):
		lines = self._read_data(dev_file)
		examples = self._create_examples(lines)
		random.shuffle(examples)
		return examples

class EvaluationProcessor(data_processor.DataProcessor):
	def get_labels(self, label_file):
		import json
		with tf.gfile.Open(label_file, "r") as f:
			label_mappings = json.load(f)
			self.label2id = label_mappings["label2id"]

	def _read_data(self, input_file):
		import _pickle as pkl
		frequent_phrases = pkl.load(open(input_file, "rb"))["frequent_phrases"]
		return frequent_phrases

	def _create_examples(self, frequent_phrases):

		examples = []
		for (i, line) in enumerate(frequent_phrases):
			guid = i
			text_a = clean(line[0])
			input_labels = ["0"]

			text_a = tokenization.convert_to_unicode(text_a)
			input_labels = [label.strip() for label in input_labels if label.strip() in list(self.label2id.keys())]
			
			examples.append(data_feature_classifier.InputExample(
					guid=guid,
					text_a=text_a,
					text_b=None,
					label=input_labels
				))
		return examples

	def get_train_examples(self, train_file):
		lines = self._read_data(train_file)
		examples = self._create_examples(lines)
		return examples

	def get_dev_examples(self, dev_file):
		lines = self._read_data(dev_file)
		examples = self._create_examples(lines)
		return examples
