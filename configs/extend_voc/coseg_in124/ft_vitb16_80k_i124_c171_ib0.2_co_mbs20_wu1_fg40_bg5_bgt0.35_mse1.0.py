_base_ = [
    "../../_base_/models/large_voc_vitb16.py",
    "../../_base_/datasets/mix_batch_IN124_COCO171_eval_ADE124.py",
    "../../_base_/default_runtime.py",
    "../../_base_/schedules/schedule_80k.py",
]

model = dict(
    pretrained="pretrain/"
    "vitb16_320k_i124_c171_ib0.2.pth",
    backbone=dict(
        drop_path_rate=0.1,
        final_norm=True,
    ),
    neck=dict(
        type="UseIndexSingleOutNeck",
        index=-1,
    ),
    decode_head=dict(
        type="MaskTransformerExtendVocHead",
        n_cls=124,
        downsample_rate=2,
        all_cls_path="notebook/ade124ucoco.json",
        mix_batch_datasets=["in124", "coco171"],
        weakly_supervised_datasets=["in124"],
        test_dataset="ade124",
        ignore_indices=[255, 255],
        test_ignore_index=255,
        basic_loss_weights=[0.2, 1.0],
        coseg_loss_weights=[0.2, 0.0],
        use_coseg=True,
        use_coseg_score_head=False,
        memory_bank_size=20,
        memory_bank_warm_up=1,
        foreground_topk=40,
        background_suppression=True,
        background_topk=5,
        background_thresh=0.35,
        background_mse_thresh=1.0,
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
