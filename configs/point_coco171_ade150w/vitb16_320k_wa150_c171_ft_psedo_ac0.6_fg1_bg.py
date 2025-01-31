_base_ = [
    "../_base_/models/large_voc_vitb16.py",
    "../_base_/datasets/mix_batch_WA150_C171_eval_A150.py",
    "../_base_/default_runtime.py",
    "../_base_/schedules/schedule_320k.py",
]

model = dict(
    pretrained="pretrain/lseg_c171.pth",
    backbone=dict(
        drop_path_rate=0.1,
        final_norm=True,
    ),
    neck=dict(
        type="UseIndexSingleOutNeck",
        index=-1,
    ),
    decode_head=dict(
        type="PointSegHead",
        n_cls=150,
        downsample_rate=2,
        mix_batch_datasets=["ade150", "coco171"],
        weakly_supervised_datasets=["ade150"],
        test_dataset="ade150",
        ignore_indices=[255, 255],
        test_ignore_index=255,
        basic_loss_weights=[0.0, 1.0],
        coseg_loss_weights=[0.6, 0.0],
        use_coseg=True,
        use_coseg_single_image=True,
        use_coseg_score_head=False,
        use_pseudo_label=True,
        use_lang_seg=True,
        cls_emb_train=["file/cls_emb_a150.pth", "file/cls_emb_c171.pth"],
        cls_emb_test="file/cls_emb_a150.pth",
    ),
    train_cfg=dict(init_method="load_checkpoint"),
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
