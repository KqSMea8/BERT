python data_processor.py \
	--train_file "/data/xuht/jd_comment/train.txt" \
	--test_file "/data/xuht/jd_comment/test.txt" \
	--train_result_file "/data/xuht/jd_comment/train" \
	--test_result_file  "/data/xuht/jd_comment/test" \
	--vocab_file "/data/xuht/chinese_L-12_H-768_A-12/vocab.txt" \
	--label_id "/data/xuht/porn/label_dict.json" \
	--lower_case True \
	--max_length 128 \
	--num_threads 10 \
	--max_predictions_per_seq 5 \
	--log_cycle 1000 \
	--feature_type "pretrain_classification" \
	--masked_lm_prob 0.15 \
	--dupe 10
