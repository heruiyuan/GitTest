#!/usr/bin/env python
# -*- coding: utf-8 -*-
import bpy
import numpy
import heapq
import json
import re

arr_location_U = []
arr_location_D = []
lost_teeth_1 = [18,17,16,15,14,13,12,11]
lost_teeth_2 = [21,22,23,24,25,26,27,28]
lost_teeth_3 = [31,32,33,34,35,36,37,38]
lost_teeth_4 = [48,47,46,45,44,43,42,41]

def ShowMessageBox(message = "", title = "Message Box", icon = 'INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

if bpy.context.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode = 'OBJECT')            
bpy.ops.object.select_all(action='DESELECT')

scene = bpy.context.scene
mytool = scene.my_tool

# ======Sort Up Side Teeth=======
lost_teeth_number = []
bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
for item in bpy.context.scene.my_tool.items():
    if item[0].startswith('U_') and item[1] == 1:
        lost_teeth_number.append(int(item[0].split('_')[1]))
print('Up Side Lost Teeth Number:', lost_teeth_number)

for lost_number in lost_teeth_number:
    if lost_number in lost_teeth_1:
        lost_teeth_1.remove(lost_number)
    if lost_number in lost_teeth_2:
        lost_teeth_2.remove(lost_number)

num = 0  #id
for tooth_num in lost_teeth_1:
    tooth_name = 'Tooth_U_' + str(num) + '_'
    bpy.context.collection.objects[tooth_name].show_name = True
    bpy.context.collection.objects[tooth_name].data.name = 'Tooth_' + str(tooth_num)
    bpy.context.collection.objects[tooth_name].name = 'Tooth_' + str(tooth_num)
    
    num = num + 1
for tooth_num in lost_teeth_2:
    tooth_name = 'Tooth_U_' + str(num) + '_'
    bpy.context.collection.objects[tooth_name].show_name = True
    bpy.context.collection.objects[tooth_name].data.name = 'Tooth_' + str(tooth_num)
    bpy.context.collection.objects[tooth_name].name = 'Tooth_' + str(tooth_num)
    
    num = num + 1
num = 0

# # ======Sort Down Side Teeth=======
lost_teeth_number = []
bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
for item in bpy.context.scene.my_tool.items():
    if item[0].startswith('D_') and item[1] == 1:
        lost_teeth_number.append(int(item[0].split('_')[1]))
print('Down Side Lost Teeth Number:', lost_teeth_number)

for lost_number in lost_teeth_number:
    if lost_number in lost_teeth_3:
        lost_teeth_3.remove(lost_number)
    if lost_number in lost_teeth_4:
        lost_teeth_4.remove(lost_number)

num = 0  #id
for tooth_num in lost_teeth_4:
    tooth_name = 'Tooth_D_' + str(num) + '_'
    bpy.context.collection.objects[tooth_name].show_name = True
    bpy.context.collection.objects[tooth_name].data.name = 'Tooth_' + str(tooth_num)
    bpy.context.collection.objects[tooth_name].name = 'Tooth_' + str(tooth_num)
    
    num = num + 1
for tooth_num in lost_teeth_3:
    tooth_name = 'Tooth_D_' + str(num) + '_'

    bpy.context.collection.objects[tooth_name].show_name = True
    bpy.context.collection.objects[tooth_name].data.name = 'Tooth_' + str(tooth_num)
    bpy.context.collection.objects[tooth_name].name = 'Tooth_' + str(tooth_num)
    num = num + 1
num = 0

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
bpy.ops.object.select_all(action='DESELECT')


bpy.ops.ed.undo_push()



