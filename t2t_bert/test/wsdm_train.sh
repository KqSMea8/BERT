python test_wsdm.py \
 --eval_data_file "/data/xuht/wsdm19/test.csv" \
 --output_file "/data/xuht/wsdm19/data/dev.tfrecords" \
 --config_file "/data/xuht/bert/chinese_L-12_H-768_A-12/bert_config.json" \
 --init_checkpoint "/data/xuht/bert/chinese_L-12_H-768_A-12/bert_model.ckpt" \
 --result_file "/data/xuht/wsdm19/data_11_17/model_11_15/submission.csv" \
 --vocab_file "/data/xuht/bert/chinese_L-12_H-768_A-12/vocab.txt" \
 --label_id "/data/xuht/wsdm19/data/label_dict.json" \
 --train_file "/data/xuht/wsdm19/data/train.tfrecords" \
 --dev_file "/data/xuht/wsdm19/data/dev.tfrecords" \
 --max_length 100 \
 --model_output "/data/xuht/wsdm19/data/model_11_21" \
 --gpu_id "1"