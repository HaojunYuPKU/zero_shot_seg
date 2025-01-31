import copy
import json
import math
import numpy as np
import os
import random
import torch
import torch.nn as nn
import torch.nn.functional as F
from enum import unique
from genericpath import exists
from importlib_metadata import requires
from mmcv.runner import force_fp32, get_dist_info
from PIL import Image
from random import sample
from timm.models.layers import DropPath
from torch.nn.init import trunc_normal_

from mmseg.ops import resize
from ..builder import HEADS, build_loss
from ..losses.accuracy import accuracy
from .decode_head import BaseDecodeHead


def init_weights(m):
    if isinstance(m, nn.Linear):
        trunc_normal_(m.weight, std=0.02)
        if isinstance(m, nn.Linear) and m.bias is not None:
            nn.init.constant_(m.bias, 0)
    elif isinstance(m, nn.LayerNorm):
        nn.init.constant_(m.bias, 0)
        nn.init.constant_(m.weight, 1.0)


@HEADS.register_module()
class MaskTransformerLargeVocCoSegHead(BaseDecodeHead):
    def __init__(
        self,
        n_cls,  # for evaluation
        patch_size,
        d_encoder,
        n_layers,
        n_heads,
        d_model,
        d_ff,
        drop_path_rate,
        dropout,
        downsample_rate=8,
        # datasets
        all_cls_path="",
        mix_batch_datasets=["coco", "ade847"],
        test_dataset="ade847",
        ignore_indices=[255, -1],
        test_ignore_index=-1,
        basic_loss_weights=[1.0, 1.0],
        # weakly supervised
        weakly_supervised_datasets=["ade847"],
        # weakly_basic_loss_weight=1.0,
        weakly_seed_loss_weight=1.0,
        weakly_min_kept=100,
        # memory bank
        use_memory_bank=False,
        memory_bank_size=20,
        memory_image_size=20,
        memory_bank_full_time=1,
        # use_coseg_score=False,
        # coseg_max_reduce=False,
        context_suppression=False,
        context_thresh=1.0,
        context_topk=2,
        context_remove_thresh=0.2,
        **kwargs,
    ):
        # in_channels & channels are dummy arguments to satisfy signature of
        # parent's __init__
        super().__init__(
            in_channels=d_encoder,
            channels=1,
            num_classes=n_cls,
            **kwargs,
        )
        del self.conv_seg
        self.d_encoder = d_encoder
        self.n_cls = n_cls
        self.d_model = d_model
        self.scale = d_model**-0.5
        self.downsample_rate = downsample_rate
        # process datasets, valid for only one dataset
        if os.path.exists(all_cls_path):
            self.all_cls = json.load(open(all_cls_path))
        else:
            self.all_cls = None
        self.mix_batch_datasets = mix_batch_datasets
        self.test_dataset = test_dataset
        self.ignore_indices = ignore_indices
        self.test_ignore_index = test_ignore_index
        self.basic_loss_weights = basic_loss_weights
        assert len(mix_batch_datasets) == len(basic_loss_weights)
        # weakly supervised
        self.weakly_supervised_datasets = weakly_supervised_datasets
        # self.weakly_basic_loss_weight = weakly_basic_loss_weight
        self.weakly_seed_loss_weight = weakly_seed_loss_weight
        self.min_kept = weakly_min_kept
        self.weakly_supervised = False
        # self.proj_dec = nn.Linear(d_encoder, d_model)
        self.proj_patch = nn.Parameter(self.scale * torch.randn(d_model, d_model))
        self.proj_classes = nn.Parameter(self.scale * torch.randn(d_model, d_model))
        # cosine classifier
        self.gamma = nn.Parameter(torch.ones([]))
        self.beta = nn.Parameter(torch.zeros([]))
        self.all_classes = (
            self.num_classes if self.all_cls is None else len(self.all_cls)
        )
        self.cls_emb = nn.Parameter(torch.randn(self.all_classes, d_model))
        # memory bank
        self.use_memory_bank = use_memory_bank
        self.memory_bank_size = memory_bank_size
        # self.use_coseg_score = use_coseg_score
        # self.coseg_max_reduce = coseg_max_reduce
        self.context_suppression = context_suppression
        self.context_thresh = context_thresh
        self.context_topk = context_topk
        self.context_remove_thresh = context_remove_thresh
        self.size = memory_image_size
        self.full_time = memory_bank_full_time
        if self.use_memory_bank:
            self.register_buffer(
                f"queue",
                torch.randn(
                    self.all_classes, memory_bank_size, self.size**2, d_model
                ),
            )
            self.register_buffer(
                f"ptr", torch.zeros(self.all_classes, dtype=torch.long)
            )
            self.register_buffer(
                f"full", torch.zeros(self.all_classes, dtype=torch.long)
            )
            self.queue = self.queue / self.queue.norm(dim=-1, keepdim=True)
        self.rank, _ = get_dist_info()

    def init_weights(self):
        self.apply(init_weights)
        trunc_normal_(self.cls_emb, std=0.02)

    def _update(self, training):
        rank, _ = get_dist_info()
        if training:
            self.dataset_on_gpu = self.mix_batch_datasets[
                rank % len(self.mix_batch_datasets)
            ]
            self.ignore_index = self.ignore_indices[rank % len(self.mix_batch_datasets)]
            self.basic_loss_weight = self.basic_loss_weights[
                rank % len(self.mix_batch_datasets)
            ]
            self.weakly_supervised = (
                self.dataset_on_gpu in self.weakly_supervised_datasets
            )
        else:
            self.dataset_on_gpu = self.test_dataset
            self.ignore_index = self.test_ignore_index

        if self.dataset_on_gpu == "coco171":
            from mmseg.datasets.coco_stuff import COCOStuffDataset, ProcessedC171Dataset

            cls_name = COCOStuffDataset.CLASSES
            if len(self.mix_batch_datasets) > 1:
                cls_name = ProcessedC171Dataset.CLASSES
            cls_name = [x.split("-")[0] for x in cls_name]
        elif self.dataset_on_gpu == "ade150":
            from mmseg.datasets.ade import ADE20KDataset

            cls_name = ADE20KDataset.CLASSES
        elif self.dataset_on_gpu == "ade124":
            from mmseg.datasets.ade import ADE20K124Dataset

            cls_name = ADE20K124Dataset.CLASSES124
        elif self.dataset_on_gpu == "ade130":
            from mmseg.datasets.ade import ADE20K130Dataset

            cls_name = ADE20K130Dataset.CLASSES130
        elif self.dataset_on_gpu == "ade847":
            from mmseg.datasets.ade import ADE20KFULLDataset

            cls_name = ADE20KFULLDataset.CLASSES
        elif self.dataset_on_gpu == "ade585":
            from mmseg.datasets.ade import ADE20K585Dataset

            cls_name = ADE20K585Dataset.CLASSES585
        elif self.dataset_on_gpu == "in124":
            from mmseg.datasets.imagenet import ImageNet124

            cls_name = ImageNet124.CLASSES
        elif self.dataset_on_gpu == "in130":
            from mmseg.datasets.imagenet import ImageNet130

            cls_name = ImageNet130.CLASSES
        elif self.dataset_on_gpu == "in585":
            from mmseg.datasets.imagenet import ImageNet585

            cls_name = ImageNet585.CLASSES
        else:
            raise NotImplementedError(f"{self.dataset_on_gpu} is not supported")

        self.cls_name = cls_name
        if self.all_cls is not None:
            self.cls_index = [self.all_cls.index(name) for name in cls_name]
        else:
            self.cls_index = list(range(len(cls_name)))

    def _mask_norm(self, masks):
        return (
            (masks - torch.mean(masks, dim=-1, keepdim=True))
            / torch.sqrt(torch.var(masks, dim=-1, keepdim=True, unbiased=False) + 1e-5)
        ) * self.gamma + self.beta

    def forward(self, x, img_metas):
        x = self._transform_inputs(x)
        B, D, H, W = x.size()
        x = x.view(B, D, -1).permute(0, 2, 1)
        # x = self.proj_dec(x)
        cls_emb = self.cls_emb[self.cls_index]
        cls_emb = cls_emb.expand(x.size(0), -1, -1)
        patches = x
        patches = patches @ self.proj_patch
        cls_emb = cls_emb @ self.proj_classes
        patches = patches / patches.norm(dim=-1, keepdim=True)
        cls_emb = cls_emb / cls_emb.norm(dim=-1, keepdim=True)
        masks = patches @ cls_emb.transpose(1, 2)
        scores = masks.clone().detach()
        embeds = patches.clone().detach()
        masks = self._mask_norm(masks)
        B, HW, N = masks.size()
        masks = masks.view(B, H, W, N).permute(0, 3, 1, 2)
        scores = scores.view(B, H, W, N).permute(0, 3, 1, 2)
        embeds = embeds.view(B, H, W, -1).permute(0, 3, 1, 2)
        return masks, embeds, scores

    def forward_train(self, inputs, img_metas, gt_semantic_seg, train_cfg):
        self._update(training=True)
        masks, embeds, scores = self.forward(inputs, img_metas)
        losses = self.losses(masks, embeds, scores, gt_semantic_seg)
        return losses

    def forward_test(self, inputs, img_metas, test_cfg, gt_semantic_seg=None, img=None):
        self._update(training=False)
        masks, _, _ = self.forward(inputs, img_metas)
        return masks

    @force_fp32(apply_to=("seg_mask",))
    def losses(self, seg_mask, seg_embed, seg_score, seg_label):
        """Compute segmentation loss."""
        loss = dict()
        h = seg_label.shape[-2] // self.downsample_rate
        w = seg_label.shape[-1] // self.downsample_rate
        seg_mask = resize(
            seg_mask, size=(h, w), mode="bilinear", align_corners=self.align_corners
        )
        seg_label = resize(seg_label.float(), size=(h, w), mode="nearest").long()

        if self.weakly_supervised:
            mask, label, seed_mask, seed_label = self._weakly_sample(
                seg_mask, seg_embed, seg_score, seg_label
            )
            loss["loss_basic"] = (
                seg_mask.sum() * 0.0
                if mask is None
                else self.loss_decode(mask, label, ignore_index=self.ignore_index)
                * self.basic_loss_weight
            )
            loss["loss_seed"] = (
                seg_mask.sum() * 0.0
                if seed_mask is None
                else self.loss_decode(
                    seed_mask, seed_label, ignore_index=self.ignore_index
                )
                * self.weakly_seed_loss_weight
            )
        else:
            mask, label = self._sample(seg_mask, seg_label)
            loss["loss_basic"] = (
                self.loss_decode(mask, label, ignore_index=self.ignore_index)
                * self.basic_loss_weight
            )
            loss["loss_seed"] = mask.sum() * 0.0
        # log accuracy
        loss["acc_seg"] = self.log_accuracy(seg_mask, seg_label)
        return loss

    def log_accuracy(self, seg_mask, seg_label):
        B, N, H, W = seg_mask.shape
        seg_label = seg_label.flatten()
        seg_mask = seg_mask.permute(0, 2, 3, 1).reshape(B * H * W, N)
        weak_in_batch = len(self.weakly_supervised_datasets) > 0
        acc_weight = 0.0 if self.weakly_supervised else 2.0
        acc_weight = acc_weight if weak_in_batch else 1.0
        return accuracy(seg_mask, seg_label)

    def _sample(self, seg_mask, seg_label):
        """
        Args:
            seg_mask (torch.Tensor): segmentation logits, shape (B, N, H, W)
            seg_label (torch.Tensor): segmentation label, shape (B, 1, H, W)

        Returns:
            pos_bucket
            seed_bucket
        """
        B, N, H, W = seg_mask.size()
        seg_mask = seg_mask.permute(0, 2, 3, 1).reshape(B * H * W, N)
        seg_label = seg_label.reshape(B * H * W)
        return seg_mask, seg_label

    def _weakly_sample(self, seg_mask, seg_embed, seg_score, seg_label):
        B, N, H, W = seg_mask.size()
        B, D, h, w = seg_embed.size()
        masks, labels, seed_masks, seed_labels = [], [], [], []
        for mask, embed, score, label in zip(seg_mask, seg_embed, seg_score, seg_label):
            mask = mask.reshape(N, H * W).permute(1, 0)
            embed = embed.reshape(1, D, h, w)
            score = score.reshape(N, h * w).permute(1, 0)
            label = label.reshape(H * W)
            unique_label = torch.unique(label)
            unique_label = unique_label[unique_label != self.ignore_index]
            for l in unique_label.tolist():
                # NOTE: use normalized scores instead of raw cosine score
                thresh = mask[:, l].mean() + mask[:, l].std()
                inds = (mask[:, l] >= thresh).nonzero(as_tuple=False).flatten()
                if len(inds) < self.min_kept:
                    inds = mask[:, l].topk(self.min_kept).indices
                masks.append(mask[inds])
                labels.append(torch.zeros_like(label[inds]) + l)
            if not self.use_memory_bank:
                continue
            assert len(unique_label) == 1, "only support imagenet now"
            seed_score = self._remap_score(
                embed=embed, cls=int(unique_label), score=score
            )
            self._dequeue_and_enqueue(embed=embed, cls=int(unique_label))
            if seed_score is None:
                continue
            seed_score = F.interpolate(
                seed_score[None, None],
                size=(H, W),
                mode="bilinear",
                align_corners=self.align_corners,
            )[0, 0].flatten()
            seed_thresh = seed_score.mean() + seed_score.std()
            seed_inds = (seed_score >= seed_thresh).nonzero(as_tuple=False).flatten()
            if len(seed_inds) == 0:
                continue
            seed_masks.append(mask[seed_inds])
            seed_labels.append(label[seed_inds])
        if len(masks) > 0:
            masks = torch.cat(masks, dim=0)
            labels = torch.cat(labels, dim=0)
        else:
            masks, labels = None, None
        if len(seed_masks) > 0:
            seed_masks = torch.cat(seed_masks, dim=0)
            seed_labels = torch.cat(seed_labels, dim=0)
        else:
            seed_masks, seed_labels = None, None
        return masks, labels, seed_masks, seed_labels

    def _dequeue_and_enqueue(self, embed, cls):
        """
        Args:
            embed: torch.Tensor(1, D, H, W)
            cls: int, class index of current dataset
        """
        embed = (
            F.interpolate(
                embed,
                size=(self.size, self.size),
                mode="bilinear",
                align_corners=self.align_corners,
            )
            .reshape(-1, self.size**2)
            .permute(1, 0)
        )
        cls_ind = self.cls_index[cls]
        ptr = int(self.ptr[cls_ind])
        self.queue[cls_ind, ptr] = embed
        if (ptr + 1) >= self.memory_bank_size:
            self.full[cls_ind] += 1
        ptr = (ptr + 1) % self.memory_bank_size
        self.ptr[cls_ind] = ptr

    def _coseg_score(self, embed, cls):
        _, D, h, w = embed.size()
        cls_ind = self.cls_index[cls]
        fg_embed = self.queue[cls_ind]  # (20, 400, 768)
        if int(self.full[cls_ind]) < self.full_time:
            return None
        embed = embed.reshape(D, h * w).permute(1, 0)
        fg_embed = fg_embed.reshape(-1, D)
        cross_score = fg_embed @ embed.T
        cross_score = cross_score.reshape(self.memory_bank_size, self.size**2, h * w)
        if self.coseg_max_reduce:
            coseg_score = cross_score.max(dim=1).values.mean(dim=0)
        else:
            coseg_score = cross_score.mean(dim=1).mean(dim=0)
        return coseg_score

    def _remap_score(self, embed, cls, score):
        """
        Args:
            embed: torch.Tensor(1, D, h, w)
            cls: int, class index of current dataset
            score: torch.Tensor(H * W, N)
        Returns:
            remap_score: torch.Tensor(h, w)
        """
        device = embed.device
        _, D, h, w = embed.size()
        cls_ind = self.cls_index[cls]
        fg_embed = self.queue[cls_ind].clone().detach()  # (20, 400, 768)
        if int(self.full[cls_ind]) < self.full_time:
            return None
        embed = embed.reshape(D, h * w).permute(1, 0)
        fg_embed = fg_embed.reshape(-1, D)
        cross_score = fg_embed @ embed.T
        self_score = embed @ embed.T
        cross_score = cross_score.reshape(self.memory_bank_size, self.size**2, h * w)
        remap_score = []
        self_inds = torch.arange(len(self_score)).to(device)
        for s in cross_score:
            a2b_inds = s.max(dim=0).indices.flatten()
            b2a_inds = s.max(dim=1).indices.flatten()
            remap_inds = b2a_inds[a2b_inds]
            remap_score.append(self_score[self_inds, remap_inds])
        remap_score = torch.stack(remap_score, dim=0).mean(dim=0).reshape(h, w)
        # context suppression
        if self.context_suppression:
            # NOTE: use topk to avoid outlier
            topk_mean_scores = score.topk(self.context_topk, dim=0).values.mean(dim=0)
            context_mask = topk_mean_scores > self.context_thresh
            context_classes = context_mask.nonzero(as_tuple=False).flatten().tolist()
            # NOTE: remove similar classes to avoid suppress foreground classes
            fg_cls_embed = self.cls_emb[cls_ind].clone().detach()
            fg_cls_embed = fg_cls_embed / fg_cls_embed.norm(dim=-1, keepdim=True)
            for bg_cls in context_classes:
                bg_cls_embed = self.cls_emb[self.cls_index[bg_cls]].clone().detach()
                bg_cls_embed = bg_cls_embed / bg_cls_embed.norm(dim=-1, keepdim=True)
                cos_sim = float(fg_cls_embed @ bg_cls_embed.T)
                # if self.rank == 0 and bg_cls == cls:
                #     print(self.cls_name[bg_cls], bg_cls, cos_sim)
                if cos_sim > self.context_remove_thresh:
                    context_classes.remove(bg_cls)
                    # if self.rank == 0:
                    #     print(f"remove {self.cls_name[bg_cls]} from {self.cls_name[cls]}")
            # if self.rank == 0:
            #     print(f"find {[self.cls_name[bg_cls] for bg_cls in context_classes]} for bg of {self.cls_name[cls]}")
            bg_scores = []
            for bg_cls in context_classes:
                bg_ind = self.cls_index[bg_cls]
                bg_embed = self.queue[bg_ind]  # (20, 400, 768)
                bg_embed = bg_embed.reshape(-1, D)
                cross_score = bg_embed @ embed.T
                cross_score = cross_score.reshape(
                    self.memory_bank_size, self.size**2, h * w
                )
                bg_score = []
                for s in cross_score:
                    a2b_inds = s.max(dim=0).indices.flatten()
                    b2a_inds = s.max(dim=1).indices.flatten()
                    remap_inds = b2a_inds[a2b_inds]
                    bg_score.append(self_score[self_inds, remap_inds])
                bg_score = torch.stack(bg_score, dim=0).mean(dim=0).reshape(h, w)
                bg_scores.append(bg_score)
            if len(bg_scores) > 0:
                bg_score = torch.stack(bg_scores, dim=0).mean(dim=0)
                remap_score -= bg_score
        return remap_score

    @staticmethod
    def _get_batch_hist_vector(target, nclass):
        # target is a 3D Variable BxHxW, output is 2D BxnClass
        batch, H, W = target.shape
        tvect = target.new_zeros((batch, nclass), dtype=torch.int64)
        for i in range(batch):
            hist = torch.histc(
                target[i].data.float(), bins=nclass, min=0, max=nclass - 1
            )
            tvect[i] = hist
        return tvect
