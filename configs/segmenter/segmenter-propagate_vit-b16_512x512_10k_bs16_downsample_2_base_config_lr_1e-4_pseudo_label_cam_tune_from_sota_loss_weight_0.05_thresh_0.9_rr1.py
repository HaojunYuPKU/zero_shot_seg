_base_ = [
    "../_base_/models/segmenter_vit-b16.py",
    "../_base_/datasets/mix_batch_coco-stuff164k_imagenet21k_ade_filter_v2_pseudo_label_cam.py",
    "../_base_/default_runtime.py",
    "../_base_/schedules/schedule_10k.py",
]

model = dict(
    pretrained="pretrain/iter_224000.pth", # sota for now
    backbone=dict(
        drop_path_rate=0.1,
        final_norm=True,
    ),
    neck=dict(
        type="UseIndexSingleOutNeck",
        index=-1,
    ),
    decode_head=dict(
        type="MaskTransformerPropagationHead",
        n_cls=150,
        downsample_rate=2,
        cls_emb_path=[
            "pretrain/cls_emb_coco_vild_v2.pth",
            "pretrain/cls_emb_in21k_vild_v2.pth"
        ],
        cls_emb_path_test="pretrain/cls_emb_ade_vild_v2.pth",
        imagenet_class_path="notebook/in21k_inter_ade_filter_v2.json",
        imagenet_prior_rate=0.05,
        imagenet_pseudo_label=True,
        pseudo_label_thresh=0.9,
        prior_rate=1.0,
        imagenet_prior_loss_weight=0.05,
    ),
    train_cfg=dict(init_method="load_checkpoint"),
    test_cfg=dict(mode="slide", crop_size=(512, 512), stride=(512, 512)),
)

optimizer = dict(
    _delete_=True,
    type="SGD",
    lr=0.0001,
    weight_decay=0.0, # replace 0.0 by 1e-10
    momentum=0.9,
    paramwise_cfg=dict(
        custom_keys={
            "pos_embed": dict(decay_mult=0.0),
            "cls_token": dict(decay_mult=0.0),
            "norm": dict(decay_mult=0.0),
        }
    ),
)

lr_config = dict(
    _delete_=True,
    policy="poly",
    warmup_iters=0,
    power=0.9,
    min_lr=1e-5,
    by_epoch=False,
)

# By default, models are trained on 8 GPUs with 1 images per GPU
data = dict(samples_per_gpu=4)