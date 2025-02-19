# ------------------------------------------------------------------------------
# Modified based on https://github.com/HRNet/HRNet-Semantic-Segmentation
# ------------------------------------------------------------------------------

import os

import cv2
import numpy as np
from PIL import Image

import torch
from .base_dataset import BaseDataset

class Flame(BaseDataset):
    def __init__(self, 
                 root, 
                 list_path,
                 num_classes=2,
                 multi_scale=True, 
                 flip=True, 
                 ignore_label=255, 
                 base_size=2048, 
                 crop_size=(512, 1024),
                 scale_factor=16,
                 mean=[0.485, 0.456, 0.406], 
                 std=[0.229, 0.224, 0.225],
                 bd_dilate_size=4):

        super(Flame, self).__init__(ignore_label, base_size,
                crop_size, scale_factor, mean, std,)

        self.root = root
        self.list_path = list_path
        self.num_classes = num_classes

        self.multi_scale = multi_scale
        self.flip = flip
        
        self.img_list = [line.strip().split() for line in open(root+list_path)]

        self.files = self.read_files()
        self.ignore_label = ignore_label

        # self.class_weights = torch.FloatTensor([0.7, 2.0]).cuda()
        self.class_weights = None

        self.label_mapping = {-1: ignore_label, 0: 0, 
                        1: 1}

        self.color_list = [[255,255,255], [0,0,0]]

        self.bd_dilate_size = bd_dilate_size
    
    def read_files(self):
        files = []
        for item in self.img_list:
            image_path, label_path = item
            name = os.path.splitext(os.path.basename(label_path))[0]
            files.append({
                "img": image_path,
                "label": label_path,
                "name": name
            })
        return files
    
    def color2label(self, color_map):
        label = np.ones(color_map.shape[:2])*self.ignore_label
        for i, v in enumerate(self.color_list):
            label[(color_map == v).sum(2)==3] = i

        return label.astype(np.uint8)
    
    def label2color(self, label):
        color_map = np.zeros(label.shape+(3,))
        for i, v in enumerate(self.color_list):
            color_map[label==i] = self.color_list[i]
            
        return color_map.astype(np.uint8)

        
    # def convert_label(self, label, inverse=False):
    #     temp = label.copy()
    #     if inverse:
    #         for v, k in self.label_mapping.items():
    #             label[temp == k] = v
    #     else:
    #         for k, v in self.label_mapping.items():
    #             label[temp == k] = v
    #     return label

    def __getitem__(self, index):
        item = self.files[index]
        name = item["name"]
        image = cv2.imread(os.path.join(self.root,'flame',item["img"]),
                           cv2.IMREAD_COLOR)
        size = image.shape

        # color_map = Image.open(os.path.join(self.root,'flame',item["label"])).convert('RGB')
        color_map = cv2.imread(os.path.join(self.root,'flame',item["label"]),
                           cv2.IMREAD_GRAYSCALE)
        color_map = np.array(color_map)
        # label = self.color2label(color_map)
        label = color_map

        # label = cv2.imread(os.path.join(self.root,'cityscapes',item["label"]),
        #                    cv2.IMREAD_GRAYSCALE)
        # label = self.convert_label(label)

        image, label, edge = self.gen_sample(image, label, 
                                self.multi_scale, self.flip, edge_size=self.bd_dilate_size)

        return image.copy(), label.copy(), edge.copy(), np.array(size), name

    
    def single_scale_inference(self, config, model, image):
        pred = self.inference(config, model, image)
        return pred


    def save_pred(self, preds, sv_path, name):
        preds = np.asarray(np.argmax(preds.cpu(), axis=1), dtype=np.uint8)
        for i in range(preds.shape[0]):
            # pred = self.convert_label(preds[i], inverse=True)
            # pred = self.label2color(preds[i])
            pred = preds[i]
            save_img = Image.fromarray(pred)
            save_img.save(os.path.join(sv_path, name[i]+'.png'))

        
        
