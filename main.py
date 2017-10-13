#!/usr/bin/env python
# coding: utf-8
#
# Author:   Kazuto Nakashima
# URL:      http://kazuto1011.github.io
# Created:  2017-05-18

from __future__ import print_function

import argparse

import cv2
import numpy as np
import torchvision
from torchvision import transforms

from grad_cam import BackPropagation, GradCAM, GuidedBackPropagation


def main(args):

    # Load the synset words
    idx2cls = list()
    with open('samples/synset_words.txt') as lines:
        for line in lines:
            line = line.strip().split(' ', 1)[1]
            line = line.split(', ', 1)[0].replace(' ', '_')
            idx2cls.append(line)

    print('Loading a model...')
    model = torchvision.models.resnet152(pretrained=True)
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])

    print('\nGrad-CAM')
    gcam = GradCAM(model=model,
                   target_layer='layer4.2',
                   cuda=args.cuda)
    gcam.load_image(args.image, transform)
    gcam.forward()

    for i in range(0, 3):
        gcam.backward(idx=gcam.idx[i])
        cls_name = idx2cls[gcam.idx[i]]
        output = gcam.generate()
        print('\t{:.5f}\t{}'.format(gcam.prob[i], cls_name))
        gcam.save('results/{}_gcam.png'.format(cls_name), output)

    print('\nVanilla Backpropagation')
    bp = BackPropagation(model=model,
                         target_layer='conv1',
                         cuda=args.cuda)
    bp.load_image(args.image, transform)
    bp.forward()

    for i in range(0, 3):
        bp.backward(idx=bp.idx[i])
        cls_name = idx2cls[bp.idx[i]]
        output = bp.generate()
        print('\t{:.5f}\t{}'.format(bp.prob[i], cls_name))
        bp.save('results/{}_bp.png'.format(cls_name), output)

    print('\nGuided Backpropagation')
    gbp = GuidedBackPropagation(model=model,
                                target_layer='conv1',
                                cuda=args.cuda)
    gbp.load_image(args.image, transform)
    gbp.forward()

    for i in range(0, 3):
        cls_idx = gcam.idx[i]
        cls_name = idx2cls[cls_idx]

        gcam.backward(idx=cls_idx)
        output_gcam = gcam.generate()

        gbp.backward(idx=cls_idx)
        output_gbp = gbp.generate()

        output_gcam -= output_gcam.min()
        output_gcam /= output_gcam.max()
        output_gcam = cv2.resize(output_gcam, (224, 224))
        output_gcam = cv2.cvtColor(output_gcam, cv2.COLOR_GRAY2BGR)

        output = output_gbp * output_gcam

        print('\t{:.5f}\t{}'.format(gbp.prob[i], cls_name))
        gbp.save('results/{}_gbp.png'.format(cls_name), output_gbp)
        gbp.save('results/{}_ggcam.png'.format(cls_name), output)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Grad-CAM visualization')
    parser.add_argument('--no-cuda', action='store_true', default=False)
    parser.add_argument('--image', type=str, required=True)
    args = parser.parse_args()
    args.cuda = not args.no_cuda and torch.cuda.is_available()

    main(args)
