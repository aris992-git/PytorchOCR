# -*- coding: utf-8 -*-
# @Time    : 2019/8/23 21:56
# @Author  : zhoujun
from torch import nn

from torchocr.networks.losses.DetBasicLoss import BalanceCrossEntropyLoss, MaskL1Loss, DiceLoss, BalanceLoss


class DBLoss(nn.Module):
    def __init__(self, balance_loss=True, main_loss_type='DiceLoss', alpha=1.0, beta=10, ohem_ratio=3, reduction='mean',
                 eps=1e-6):
        """
        Implement PSE Loss.
        :param alpha: binary_map loss 前面的系数
        :param beta: threshold_map loss 前面的系数
        :param ohem_ratio: OHEM的比例
        :param reduction: 'mean' or 'sum'对 batch里的loss 算均值或求和
        """
        super().__init__()
        assert reduction in ['mean', 'sum'], " reduction must in ['mean','sum']"
        self.alpha = alpha
        self.beta = beta
        # self.bce_loss = BalanceCrossEntropyLoss(negative_ratio=ohem_ratio)
        self.bce_loss = BalanceLoss(
            balance_loss=balance_loss,
            main_loss_type=main_loss_type,
            negative_ratio=ohem_ratio)
        self.dice_loss = DiceLoss(eps=eps)
        self.l1_loss = MaskL1Loss(eps=eps)
        self.reduction = reduction

    def forward(self, pred, batch):
        """

        :param pred:
        :param batch: bach为一个dict{
                                    'shrink_map': 收缩图,b*c*h,w
                                    'shrink_mask: 收缩图mask,b*c*h,w
                                    'threshold_map: 二值化边界gt,b*c*h,w
                                    'threshold_mask: 二值化边界gtmask,b*c*h,w
                                    }
        :return:
        """
        shrink_maps = pred[:, 0, :, :]
        threshold_maps = pred[:, 1, :, :]
        binary_maps = pred[:, 2, :, :]

        loss_shrink_maps = self.alpha * self.bce_loss(shrink_maps, batch['shrink_map'], batch['shrink_mask'])
        loss_threshold_maps = self.beta * self.l1_loss(threshold_maps, batch['threshold_map'], batch['threshold_mask'])
        loss_dict = dict(loss_shrink_maps=loss_shrink_maps, loss_threshold_maps=loss_threshold_maps)
        if pred.size()[1] > 2:
            loss_binary_maps = self.dice_loss(binary_maps, batch['shrink_map'], batch['shrink_mask'])
            loss_dict['loss_binary_maps'] = loss_binary_maps
            loss_all = loss_shrink_maps + loss_threshold_maps + loss_binary_maps
            loss_dict['loss'] = loss_all
        else:
            loss_dict['loss'] = loss_shrink_maps

        return loss_dict
