#!/usr/bin/env python
# -*- coding: utf-8 -*-
import bpy
import numpy
import heapq
import json
import re

arr_location_U = []
arr_location_D = []
lost_teeth_1 = [11,12,13,14,15,16,17,18]
lost_teeth_2 = [21,22,23,24,25,26,27,28]
lost_teeth_3 = [31,32,33,34,35,36,37,38]
lost_teeth_4 = [41,42,43,44,45,46,47,48]

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
print(lost_teeth_1, lost_teeth_2)
num = 0  #id
for obj in bpy.context.collection.objects:
    if obj.name.startswith('Tooth'):
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
        arr_location_U.append({"id":num, "name":obj.name, "x":obj.location[0], "y":obj.location[1], "z":obj.location[2]})
        num += 1
        bpy.ops.object.select_all(action='DESELECT')

num_1 = 0
num_2 = 0

for obj in sorted(arr_location_U, key=lambda x:x['y']):
    if obj["x"] > 0:
        try:
            bpy.context.collection.objects[obj["name"]].data.name = ("Tooth_"+str(lost_teeth_2[num_2]))
            bpy.context.collection.objects[obj["name"]].name = ("Tooth_"+str(lost_teeth_2[num_2]))
        except IndexError:
            bpy.ops.ed.undo()
            ShowMessageBox("This is a message", "This is a custom title", 'ERROR')
        else:
            pass
        num_2 += 1
    elif obj["x"] < 0:
        try:
            bpy.context.collection.objects[obj["name"]].data.name = ("Tooth_"+str(lost_teeth_1[num_1]))
            bpy.context.collection.objects[obj["name"]].name = ("Tooth_"+str(lost_teeth_1[num_1]))
        except IndexError:
            ShowMessageBox("This is a message", "This is a custom title", 'ERROR')
        else:
            pass
        num_1 += 1


# ======Sort Down Side Teeth=======
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
print(lost_teeth_3, lost_teeth_4)
num = 0
for obj in bpy.context.collection.objects:
    if obj.name.startswith('Tooth'):
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
        arr_location_D.append({"id":num, "name":obj.name, "x":obj.location[0], "y":obj.location[1], "z":obj.location[2]})
        num += 1
        bpy.ops.object.select_all(action='DESELECT')
print(arr_location_D)
num_4 = 0
num_3 = 0
for obj in sorted(arr_location_D, key=lambda x:x['y']):
    if obj["x"] > 0:
        try:
            bpy.context.collection.objects[obj["name"]].data.name = ("Tooth_"+str(lost_teeth_3[num_3]))
            bpy.context.collection.objects[obj["name"]].name = ("Tooth_"+str(lost_teeth_3[num_3]))
        except IndexError:
            ShowMessageBox("This is a message", "This is a custom title", 'ERROR')
        else:
            pass
        num_3 += 1
    elif obj["x"] < 0:
        try:
            bpy.context.collection.objects[obj["name"]].data.name = ("Tooth_"+str(lost_teeth_4[num_4]))
            bpy.context.collection.objects[obj["name"]].name = ("Tooth_"+str(lost_teeth_4[num_4]))
        except IndexError:
            ShowMessageBox("This is a message", "This is a custom title", 'ERROR')
        else:
            pass
        num_4 += 1
bpy.ops.ed.undo_push()



