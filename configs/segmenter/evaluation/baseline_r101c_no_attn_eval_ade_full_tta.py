_base_ = [
    "../../_base_/models/segmenter_r101.py",
    "../../_base_/datasets/ade20kfull_merged_multiscale_rr1.py",
    "../../_base_/default_runtime.py",
    "../../_base_/schedules/schedule_160k.py",
]

model = dict(
    neck=dict(
        type="UseIndexSingleOutNeck",
        index=-1,
    ),
    decode_head=dict(
        type="MaskTransformerPropagationHead",
        use_attention_module=False,
        n_cls=655,
        d_encoder=2048,
        downsample_rate=2,
        upsample_input=2,
        cls_emb_path="pretrain/cls_emb_ade_full_merged_vild.pth",
        cls_emb_path_test="pretrain/cls_emb_ade_full_merged_vild.pth",
        prior_rate=1.0,
        imagenet_prior_loss_weight=0.05,
        propagation_loss_weight=0.0,
        grounding_inference=False,
        ann_suffix=".tif",
        test_anno_dir="/mnt/haojun2/dataset/ADE20K_2021_17_01/annotations_detectron2/validation_merged",
        ignore_index=65535
    ),
    test_cfg=dict(mode="slide", crop_size=(512, 512), stride=(512, 512)),
)

optimizer = dict(
    _delete_=True,
    type="SGD",
    lr=0.001,
    weight_decay=0.0,
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

# By default, models are trained on 8 GPUs with 2 images per GPU
data = dict(samples_per_gpu=2)
