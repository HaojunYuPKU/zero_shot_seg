# sudo bash local.sh \
# configs/segmenter/segmenter-propagate_vit-b16_512x512_40k_bs16_prior_1.0_lambda_0.0_downsample_2_pairwise_affinity_cam_thre_0.7_pa_thre_0.9_in21k_ade_filter_vild_v2_prior_0.05_loss_weight_0.05_mix_batch_coco-stuff164k_imagenet21k_local.py \
# --auto-resume
# configs/segmenter/segmenter-propagate_vit-b16_512x512_40k_bs16_prior_1.0_lambda_0.0_downsample_2_pairwise_affinity_cam_thre_0.9_pa_thre_0.95_in21k_ade_filter_vild_v2_prior_0.05_loss_weight_0.05_mix_batch_coco-stuff164k_imagenet21k_local.py
# configs/segmenter/segmenter-propagate_vit-b16_512x512_40k_bs16_prior_1.0_lambda_0.0_downsample_2_in21k_ade_filter_vild_v2_prior_0.05_loss_weight_0.05_mix_batch_coco-stuff164k_imagenet21k_local.py
# configs/segmenter/segmenter-propagate_vit-b16_512x512_40k_bs16_prior_1.0_lambda_0.0_downsample_2_in21k_ade_filter_vild_v2_prior_0.05_loss_weight_0.1_mix_batch_coco-stuff164k_imagenet21k_local.py

sudo bash local.sh \
configs/segmenter/segmenter-propagate_vit-b16_512x512_40k_bs8_downsample_4_base_config_prompt_learning_shape_16_0_lrm_1e-1_wd_1e-3_local.py

# sudo bash local.sh \
# configs/segmenter/segmenter-propagate_vit-b16_512x512_320k_bs16_prior_1.0_lambda_0.0_downsample_2_in21k_ade_filter_vild_v2_prior_0.05_loss_weight_0.05_mix_batch_coco-stuff164k_imagenet21k_local.py \
# --auto-resume

# sudo bash local_test.sh \
# configs/segmenter/segmenter-propagate_vit-b16_512x512_eval_on_ade_full.py \
# work_dirs/segmenter-propagate_vit-b16_512x512_320k_bs16_prior_1.0_lambda_0.0_downsample_2_in21k_ade_filter_vild_v2_prior_0.05_loss_weight_0.05_mix_batch_coco-stuff164k_imagenet21k_local/iter_224000.pth \
# 4 \
# --eval mIoU


# sudo bash local_test.sh \
# configs/segmenter/segmenter-propagate_vit-b16_512x512_eval_on_ade_full.py \
# work_dirs/segmenter-propagate_vit-b16_512x512_320k_bs16_prior_1.0_lambda_0.0_downsample_2_in21k_ade_filter_vild_v2_prior_0.05_loss_weight_0.05_mix_batch_coco-stuff164k_imagenet21k_local/iter_320000.pth \
# 4 \
# --format-only \
# --eval-options "imgfile_prefix=work_dirs/segmenter-propagate_vit-b16_512x512_320k_bs16_prior_1.0_lambda_0.0_downsample_2_in21k_ade_filter_vild_v2_prior_0.05_loss_weight_0.05_mix_batch_coco-stuff164k_imagenet21k_local/inference_imagenet"
