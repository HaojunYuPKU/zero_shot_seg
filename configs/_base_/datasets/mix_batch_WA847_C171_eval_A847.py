# MixBatch dataset
img_norm_cfg = dict(
    mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True
)
# COCO dataset settings
coco_data_root = "/workspace/dataset/coco_stuff164k"
coco_train_pipeline = [
    dict(type="LoadImageFromFile"),
    dict(type="LoadAnnotations"),
    dict(type="Resize", img_scale=(2048, 512), ratio_range=(0.5, 2.0)),
    dict(type="RandomCrop", crop_size=(512, 512), cat_max_ratio=0.75),
    dict(type="RandomFlip", prob=0.5),
    dict(type="PhotoMetricDistortion"),
    dict(type="Normalize", **img_norm_cfg),
    dict(type="Pad", size=(512, 512), pad_val=0, seg_pad_val=255),
    dict(type="DefaultFormatBundle"),
    dict(type="Collect", keys=["img", "gt_semantic_seg"]),
]
# ADE20K dataset settings
ade_data_root = "/workspace/dataset/ade20k_full"
ade_train_pipeline = [
    dict(type="LoadImageFromFile"),
    dict(type="LoadAnnotations", reduce_zero_label=False, int16=True),
    dict(type="Resize", img_scale=(2048, 512), ratio_range=(0.5, 2.0)),
    dict(type="RandomCrop", crop_size=(512, 512), cat_max_ratio=0.75),
    dict(type="RandomFlip", prob=0.5),
    dict(type="PhotoMetricDistortion"),
    dict(type="Normalize", **img_norm_cfg),
    dict(type="Pad", size=(512, 512), pad_val=0, seg_pad_val=-1),
    dict(type="DefaultFormatBundle"),
    dict(type="Collect", keys=["img", "gt_semantic_seg"]),
]
ade_test_pipeline = [
    dict(type="LoadImageFromFile"),
    dict(
        type="MultiScaleFlipAug",
        img_scale=(2048, 512),
        flip=False,
        transforms=[
            dict(type="Resize", keep_ratio=True),
            dict(type="RandomFlip"),
            dict(type="Normalize", **img_norm_cfg),
            dict(type="ImageToTensor", keys=["img"]),
            dict(type="Collect", keys=["img"]),
        ],
    ),
]

data = dict(
    samples_per_gpu=2,
    workers_per_gpu=4,
    train=dict(
        type="MixBatchDataset",
        dataset_list=[
            dict(
                type="ADE20KFULLDataset",
                data_root=ade_data_root,
                img_dir="train/image",
                ann_dir="train/label",
                pipeline=ade_train_pipeline,
            ),
            dict(
                type="ProcessedC171Dataset",
                data_root=coco_data_root,
                img_dir="images/train2017",
                ann_dir="annotations/train2017",
                pipeline=coco_train_pipeline,
            ),
        ],
    ),
    val=dict(
        type="ADE20KFULLDataset",
        data_root=ade_data_root,
        img_dir="val/image",
        ann_dir="val/label",
        pipeline=ade_test_pipeline,
    ),
    test=dict(
        type="ADE20KFULLDataset",
        data_root=ade_data_root,
        img_dir="val/image",
        ann_dir="val/label",
        pipeline=ade_test_pipeline,
    ),
)
