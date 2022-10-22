# Copyright (c) OpenMMLab. All rights reserved.
from .ann_head import ANNHead
from .apc_head import APCHead
from .aspp_head import ASPPHead
from .cc_head import CCHead
from .da_head import DAHead
from .dm_head import DMHead
from .dnl_head import DNLHead
from .dpt_head import DPTHead
from .ema_head import EMAHead
from .enc_head import EncHead
from .fcn_head import FCNHead
from .fpn_head import FPNHead
from .gc_head import GCHead
from .isa_head import ISAHead
from .lraspp_head import LRASPPHead
from .mask_transformer_contrastive_head import MaskTransformerContrastiveHead
from .mask_transformer_cos_head import MaskTransformerCosHead
from .mask_transformer_essnet_head import MaskTransformerNNCEESSNetHead
from .mask_transformer_head import MaskTransformerHead
from .mask_transformer_large_voc_avgpool_head import \
    MaskTransformerLargeVocAvgPoolHead
from .mask_transformer_large_voc_head import MaskTransformerLargeVocHead
from .mask_transformer_large_voc_memory_bank_head import \
    MaskTransformerLargeVocMemoryBankHead
from .mask_transformer_large_voc_propagation_head import \
    MaskTransformerLargeVocPropagationHead
from .mask_transformer_large_voc_structure_head import \
    MaskTransformerLargeVocStructureHead
from .mask_transformer_linear_head import MaskTransformerLinearHead
from .mask_transformer_lseg_head import MaskTransformerLSegHead
from .mask_transformer_mlseg_decoder_head import \
    MaskTransformerMLSegDecoderHead
from .mask_transformer_mlseg_gt_head import MaskTransformerMLSegGTHead
from .mask_transformer_mlseg_head import MaskTransformerMLSegHead
from .mask_transformer_pix_embed_head import MaskTransformerPixEmbedHead
from .mask_transformer_prompt_learning_head import \
    MaskTransformerPromptLearningHead
from .mask_transformer_large_voc_attn_head import MaskTransformerLargeVocAttnHead
from .mask_transformer_large_voc_coseg_head import MaskTransformerLargeVocCoSegHead
from .mask_transformer_propagation_head import MaskTransformerPropagationHead
from .mask_transformer_structure_head import MaskTransformerStructureHead
from .mask_transformer_weak_head import MaskTransformerWeakHead
from .mlseg_decoder_head import MLSegDecoderHead
from .mlseg_encoder_head import MLSegEncoderHead
from .nl_head import NLHead
from .ocr_head import OCRHead
from .point_head import PointHead
from .psa_head import PSAHead
from .psp_head import PSPHead
from .segformer_head import SegformerHead
from .sep_aspp_head import DepthwiseSeparableASPPHead
from .sep_fcn_head import DepthwiseSeparableFCNHead
from .setr_mla_head import SETRMLAHead
from .setr_up_head import SETRUPHead
from .uper_head import UPerHead
from .uper_mlseg_head import UPerMLSegHead

__all__ = [
    'FCNHead', 'PSPHead', 'ASPPHead', 'PSAHead', 'NLHead', 'GCHead', 'CCHead',
    'UPerHead', 'DepthwiseSeparableASPPHead', 'ANNHead', 'DAHead', 'OCRHead',
    'EncHead', 'DepthwiseSeparableFCNHead', 'FPNHead', 'EMAHead', 'DNLHead',
    'PointHead', 'APCHead', 'DMHead', 'LRASPPHead', 'SETRUPHead', 'MLSegEncoderHead',
    'SETRMLAHead', 'DPTHead', 'SETRMLAHead', 'SegformerHead', 'ISAHead',
    'MaskTransformerHead', 'MaskTransformerMLSegGTHead', 'MaskTransformerNNCEESSNetHead', 
    'MaskTransformerMLSegHead', 'MLSegDecoderHead',
    'UPerMLSegHead', 'MaskTransformerMLSegDecoderHead',
    'MaskTransformerPixEmbedHead', 'MaskTransformerPropagationHead', 'MaskTransformerLSegHead',
    'MaskTransformerContrastiveHead', 'MaskTransformerPromptLearningHead',
    'MaskTransformerStructureHead', 'MaskTransformerLinearHead', 'MaskTransformerCosHead',
    'MaskTransformerLargeVocHead', 'MaskTransformerLargeVocPropagationHead',
    'MaskTransformerLargeVocMemoryBankHead', 'MaskTransformerLargeVocStructureHead',
    'MaskTransformerLargeVocAvgPoolHead', 'MaskTransformerLargeVocAttnHead',
    'MaskTransformerLargeVocCoSegHead'
]
