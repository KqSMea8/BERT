CUDA_VISIBLE_DEVICES="" python export_model.py \
 --config_file "/data/xuht/chinese_L-12_H-768_A-12/bert_config.json" \
 --model_dir "/data/xuht/LCQMC/restore_model" \
 --label2id "/data/xuht/LCQMC/label_dict.json" \
 --init_checkpoint "/data/xuht/LCQMC/restore_model/oqmrc_4.ckpt" \
 --max_length 128 \
 --export_path "/data/xuht/LCQMC/export" \
 --export_type "2"