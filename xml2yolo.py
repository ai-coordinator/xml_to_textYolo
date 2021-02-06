#!/usr/bin/env python
# -*- coding: utf8 -*-
import os
import sys
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
from lxml import etree
import codecs
import cv2
from glob import glob

XML_EXT = '.xml'
ENCODE_METHOD = 'utf-8'

class PascalVocReader:
    def __init__(self, filepath):
        # shapes type:
        # [labbel, [(x1,y1), (x2,y2), (x3,y3), (x4,y4)], color, color, difficult]
        self.shapes = []
        self.filepath = filepath
        self.verified = False
        try:
            self.parseXML()
        except:
            pass

    def getShapes(self):
        return self.shapes

    def addShape(self, label, bndbox, filename, difficult):
        xmin = int(bndbox.find('xmin').text)
        ymin = int(bndbox.find('ymin').text)
        xmax = int(bndbox.find('xmax').text)
        ymax = int(bndbox.find('ymax').text)
        points = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
        self.shapes.append((label, points, filename, difficult))

    def parseXML(self):
        assert self.filepath.endswith(XML_EXT), "Unsupport file format"
        parser = etree.XMLParser(encoding=ENCODE_METHOD)
        xmltree = ElementTree.parse(self.filepath, parser=parser).getroot()
        filename = xmltree.find('filename').text
        path = xmltree.find('path').text
        try:
            verified = xmltree.attrib['verified']
            if verified == 'yes':
                self.verified = True
        except KeyError:
            self.verified = False

        for object_iter in xmltree.findall('object'):
            bndbox = object_iter.find("bndbox")
            label = object_iter.find('name').text
            # Add chris

            difficult = False
            if object_iter.find('difficult') is not None:
                difficult = bool(int(object_iter.find('difficult').text))
            self.addShape(label, bndbox, path, difficult)
        return True


classes = dict()
num_classes = 0

try:
    input = raw_input
except NameError:
    pass


parentpath = './' #"Directory path with parent dir before xml_dir or img_dir"
addxmlpath = parentpath + 'fire-dataset/validation/annotations' #"Directory path with XML files"
addimgpath = parentpath + 'fire-dataset/validation/images' #"Directory path with IMG files"
outputpath = parentpath + 'labels' #"output folder for yolo format"
classes_txt = './fire_classes.txt' #"File containing classes"
ext = '.jpg' #"Image file extension [.jpg or .png]"


if os.path.isfile(classes_txt):
    with open(classes_txt, "r") as f:
        class_list = f.read().strip().split()
        classes = {k : v for (v, k) in enumerate(class_list)}

xmlPaths = glob(addxmlpath + "/*.xml")
#imgPaths = glob(addimgpath + "/*"+ext)

for xmlPath in xmlPaths:
    tVocParseReader = PascalVocReader(xmlPath)
    shapes = tVocParseReader.getShapes()

    with open(outputpath + "/" + os.path.basename(xmlPath)[:-4] + ".txt", "w") as f:
        for shape in shapes:
            class_name = shape[0]
            box = shape[1]
            #filename = os.path.splittext(xmlPath)[0] + ext
            filename = os.path.splitext(addimgpath + "/" + os.path.basename(xmlPath)[:-4])[0] + ext

            if class_name not in classes.keys():
                classes[class_name] = num_classes
                num_classes += 1
            class_idx = classes[class_name]

            (height, width, _) = cv2.imread(filename).shape

            coord_min = box[0]
            coord_max = box[2]

            xcen = float((coord_min[0] + coord_max[0])) / 2 / width
            ycen = float((coord_min[1] + coord_max[1])) / 2 / height
            w = float((coord_max[0] - coord_min[0])) / width
            h = float((coord_max[1] - coord_min[1])) / height

            f.write("%d %.06f %.06f %.06f %.06f\n" % (class_idx, xcen, ycen, w, h))
            print(class_idx, xcen, ycen, w, h)

with open(parentpath + "classes.txt", "w") as f:
    for key in classes.keys():
        f.write("%s\n" % key)
        print(key)
