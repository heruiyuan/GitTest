bl_info = {
    "name": "Smooth Tooth Edge",
    "author": "Rien",
    "version": (1, 0),
    "blender": (2, 83, 0),
    "location": "SpaceBar Search -> Add-on Preferences Example",
    "description": "Smooth the edge of a selected single tooth",
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Mesh",
}
import collections
from types import CodeType, resolve_bases
from typing import Text
from numpy.lib import angle
from numpy.lib.arraypad import _set_pad_area

from numpy.linalg import norm
import bpy
import mathutils
import bmesh
import math
import numpy as np
import sys
from bpy_extras import object_utils
import functools
import re
import os
import json
import getpass


dir = os.path.expanduser('~')+'\\AppData\\Roaming\\Blender Foundation\\Blender\\2.83\\scripts\\addons\\pie_menu_editor\\scripts\\zhangzechu'
if not dir in sys.path:
    sys.path.append(dir)

# from fillToothHole import fillSingleToothHole, fill_all_teeth_hide
from tip_torque import select_tooth_Tip_Torque
from tip_torque import get_tooth_surface_matrix
from tip_torque import ShowMessageBox
from tip_torque import getTip
from tip_torque import getTorque


from movePanel import recover_homogenous_affine_transformation
from movePanel import create_plane_three_point
from movePanel import into_select_faces_mode_jaw
from movePanel import delete_object
from movePanel import create_plane

filepath=os.path.expanduser('~')+'/AppData/Roaming/Blender Foundation/Blender/2.83/parameter.json'
parameterlist=[]
with open(filepath, 'r') as f:
    parameterlist = json.load(f)
    
#read parameters
setnames = locals()
for key, value in parameterlist.items():  
    setnames[key]=value 

def exec_read_global_peremeter(commend,key):
    _locals = locals()
    exec(commend,globals(),_locals)
    if key in _locals:
        return _locals[key]
    return commend

#read parameters
setnames = locals()
for key, value in parameterlist.items():  
    setnames[key]=value 

def exec_read_global_peremeter(commend,key):
    _locals = locals()
    exec(commend,globals(),_locals)
    if key in _locals:
        return _locals[key]
    return commend

def remove_extra_vetrices_faces(context_object):
    edge_keys = context_object.data.edge_keys
    total_index = len(context_object.data.vertices)

    vrt_index = []
    for edge_key in edge_keys:
        vrt_index.append(edge_key[0])
        vrt_index.append(edge_key[1])

    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    for index in range(total_index):
        b = vrt_index.count(index)
        if b == 1:
            context_object.data.vertices[index].select = True
        elif b == 3:
            if len(bpy.context.object.data.polygons) != 0:
                for polygon in bpy.context.object.data.polygons:
                    three_index = []
                    three_index.append(polygon.edge_keys[0][0])
                    three_index.append(polygon.edge_keys[0][1])
                    if polygon.edge_keys[1][0] != three_index[0] and polygon.edge_keys[1][0] != three_index[1]:
                        three_index.append(polygon.edge_keys[1][0])
                    else:
                        three_index.append(polygon.edge_keys[1][1])
                    print(three_index)
                    for tri_index in three_index:
                        if vrt_index.count(tri_index) == 2:
                            context_object.data.vertices[tri_index].select = True
                            break
            else:
                pass
        else:
            pass
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode = 'OBJECT')

    return {'FINISHED'}

def draw(self, context):
    
    error_message = str(context.object.pass_index) + '\'s knife panel is not in correct position!'
    self.layout.label(text=error_message)

def distance(point1, point2):
    """Calculate distance bewteen two points in 3D space"""
    disp = point1 - point2
    dis = math.sqrt(disp[0]*disp[0] + disp[1]*disp[1] + disp[2]*disp[2])
    return dis

def pair_traingles(through_triangle_info):
        dis_triangle_info = dict()
        for triangle_info1 in through_triangle_info:
            hit_loc1 = triangle_info1[0]
            index = triangle_info1[1]
            min_dis = 100
            min_dis_triangle_info = triangle_info1
            for triangle_info2 in through_triangle_info:
                if index == triangle_info2[1]:
                    continue
                hit_loc2 = triangle_info2[0]
                dis = distance(hit_loc1, hit_loc2)
                if dis < min_dis:
                    min_dis = dis
                    min_dis_triangle_info = triangle_info2
            dis_triangle_info[min_dis] = (triangle_info1, min_dis_triangle_info)
        sorted_list = sorted(dis_triangle_info.items(), key=lambda item:item[0], reverse=True)
        # print("Sort List:", sorted_list)
        return sorted_list

def generate_emboss_panel(self, context, object_name):
    if len(context.selected_objects) == 1 and context.object.name.endswith('curve'):
        scene = context.scene
        mytool = scene.my_tool

        tooth_object = context.collection.objects[object_name]
        
        curve_object = context.object
        context.view_layer.objects.active = curve_object
        context.object.select_set(True)
        bpy.ops.object.convert(target='MESH')

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='cubic', lock_x=False, lock_y=False, lock_z=False)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        
        bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')
        bpy.ops.object.modifier_add(type='SHRINKWRAP')
        bpy.context.object.modifiers["Shrinkwrap"].target = tooth_object
        bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'ABOVE_SURFACE'
        bpy.context.object.modifiers["Shrinkwrap"].offset = -0.27
        bpy.ops.object.modifier_add(type='SMOOTH')
        bpy.context.object.modifiers["Smooth"].iterations = 10

        bpy.ops.object.convert(target='MESH')

        curve_object_copy = bpy.context.object

        temp_name = curve_object.name + '.001'
        context.view_layer.objects.active = curve_object
        curve_object.select_set(True)
        curve_object_copy.select_set(True)
        bpy.ops.object.join()

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT') 
        bpy.ops.mesh.select_all(action='SELECT')  
        bpy.ops.mesh.bridge_edge_loops(type='PAIRS')
        bpy.ops.object.mode_set(mode='OBJECT')

        context.view_layer.objects.active = tooth_object
        tooth_object.select_set(True)
        bpy.ops.object.join()

        bpy.ops.object.mode_set(mode='EDIT')

        bpy.ops.object.vertex_group_add()
        tooth_object.vertex_groups['Group'].name = 'panel'
        bpy.ops.object.vertex_group_assign()

        bpy.ops.mesh.intersect()
        bpy.ops.object.vertex_group_add()
        tooth_object.vertex_groups['Group'].name = 'intersect'
        bpy.ops.object.vertex_group_assign()
        
        bpy.ops.mesh.select_all(action='DESELECT')
        tooth_object.vertex_groups.active = tooth_object.vertex_groups['panel']
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_remove()

        bpy.ops.mesh.select_linked(delimit=set())
        if context.object.data.total_vert_sel > 1000:
            print('Selection Error!')
            self.report({'ERROR'}, 'Selection Error!')
            return {'CANCELED'}
        bpy.ops.mesh.separate(type='SELECTED')
        
        bpy.ops.object.mode_set(mode='OBJECT')
        tooth_object.select_set(False)
        bpy.ops.object.delete(use_global=False, confirm=True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_select()

        bpy.ops.mesh.loop_to_region()
        if context.object.data.total_vert_sel > 1000:
            print('Selection Error!')
            self.report({'ERROR'}, 'Selection Error!')
            return {'CANCELED'}
        bpy.ops.mesh.duplicate(mode=1)
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        panel_name = object_name + '.001'
        panel_object = bpy.data.objects[panel_name]
        panel_object.data.name =  object_name + 'panel'
        panel_object.name = object_name + 'panel'

        return panel_object

def conver_gpencil_to_curve(self, context, pencil, type):
    newCurve = bpy.data.curves.new(type + '_line', type='CURVE')
    newCurve.dimensions = '3D'
    CurveObject = object_utils.object_data_add(context, newCurve)
    error = False

    try:
        strokes = bpy.context.annotation_data.layers.active.active_frame.strokes
    except:
        error = True
        CurveObject.location = (0.0, 0.0, 0.0)
        CurveObject.rotation_euler = (0.0, 0.0, 0.0)
        CurveObject.scale = (1.0, 1.0, 1.0)

    if not error:
        for i, _stroke in enumerate(strokes):
            print(i)
            stroke_points = strokes[i].points
            data_list = [ (point.co.x, point.co.y, point.co.z)
                            for point in stroke_points ]
            points_to_add = len(data_list)-1

            flat_list = []
            for point in data_list:
                flat_list.extend(point)

            spline = newCurve.splines.new(type='BEZIER')
            spline.bezier_points.add(points_to_add)
            spline.bezier_points.foreach_set("co", flat_list)

            for point in spline.bezier_points:
                point.handle_left_type="AUTO"
                point.handle_right_type="AUTO"

        return CurveObject
    else:
        return None

def get_picked_tooth_name(scene, context):
    items = [
    ]
    if bpy.data.collections.get('Pick_Teeth') is None :
        pass   
    else:
        if len(bpy.data.collections['Pick_Teeth'].objects) > 0:
            for obj in bpy.data.collections['Pick_Teeth'].objects:
                items.append((obj.name, obj.name, obj.name))
    return items

def get_bound_box_volume(object):
    ref_box = object.bound_box
    x = ref_box[0][0]
    y = ref_box[0][1]
    z = ref_box[0][2]
    x_ = 0
    y_ = 0
    z_ = 0
    for vertex in ref_box:
        if vertex[0] != x:
            x_ = vertex[0]
        if vertex[1] != y:
            y_ = vertex[1]
        if vertex[2] != z:
            z_ = vertex[2]
    len_x = abs(x - x_)
    len_y = abs(y - y_)
    len_z = abs(z - z_)
    volume = len_x * len_y * len_z
    print('box_info  ', object.name, len_x, len_y, len_z, volume)
    return volume

def get_plane_ref_coord_matrix(plane_object, tooth_object, up_down):
    loca = plane_object.location
    matrix_world = plane_object.matrix_world.copy()    
    if len(plane_object.data.polygons) == 1:
        polygon_normal = plane_object.data.polygons[0].normal.copy()
        if up_down == 'UP_':
            if polygon_normal[2] < 0:
                polygon_normal[2] = -polygon_normal[2]
        else:
            if polygon_normal[2] > 0:
                polygon_normal[2] = -polygon_normal[2]  

        polygon_normal = (matrix_world @ polygon_normal) - loca
        polygon_normal.normalize()
        print('polygon normal', polygon_normal)
    else:
        print('Jaw polygons has no face normal')
        return {'CANCELLED'}

    x_axis = mathutils.Vector((tooth_object.matrix_local.row[0][0], tooth_object.matrix_local.row[1][0], tooth_object.matrix_local.row[2][0]))
    z_axis = x_axis.cross(polygon_normal)
    z_axis.normalize()
    x_axis = polygon_normal.cross(z_axis)
    x_axis.normalize()

    M_orient = mathutils.Matrix([x_axis, polygon_normal, z_axis])
    M_orient.transpose()
    M_orient.normalize()
    M_orient = M_orient.to_4x4()
    
    N = tooth_object.matrix_local.copy()
    M_orient.row[0][3] = N.row[0][3]
    M_orient.row[1][3] = N.row[1][3]
    M_orient.row[2][3] = N.row[2][3]

    return M_orient

def get_tip(tooth_object, K_orient, tooth_number):
    K_orient = K_orient.to_3x3()
    K_orient_inver = K_orient.inverted()
    obj_y_axis = mathutils.Vector((tooth_object.matrix_local.row[0][1], tooth_object.matrix_local.row[1][1], tooth_object.matrix_local.row[2][1]))
    
    local_y_axis = (K_orient_inver @ obj_y_axis)

    print(tooth_number,' local Y axis:',local_y_axis)
    angle_radian = math.atan2(local_y_axis[0], local_y_axis[1])
    if ((10 < tooth_number) and (tooth_number < 20)) or ((30 < tooth_number) and (tooth_number < 40)):
        if local_y_axis[0] > 0:
            angle_radian = abs(angle_radian)
        else:
            angle_radian = -abs(angle_radian)
    elif ((20 < tooth_number) and (tooth_number < 30)) or ((40 < tooth_number) and (tooth_number < 50)):
        if local_y_axis[0] < 0:
            angle_radian = abs(angle_radian)
        else:
            angle_radian = -abs(angle_radian)
    else:
        pass
    print('tip angle radian', angle_radian)
    return angle_radian

def get_torque(tooth_object, K_orient):
    
    matrix_world = tooth_object.matrix_world.copy()
    obj_loca = tooth_object.location.copy()
    polygons = tooth_object.data.polygons
    vertex_index = []
    cusp_points_hight=polygons[0].center[1]
    for face in polygons:
        if face.center[2]<0 and cusp_points_hight>face.center[1]:
            cusp_points_hight = face.center[1]
            vertex_index.append(face.index)
    print(tooth_object.name, 'min hight:', cusp_points_hight)
    dir = mathutils.Vector((0, 0, 1))
    dist = 10
    origin = mathutils.Vector((0, cusp_points_hight/4, -10))
    result = tooth_object.ray_cast(origin, dir, distance=dist)
    polygons[result[3]].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_more()
    bpy.ops.mesh.select_more()
    bpy.ops.object.mode_set(mode='OBJECT')
    
    normal_vector = mathutils.Vector((0, 0, 0))
    num = 0
    for face in polygons:
        if face.select == True:
            normal_vector = normal_vector + face.normal
            num = num + 1
    normal_vector = normal_vector / num
    normal_vector.normalize()
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    face_normal = (matrix_world @ normal_vector) - obj_loca
    face_normal.normalize()
    x_axis = mathutils.Vector((matrix_world.row[0][0], matrix_world.row[1][0], matrix_world[2][0]))
    y_axis = x_axis.cross(face_normal)
    y_axis.normalize()
    x_axis = face_normal.cross(y_axis)
    x_axis.normalize()

    K_orient = K_orient.to_3x3()
    K_orient_inver = K_orient.inverted()
    y_axis_local = (K_orient_inver @ y_axis)
    y_axis_local.normalize()

    angle_raidan = math.atan2(y_axis_local[2], y_axis_local[1])
    if y_axis_local[2] > 0:
        angle_raidan = abs(angle_raidan)
    else:
        angle_raidan = -abs(angle_raidan)
    # print('y_axis_local', y_axis_local)
    # print('torque angle', angle)
    return angle_raidan

def update(self, context, operate_id):
    tooth_number = operate_id.split('_')[1]
    operate_type = operate_id.split('_')[0]
    mytool = context.scene.my_tool

    if mytool.up_down == 'UP_':
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
    else:
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']

    tooth_name = 'Tooth_' + tooth_number
    tooth_object = context.collection.objects[tooth_name]

    jawplaneName = 'jawPlane_' + mytool.up_down
    plane_object = bpy.data.objects[jawplaneName]

    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = tooth_object
    tooth_object.select_set(True)
    print('selected_objects:', len(bpy.context.selected_objects))
    M_orient = get_plane_ref_coord_matrix(plane_object, tooth_object, mytool.up_down)
    if operate_type == 'A':
        current_tip = get_tip(tooth_object, M_orient, int(tooth_number))
        prop_name = 'Tip_' + tooth_number
        update_tip = mytool.get(prop_name)
        disp_angle = current_tip - update_tip
        if (20 < int(tooth_number) < 30) or (40 < int(tooth_number) < 50):
            disp_angle = -disp_angle
        print('Changed Tip:', update_tip * (180/math.pi))
        print('Disprity angle:', disp_angle * (180/math.pi))

        a = (M_orient.row[0][0], M_orient.row[1][0], M_orient.row[2][0]) 
        b = (M_orient.row[0][1], M_orient.row[1][1], M_orient.row[2][1])
        c = (M_orient.row[0][2], M_orient.row[1][2], M_orient.row[2][2])
        bpy.ops.transform.rotate(value=disp_angle, orient_axis='Z', orient_type='LOCAL', orient_matrix=(a, b, c), orient_matrix_type='LOCAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
    else:
        current_tor = get_torque(tooth_object, M_orient)
        prop_name = 'Tor_' + tooth_number
        update_tor = mytool.get(prop_name)
        disp_angle = update_tor - current_tor
        print('Current_tor', current_tor * (180/math.pi))
        print('Changed Tor:', update_tor * (180/math.pi))
        print('Disprity angle:', disp_angle * (180/math.pi))
        a = (M_orient.row[0][0], M_orient.row[1][0], M_orient.row[2][0])
        b = (M_orient.row[0][1], M_orient.row[1][1], M_orient.row[2][1])
        c = (M_orient.row[0][2], M_orient.row[1][2], M_orient.row[2][2])
        
        bpy.ops.transform.rotate(value=disp_angle, orient_axis='X', orient_type='LOCAL', orient_matrix=(a, b, c), orient_matrix_type='LOCAL', constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

    tooth_object.select_set(False)

    
class MyProperties(bpy.types.PropertyGroup):
    selected_object_name : bpy.props.StringProperty(name="")
    y_direction : bpy.props.FloatVectorProperty(name="Y axis direction of tooth in local coordinate", subtype='XYZ', precision=2, size=3, default=(0.0, 0.0,0.0))
    z_direction : bpy.props.FloatVectorProperty(name="Z axis direction of tooth in local coordinate", subtype='XYZ', precision=2, size=3, default=(0.0, 0.0,0.0))
    up_teeth_object_name : bpy.props.StringProperty(name="")
    down_teeth_object_name : bpy.props.StringProperty(name="")
    trim_cut_object_name : bpy.props.StringProperty(name="")
    tooth_name : bpy.props.StringProperty(name="")
    curve_collection_name_U : bpy.props.StringProperty(name="")
    curve_collection_name_D : bpy.props.StringProperty(name="")

    up_down : bpy.props.EnumProperty(
        name="UP/DOWN",
        description="Choose up or down side of teeth",
        items=[
            ('UP_', 'UP', 'It is UP side'),
            ('DOWN_', 'DOWN', 'It is DOWN side'),
        ]
    )

    quantity_of_teeth : bpy.props.EnumProperty(
        name="Quantity",
        description="Set the quantity of teeth",
        items=[
            ('16', '16', '16'),
            ('15', '15', '15'),
            ('14', '14', '14'),
            ('13', '13', '13'),
            ('12', '12', '12'),
            ('11', '11', '11'),
            ('10', '10', '10'),
            ('9', '9', '9'),
            ('8', '8', '8'),
            ('7', '7', '7'),
            ('6', '6', '6'),
            ('5', '5', '5'),
        ]
    )

    save_as_name:bpy.props.EnumProperty(
        name="Save Name",
        description="Save blender file with this name",
        items=[
            ('import_', 'import', 'Save import stage'),
            ('smooth_edge_', 'smooth edges', 'Save smooth edges stage'),
            ('sort_curves_', 'sort curves', 'Save sort curves stage'),
            ('adjust_', 'adjust curves', 'Save adjust curves stage'),
            ('intersection', 'find intersection', 'Save find intersection stage'),
            ('knife panel', 'knife panel', 'Save generate knife panel stage'),
            ('cut teeth', 'cut teeth', 'Save cut teeth stage'),
            ('add coordinate', 'add coordinate', 'Save add coordinate stage'),
            ('adjust orientation', 'adjust orientation', 'Save adjust orientation stage'),
        ]
    )

    picked_tooth_name:bpy.props.EnumProperty(
        name="Picked Tooth Name",
        description="Stroe the picked tooth name dynamicly",
        items=get_picked_tooth_name
    )

    scale_up_arch : bpy.props.BoolProperty(name="scale up arch or not", default=False)
    scale_down_arch : bpy.props.BoolProperty(name="scale down arch or not", default=False)


    factor : bpy.props.FloatProperty(name="extrude_factor", 
                description="The Factor control resize scale", 
                default=1.0, 
                min=1.0, max=1.3, 
                soft_min=1.0, soft_max=1.3, 
                step=0.01)

    U_28: bpy.props.BoolProperty(name="28", description="Lost Tooth 28", default=False)
    U_27: bpy.props.BoolProperty(name="27", description="Lost Tooth 27", default=False)
    U_26: bpy.props.BoolProperty(name="26", description="Lost Tooth 26", default=False)
    U_25: bpy.props.BoolProperty(name="25", description="Lost Tooth 25", default=False)
    U_24: bpy.props.BoolProperty(name="24", description="Lost Tooth 24", default=False)
    U_23: bpy.props.BoolProperty(name="23", description="Lost Tooth 23", default=False)
    U_22: bpy.props.BoolProperty(name="22", description="Lost Tooth 22", default=False)
    U_21: bpy.props.BoolProperty(name="21", description="Lost Tooth 21", default=False)
    U_18: bpy.props.BoolProperty(name="18", description="Lost Tooth 18", default=False)
    U_17: bpy.props.BoolProperty(name="17", description="Lost Tooth 17", default=False)
    U_16: bpy.props.BoolProperty(name="16", description="Lost Tooth 16", default=False)
    U_15: bpy.props.BoolProperty(name="15", description="Lost Tooth 15", default=False)
    U_14: bpy.props.BoolProperty(name="14", description="Lost Tooth 14", default=False)
    U_13: bpy.props.BoolProperty(name="13", description="Lost Tooth 13", default=False)
    U_13: bpy.props.BoolProperty(name="13", description="Lost Tooth 13", default=False)
    U_12: bpy.props.BoolProperty(name="12", description="Lost Tooth 12", default=False)
    U_11: bpy.props.BoolProperty(name="11", description="Lost Tooth 11", default=False)

    D_38: bpy.props.BoolProperty(name="38", description="Lost Tooth 38", default=False)
    D_37: bpy.props.BoolProperty(name="37", description="Lost Tooth 37", default=False)
    D_36: bpy.props.BoolProperty(name="36", description="Lost Tooth 36", default=False)
    D_35: bpy.props.BoolProperty(name="35", description="Lost Tooth 35", default=False)
    D_34: bpy.props.BoolProperty(name="34", description="Lost Tooth 34", default=False)
    D_33: bpy.props.BoolProperty(name="33", description="Lost Tooth 33", default=False)
    D_32: bpy.props.BoolProperty(name="32", description="Lost Tooth 32", default=False)
    D_31: bpy.props.BoolProperty(name="31", description="Lost Tooth 31", default=False)
    D_48: bpy.props.BoolProperty(name="48", description="Lost Tooth 48", default=False)
    D_47: bpy.props.BoolProperty(name="47", description="Lost Tooth 47", default=False)
    D_46: bpy.props.BoolProperty(name="46", description="Lost Tooth 46", default=False)
    D_45: bpy.props.BoolProperty(name="45", description="Lost Tooth 45", default=False)
    D_44: bpy.props.BoolProperty(name="44", description="Lost Tooth 44", default=False)
    D_43: bpy.props.BoolProperty(name="43", description="Lost Tooth 43", default=False)
    D_43: bpy.props.BoolProperty(name="43", description="Lost Tooth 43", default=False)
    D_42: bpy.props.BoolProperty(name="42", description="Lost Tooth 42", default=False)
    D_41: bpy.props.BoolProperty(name="41", description="Lost Tooth 41", default=False)

    UP_tipTorExpand: bpy.props.BoolProperty(name="Tip Tor Expand", description="Expand Tip and Torque Panel", default=False)
    Tip_11: bpy.props.FloatProperty(name="tip11", description="Tip value of Tooth 11", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_11'))
    Tor_11: bpy.props.FloatProperty(name="tor11", description="Torque value of Tooth 11", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_11'))
    Tip_12: bpy.props.FloatProperty(name="tip12", description="Tip value of Tooth 12", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_12'))
    Tor_12: bpy.props.FloatProperty(name="tor12", description="Torque value of Tooth 12", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_12'))
    Tip_13: bpy.props.FloatProperty(name="tip13", description="Tip value of Tooth 13", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_13'))
    Tor_13: bpy.props.FloatProperty(name="tor14", description="Torque value of Tooth 13", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_13'))
    Tip_14: bpy.props.FloatProperty(name="tip14", description="Tip value of Tooth 14", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_14'))
    Tor_14: bpy.props.FloatProperty(name="tor15", description="Torque value of Tooth 14", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_14'))
    Tip_15: bpy.props.FloatProperty(name="tip15", description="Tip value of Tooth 15", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_15'))
    Tor_15: bpy.props.FloatProperty(name="tor15", description="Torque value of Tooth 15", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_15'))
    Tip_16: bpy.props.FloatProperty(name="tip16", description="Tip value of Tooth 16", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_16'))
    Tor_16: bpy.props.FloatProperty(name="tor16", description="Torque value of Tooth 16", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_16'))
    Tip_17: bpy.props.FloatProperty(name="tip17", description="Tip value of Tooth 17", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_17'))
    Tor_17: bpy.props.FloatProperty(name="tor17", description="Torque value of Tooth 17", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_17'))
    Tip_18: bpy.props.FloatProperty(name="tip18", description="Tip value of Tooth 18", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_18'))
    Tor_18: bpy.props.FloatProperty(name="tor18", description="Torque value of Tooth 18", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_18'))
    
    Tip_21: bpy.props.FloatProperty(name="tip21", description="Tip value of Tooth 21", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_21'))
    Tor_21: bpy.props.FloatProperty(name="tor21", description="Torque value of Tooth 21", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_21'))
    Tip_22: bpy.props.FloatProperty(name="tip22", description="Tip value of Tooth 22", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_22'))
    Tor_22: bpy.props.FloatProperty(name="tor22", description="Torque value of Tooth 22", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_22'))
    Tip_23: bpy.props.FloatProperty(name="tip23", description="Tip value of Tooth 23", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_23'))
    Tor_23: bpy.props.FloatProperty(name="tor24", description="Torque value of Tooth 23", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_23'))
    Tip_24: bpy.props.FloatProperty(name="tip24", description="Tip value of Tooth 24", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_24'))
    Tor_24: bpy.props.FloatProperty(name="tor25", description="Torque value of Tooth 24", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_24'))
    Tip_25: bpy.props.FloatProperty(name="tip25", description="Tip value of Tooth 25", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_25'))
    Tor_25: bpy.props.FloatProperty(name="tor25", description="Torque value of Tooth 25", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_25'))
    Tip_26: bpy.props.FloatProperty(name="tip26", description="Tip value of Tooth 26", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_26'))
    Tor_26: bpy.props.FloatProperty(name="tor26", description="Torque value of Tooth 26", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_26'))
    Tip_27: bpy.props.FloatProperty(name="tip27", description="Tip value of Tooth 27", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_27'))
    Tor_27: bpy.props.FloatProperty(name="tor27", description="Torque value of Tooth 27", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_27'))
    Tip_28: bpy.props.FloatProperty(name="tip28", description="Tip value of Tooth 28", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_28'))
    Tor_28: bpy.props.FloatProperty(name="tor28", description="Torque value of Tooth 28", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_28'))
    
    Tip_31: bpy.props.FloatProperty(name="tip31", description="Tip value of Tooth 31", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_31'))
    Tor_31: bpy.props.FloatProperty(name="tor31", description="Torque value of Tooth 31", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_31'))
    Tip_32: bpy.props.FloatProperty(name="tip32", description="Tip value of Tooth 32", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_32'))
    Tor_32: bpy.props.FloatProperty(name="tor32", description="Torque value of Tooth 32", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_32'))
    Tip_33: bpy.props.FloatProperty(name="tip33", description="Tip value of Tooth 33", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_33'))
    Tor_33: bpy.props.FloatProperty(name="tor34", description="Torque value of Tooth 33", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_33'))
    Tip_34: bpy.props.FloatProperty(name="tip34", description="Tip value of Tooth 34", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_34'))
    Tor_34: bpy.props.FloatProperty(name="tor35", description="Torque value of Tooth 34", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_34'))
    Tip_35: bpy.props.FloatProperty(name="tip35", description="Tip value of Tooth 35", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_35'))
    Tor_35: bpy.props.FloatProperty(name="tor35", description="Torque value of Tooth 35", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_35'))
    Tip_36: bpy.props.FloatProperty(name="tip36", description="Tip value of Tooth 36", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_36'))
    Tor_36: bpy.props.FloatProperty(name="tor36", description="Torque value of Tooth 36", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_36'))
    Tip_37: bpy.props.FloatProperty(name="tip37", description="Tip value of Tooth 37", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_37'))
    Tor_37: bpy.props.FloatProperty(name="tor37", description="Torque value of Tooth 37", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_37'))
    Tip_38: bpy.props.FloatProperty(name="tip38", description="Tip value of Tooth 38", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_38'))
    Tor_38: bpy.props.FloatProperty(name="tor38", description="Torque value of Tooth 38", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_38'))
    
    Tip_41: bpy.props.FloatProperty(name="tip41", description="Tip value of Tooth 41", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_41'))
    Tor_41: bpy.props.FloatProperty(name="tor41", description="Torque value of Tooth 41", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_41'))
    Tip_42: bpy.props.FloatProperty(name="tip42", description="Tip value of Tooth 42", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_42'))
    Tor_42: bpy.props.FloatProperty(name="tor42", description="Torque value of Tooth 42", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_42'))
    Tip_43: bpy.props.FloatProperty(name="tip43", description="Tip value of Tooth 43", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_43'))
    Tor_43: bpy.props.FloatProperty(name="tor44", description="Torque value of Tooth 43", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_43'))
    Tip_44: bpy.props.FloatProperty(name="tip44", description="Tip value of Tooth 44", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_44'))
    Tor_44: bpy.props.FloatProperty(name="tor45", description="Torque value of Tooth 44", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_44'))
    Tip_45: bpy.props.FloatProperty(name="tip45", description="Tip value of Tooth 45", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_45'))
    Tor_45: bpy.props.FloatProperty(name="tor45", description="Torque value of Tooth 45", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_45'))
    Tip_46: bpy.props.FloatProperty(name="tip46", description="Tip value of Tooth 46", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_46'))
    Tor_46: bpy.props.FloatProperty(name="tor46", description="Torque value of Tooth 46", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_46'))
    Tip_47: bpy.props.FloatProperty(name="tip47", description="Tip value of Tooth 47", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_47'))
    Tor_47: bpy.props.FloatProperty(name="tor47", description="Torque value of Tooth 47", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_47'))
    Tip_48: bpy.props.FloatProperty(name="tip48", description="Tip value of Tooth 48", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'A_48'))
    Tor_48: bpy.props.FloatProperty(name="tor48", description="Torque value of Tooth 48", default=0.0, min=-180, max=180, step=100, precision=2, options={'ANIMATABLE'}, subtype='ANGLE', unit='NONE', update=lambda s, c: update(s, c, 'B_48'))

class MESH_TO_ready_seperate_teeth(bpy.types.Operator):
    """Read for seperating teeth"""
    bl_idname = "mesh.ready_seperating"
    bl_label = "Read Seperating"

    def execute(self, context):
        filename = os.path.expanduser('~') + "\\AppData\\Roaming\\Blender Foundation\\Blender\\2.83\\scripts\\addons\\pie_menu_editor\\scripts\\prepare_tooth_seperation.py" 
        exec(compile(open(filename).read(), filename, 'exec'))
        return {'FINISHED'} 
        
class MESH_TO_seperate_Teeth(bpy.types.Operator):
    """Seperate Teeth"""
    bl_idname = "mesh.seperate_teeth"
    bl_label = "Seperate Teeth"

    def execute(self, context):
        filename = os.path.expanduser('~') + "\\AppData\\Roaming\\Blender Foundation\\Blender\\2.83\\scripts\\addons\\pie_menu_editor\\scripts\\tooth_seperation.py" 
        exec(compile(open(filename).read(), filename, 'exec'))
        return {'FINISHED'} 
    
class MESH_TO_draw_arch(bpy.types.Operator):
    """Draw Arch Cut Thread"""
    bl_idname = "mesh.draw_arch"
    bl_label = "Draw Arch"

    def execute(self, context):
        if len(context.selected_objects) == 1:
            scene = context.scene
            mytool = scene.my_tool
            mytool.trim_cut_object_name = bpy.context.object.name

            trim_cut_object_name = bpy.context.object.name
            trim_cut_object = bpy.data.objects[trim_cut_object_name]
            context.scene.tool_settings.use_snap = True

            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

            # set EDIT mode's select mode to "vertex select" 
            context.tool_settings.mesh_select_mode = (True , False , False)

            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            context.scene.tool_settings.use_snap = True
            context.scene.tool_settings.snap_elements = {'FACE'}
            context.scene.tool_settings.use_proportional_edit = False

            bpy.ops.object.mode_set(mode="EDIT") #Activating Edit mode
            bpy.ops.mesh.select_all(action = 'DESELECT') #Deselecting all
            bpy.ops.object.mode_set(mode="OBJECT") #Going back to Object mode

            bpy.ops.object.select_all(action='INVERT')
            bpy.ops.object.hide_view_set(unselected=False)

            bpy.ops.object.select_all(action='DESELECT') #deselect all object

            context.view_layer.objects.active = trim_cut_object
            trim_cut_object.select_set(True)
            
            bpy.ops.ed.undo_push()

            bpy.ops.mesh.primitive_vert_add()

            bpy.context.object.name = "loop"

            for obj in bpy.context.selected_objects:
                obj.name = "loop"
                obj.data.name = "loop"

            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(5, 0, 0), "orient_type":'VIEW',  "orient_matrix_type":'VIEW', "constraint_axis":(True, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})

            bpy.ops.mesh.select_all(action='INVERT')

            bpy.ops.object.vertex_group_add()
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_assign()

            bpy.ops.object.skin_root_mark()

            bpy.ops.mesh.select_all(action='INVERT')

            bpy.ops.object.editmode_toggle()

            for x in bpy.context.object.material_slots: #For all of the materials in the selected object:
                bpy.context.object.active_material_index = 0 #select the top material
                bpy.ops.object.material_slot_remove() #delete it

            #changing colour of tool

            activeObject = bpy.context.active_object #Set active object to variable
            mat = bpy.data.materials.new(name="MaterialName") #set new material to variable
            activeObject.data.materials.append(mat) #add the material to the object

            bpy.context.object.active_material.diffuse_color = (0.121583, 0.144091, 0.8, 0.729885)

            bpy.ops.object.select_all(action='DESELECT') #deselect all object

            bpy.data.objects['loop'].select_set(True)
            obj = bpy.context.window.scene.objects['loop']
            bpy.context.view_layer.objects.active = obj

            bpy.ops.object.editmode_toggle()

            #set parameters

            bpy.ops.object.modifier_add(type='SUBSURF')
            bpy.context.object.modifiers["Subdivision"].levels = 3

            bpy.ops.object.modifier_add(type='SHRINKWRAP')
            bpy.context.object.modifiers["Shrinkwrap"].target = trim_cut_object
            bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'NEAREST_SURFACEPOINT'
            bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'ABOVE_SURFACE'
            bpy.context.object.modifiers["Shrinkwrap"].offset = 0.2

            bpy.context.object.modifiers["Shrinkwrap"].show_on_cage = True
            bpy.context.object.modifiers["Subdivision"].show_on_cage = True


            bpy.ops.object.modifier_add(type='SMOOTH')
            bpy.context.object.modifiers["Smooth"].iterations = 4
            bpy.context.object.modifiers["Smooth"].show_in_editmode = True
            bpy.context.object.modifiers["Smooth"].show_on_cage = True
            bpy.context.object.modifiers["Smooth"].factor = 0.5

            bpy.ops.object.modifier_add(type='SKIN')
            bpy.ops.transform.skin_resize(value=(0.8, 0.8, 0.8), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

            bpy.ops.wm.tool_set_by_id(name="builtin.select")

            bpy.ops.ed.undo_push()
        return {'FINISHED'}   
    
class MESH_TO_trim_cut(bpy.types.Operator):
    """Trim Cut By Arch drawing"""
    bl_idname = "mesh.trim_cut"
    bl_label = "Trim Cut"

    def execute(self, context):
        bpy.ops.scene.saveblend(filename="preSeperation")
        if context.mode == 'EDIT_MESH':
            scene = context.scene
            mytool = scene.my_tool

            trim_cut_object_name = mytool.trim_cut_object_name
            trim_cut_object = bpy.data.objects[trim_cut_object_name]

            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

            bpy.context.tool_settings.mesh_select_mode = (True , False , False)
            bpy.ops.object.mode_set(mode="OBJECT") 

            bpy.ops.object.select_all(action='DESELECT') 
            bpy.context.view_layer.objects.active = trim_cut_object
            trim_cut_object.select_set(True)

            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.editmode_toggle()

            bpy.ops.object.select_all(action='DESELECT') #deselect all object

            bpy.data.objects['loop'].select_set(True)
            obj = bpy.context.window.scene.objects['loop']
            bpy.context.view_layer.objects.active = obj
            bpy.context.scene.tool_settings.use_mesh_automerge = False

            bpy.ops.ed.undo_push()

            bpy.ops.object.modifier_remove(modifier="Skin")

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.subdivide(quadcorner='INNERVERT')
            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.ops.object.convert(target='MESH')


            bpy.ops.object.select_all(action='DESELECT') #deselect all object


            bpy.data.objects['loop'].select_set(True)
            obj = bpy.context.window.scene.objects['loop']
            bpy.context.view_layer.objects.active = obj

            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles(threshold=0.5)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.editmode_toggle()

            bpy.ops.object.duplicate_move()
            bpy.context.object.name = "inside_loop"


            bpy.ops.object.select_all(action='DESELECT') #deselect all object


            bpy.data.objects['loop'].select_set(True)
            obj = bpy.context.window.scene.objects['loop']
            bpy.context.view_layer.objects.active = obj

            bpy.ops.object.modifier_add(type='SHRINKWRAP')
            bpy.context.object.modifiers["Shrinkwrap"].target = trim_cut_object
            bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'ABOVE_SURFACE'
            bpy.context.object.modifiers["Shrinkwrap"].offset = 0.8
            bpy.ops.object.modifier_add(type='SMOOTH')
            bpy.context.object.modifiers["Smooth"].show_in_editmode = True
            bpy.context.object.modifiers["Smooth"].iterations = 5
            bpy.context.object.modifiers["Shrinkwrap"].show_on_cage = True
            bpy.context.object.modifiers["Smooth"].show_on_cage = True

            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='cubic', lock_x=False, lock_y=False, lock_z=False)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.editmode_toggle()

            bpy.ops.object.convert(target='MESH')


            bpy.ops.object.modifier_add(type='SUBSURF')

            bpy.ops.object.modifier_add(type='SHRINKWRAP')
            bpy.context.object.modifiers["Shrinkwrap"].target = trim_cut_object
            bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'ABOVE_SURFACE'
            bpy.context.object.modifiers["Shrinkwrap"].show_on_cage = True
            bpy.context.object.modifiers["Shrinkwrap"].offset = 0.4
            bpy.ops.object.modifier_add(type='SMOOTH')
            bpy.context.object.modifiers["Smooth"].iterations = 5
            bpy.context.object.modifiers["Smooth"].show_in_editmode = True
            bpy.context.object.modifiers["Smooth"].show_on_cage = True


            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='cubic', lock_x=False, lock_y=False, lock_z=False)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.editmode_toggle()


            bpy.ops.object.convert(target='MESH')



            #loop inside step 2


            bpy.ops.object.select_all(action='DESELECT') #deselect all object


            bpy.data.objects['inside_loop'].select_set(True)
            obj = bpy.context.window.scene.objects['inside_loop']
            bpy.context.view_layer.objects.active = obj


            bpy.ops.object.modifier_add(type='SHRINKWRAP')
            bpy.context.object.modifiers["Shrinkwrap"].target = trim_cut_object
            bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'ABOVE_SURFACE'
            bpy.context.object.modifiers["Shrinkwrap"].show_on_cage = True
            bpy.context.object.modifiers["Shrinkwrap"].offset = -2.3
            bpy.ops.object.modifier_add(type='CORRECTIVE_SMOOTH')
            bpy.context.object.modifiers["CorrectiveSmooth"].show_in_editmode = True
            bpy.context.object.modifiers["CorrectiveSmooth"].show_on_cage = True
            bpy.context.object.modifiers["CorrectiveSmooth"].iterations = 50


            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='cubic', lock_x=False, lock_y=False, lock_z=False)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.editmode_toggle()

            bpy.ops.object.convert(target='MESH')


            bpy.ops.object.modifier_add(type='SHRINKWRAP')
            bpy.context.object.modifiers["Shrinkwrap"].target = trim_cut_object
            bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'ABOVE_SURFACE'
            bpy.context.object.modifiers["Shrinkwrap"].offset = -1.2

            bpy.ops.object.modifier_add(type='SMOOTH')
            bpy.context.object.modifiers["Smooth"].iterations = 5


            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='cubic', lock_x=False, lock_y=False, lock_z=False)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.editmode_toggle()

            bpy.ops.object.convert(target='MESH')



            bpy.ops.object.select_all(action='DESELECT') #deselect all object


            bpy.data.objects['loop'].select_set(True)
            obj = bpy.context.window.scene.objects['loop']
            bpy.context.view_layer.objects.active = obj


            bpy.data.objects['inside_loop'].select_set(True)
            obj = bpy.context.window.scene.objects['inside_loop']
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.join()

            
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')

            bpy.ops.mesh.bridge_edge_loops()

            obj = bpy.context.object
            vg = obj.vertex_groups.get('Group')

            if vg is not None:
                obj.vertex_groups.remove(vg)
                
            bpy.ops.object.vertex_group_add()
            obj.vertex_groups[-1].name="Ribbon"
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_assign()

            bpy.ops.object.mode_set(mode="OBJECT") #Going back to Object mode

            #join cutting tool and target model and cut

            bpy.context.view_layer.objects.active = trim_cut_object
            trim_cut_object.select_set(True)

            bpy.ops.object.join()
            bpy.ops.object.editmode_toggle()

            #show problem areas

            bpy.ops.mesh.intersect()
            bpy.ops.mesh.rip_move()

            bpy.ops.mesh.edge_split()

            bpy.ops.mesh.hide(unselected=False)

            # set EDIT mode's select mode to "vertex select" 
            bpy.context.tool_settings.mesh_select_mode = (False , False , True)

            #changing colour of tool

            activeObject = bpy.context.active_object #Set active object to variable
            mat = bpy.data.materials.get("MaterialName")
            if mat is None:
                mat = bpy.data.materials.new(name="MaterialName") #set new material to variable
            activeObject.data.materials.append(mat) #add the material to the object

            bpy.context.object.active_material.diffuse_color = (0.121583, 0.144091, 0.8, 1)

            bpy.ops.object.vertex_group_set_active(group='Ribbon')
            bpy.ops.object.vertex_group_select()

            bpy.ops.mesh.delete(type='VERT')

            obj = bpy.context.object

            vg = obj.vertex_groups.get('Ribbon')

            if vg is not None:
                obj.vertex_groups.remove(vg)
                
            bpy.ops.ed.undo_push()

        return {'FINISHED'}

class MESH_TO_clean(bpy.types.Operator):
    """Clean mesh After Trim Cut"""
    bl_idname = "mesh.clean"
    bl_label = "Clean"

    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            scene = context.scene
            mytool = scene.my_tool

            trim_cut_object_name = mytool.trim_cut_object_name
            trim_cut_object = bpy.data.objects[trim_cut_object_name]

            bpy.context.tool_settings.mesh_select_mode = (True , False , False)

            bpy.ops.mesh.select_linked(delimit=set())
            bpy.ops.mesh.reveal()

            bpy.ops.mesh.select_all(action='INVERT')
            bpy.ops.mesh.delete(type='VERT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.delete_loose()

            bpy.ops.mesh.reveal()
            bpy.ops.mesh.select_non_manifold()

            bpy.ops.mesh.dissolve_limited(angle_limit=0.0872665, use_dissolve_boundaries=True)

            bpy.ops.mesh.select_all(action='DESELECT')

            bpy.ops.object.editmode_toggle()

            bpy.ops.object.select_all(action='DESELECT') #deselect all object

            for x in bpy.context.object.material_slots: #For all of the materials in the selected object:
                bpy.context.object.active_material_index = 0 #select the top material
                bpy.ops.object.material_slot_remove() #delete it

            bpy.ops.object.shade_flat()

            bpy.ops.object.select_all(action='DESELECT') #deselect all object

            bpy.context.view_layer.objects.active = trim_cut_object
            trim_cut_object.select_set(True)

            bpy.ops.ed.undo_push()

            bpy.ops.object.select_all(action='DESELECT')
            context.scene.cursor.location = mathutils.Vector((0.0, 0.0, 0.0))
            context.scene.cursor.rotation_euler = mathutils.Vector((0.0, 0.0, 0.0))
            context.view_layer.objects.active = trim_cut_object
            trim_cut_object.select_set(True)
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

        return {'FINISHED'}

class MESH_TO_make_base(bpy.types.Operator):
    """Make upper/lower teeth base"""
    bl_idname = "mesh.make_base"
    bl_label = "Make Base"

    def execute(self, context):
        if len(context.selected_objects) == 1:
            scene = context.scene
            mytool = scene.my_tool

            up_down = mytool.up_down
            bpy.context.scene.transform_orientation_slots[0].type = "GLOBAL"

            # set EDIT mode's select mode to "vertex select" 
            bpy.context.tool_settings.mesh_select_mode = (True , False , False)

            bpy.context.scene.tool_settings.use_snap = False
            bpy.context.scene.tool_settings.snap_elements = {'FACE'}
            bpy.context.scene.tool_settings.use_proportional_edit_objects = False
            bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'

            bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')

            bpy.ops.object.mode_set(mode="EDIT") #Activating Edit mode

            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.delete_loose()

            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles(threshold=0.0001)
            bpy.ops.mesh.select_all(action='DESELECT')

            bpy.ops.mesh.select_non_manifold()

            bpy.ops.mesh.dissolve_limited(angle_limit=0.0872665, use_dissolve_boundaries=True)

            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.mesh.select_all(action='DESELECT')

            bpy.ops.mesh.select_all(action='DESELECT')

            bpy.ops.mesh.select_non_manifold()

            bpy.ops.mesh.delete(type='FACE')

            bpy.ops.mesh.select_non_manifold()

            bpy.ops.mesh.looptools_relax(input='selected', interpolation='linear', iterations='25', regular=True)

            obj = bpy.context.object

            vg = obj.vertex_groups.get('Group')

            if vg is not None:
                obj.vertex_groups.remove(vg)
                
            bpy.ops.object.vertex_group_add()
            obj.vertex_groups[-1].name="Border"
            
            bpy.ops.object.vertex_group_assign()
            if up_down == 'UP_':
                bpy.ops.transform.translate(value=(0, 0, 0.2), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
            else:
                bpy.ops.transform.translate(value=(0, 0, -0.2), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

            bpy.ops.mesh.delete_loose()
            bpy.ops.mesh.select_non_manifold()

            bpy.ops.mesh.select_more()
            bpy.ops.mesh.select_more()

            bpy.ops.object.vertex_group_deselect()

            bpy.ops.mesh.vertices_smooth(factor=0.5, repeat=3)

            obj = bpy.context.object

            vg = obj.vertex_groups.get('Border')

            if vg is not None:
                obj.vertex_groups.remove(vg)

            bpy.ops.mesh.select_all(action='DESELECT')

            bpy.ops.mesh.select_non_manifold()

            bpy.ops.object.vertex_group_add()
            obj.vertex_groups[-1].name="Whole"
            bpy.ops.object.vertex_group_assign()

            if up_down == 'UP_':
                bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, 12), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
            else:
                bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, -12), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})

            bpy.ops.transform.resize(value=(1, 1, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
            bpy.ops.mesh.fill()
            bpy.ops.mesh.dissolve_limited()

            obj = bpy.context.object

            vg = obj.vertex_groups.get('Group')

            if vg is not None:
                obj.vertex_groups.remove(vg)
                
            bpy.ops.object.vertex_group_add()
            obj.vertex_groups[-1].name="Base"
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_assign()

            bpy.ops.mesh.select_all(action='SELECT')

            bpy.ops.mesh.normals_make_consistent(inside=False)

            bpy.ops.mesh.select_all(action='DESELECT')

            bpy.ops.object.vertex_group_select()

            bpy.ops.object.editmode_toggle()
        bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_apply_base(bpy.types.Operator):
    """Apply edit base"""
    bl_idname = "mesh.apply_base"
    bl_label = "Apply Base"

    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            bpy.ops.scene.saveblend(filename="preSeperation")
            bpy.ops.mesh.select_all(action='DESELECT')
            if context.object.vertex_groups.get('Whole') is not None:
                context.object.vertex_groups.active = context.object.vertex_groups['Whole']
                bpy.ops.object.vertex_group_select()
                bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)

            bpy.ops.object.mode_set(mode='OBJECT')
        
        if context.mode == 'OBJECT':
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            if context.object.vertex_groups.get('Whole') is not None:
                context.object.vertex_groups.active = context.object.vertex_groups['Whole']
                bpy.ops.object.vertex_group_select()
                bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.ed.undo_push()
        return {'FINISHED'}  

class MESH_TO_base_move_up(bpy.types.Operator):
    """Move up base"""
    bl_idname = "mesh.move_up"
    bl_label = "Move Up"

    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            bpy.ops.object.vertex_group_set_active(group='Base')
            bpy.ops.object.vertex_group_select()
            bpy.ops.transform.translate(value=(0, 0, 2), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
            
        if context.mode == 'OBJECT':
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group='Base')
            bpy.ops.object.vertex_group_select()
            bpy.ops.transform.translate(value=(0, 0, 2), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        bpy.ops.ed.undo_push()
        return {'FINISHED'}  

class MESH_TO_base_move_donw(bpy.types.Operator):
    """Move down base"""
    bl_idname = "mesh.move_down"
    bl_label = "Move Down"

    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            bpy.ops.object.vertex_group_set_active(group='Base')
            bpy.ops.object.vertex_group_select()
            bpy.ops.transform.translate(value=(0, 0, -2), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
            
        if context.mode == 'OBJECT':
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_set_active(group='Base')
            bpy.ops.object.vertex_group_select()
            bpy.ops.transform.translate(value=(0, 0, -2), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)   
        bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_smooth_tooth_edge(bpy.types.Operator):
    """Smooth the edge of a selected single"""
    bl_idname = "mesh.smooth_tooth_edge"
    bl_label = "Smooth Tooth Edge"
    
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            scene = context.scene
            mytool = scene.my_tool
            up_down = mytool.up_down

            # store main object name into my properity
            if up_down == 'UP_':
                mytool.up_teeth_object_name = bpy.context.object.name 
            else:
                mytool.down_teeth_object_name = bpy.context.object.name
            # select the whole tooth as main object(initilize enviroment)
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Collection']
            mainObjectName = bpy.context.object.name
            sysGaveName = mainObjectName + '.001'

            bpy.ops.object.editmode_toggle()        # enter 'EDIT_MESH' mode
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.editmode_toggle()        # return 'OBJECT' mode

            context.view_layer.objects.active = bpy.data.objects[mainObjectName]
            bpy.data.objects[mainObjectName].select_set(True)

            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

            txtfile = exec_read_global_peremeter(globals()['txtfile'],'txtfile')              
            # read index file
            f = open(txtfile,'r')
            arr = f.readlines() 
            f.close()
    
            # in each tooth:
            for line_index, line in enumerate(arr):
                # get vertices index and store them
                line = line.strip('\n')
                line = line.rstrip(',')
                # print(line_index, 'This is a new line')
                data = line.split(',')
                data_index = list(map(int, data))
                
                if line_index != 0:
                    for index in data_index:
                        bpy.data.objects[mainObjectName].data.vertices[index].select = True
    
                    bpy.ops.object.editmode_toggle()        # enter 'EDIT_MESH' mode 
                    # get selected tooth outline and store it into vertex group
                    bpy.ops.mesh.region_to_loop()
                    bpy.ops.object.vertex_group_add()
                    bpy.data.objects[mainObjectName].vertex_groups['Group'].name = 'Ori_Outline_' + str(line_index-1)
                    bpy.ops.object.vertex_group_assign()
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.object.editmode_toggle()        # return 'OBJECT' mode
            s_index = ''
            for vertex_group in bpy.data.objects[mainObjectName].vertex_groups:
                if vertex_group.name.startswith('Ori_Outline_'):
                    temp_name = vertex_group.name
                    split_name = vertex_group.name.split('_')
                    s_index = split_name[2]
                else:
                    continue
                bpy.ops.object.editmode_toggle()        # enter 'EDIT_MESH' mode
                bpy.ops.object.vertex_group_set_active(group=temp_name)
                bpy.ops.object.vertex_group_select()
                # bpy.ops.object.vertex_group_remove()
                bpy.ops.mesh.duplicate(mode=1)
                bpy.ops.mesh.separate(type='SELECTED')
                bpy.ops.object.editmode_toggle()        # return 'OBJECT' mode
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = bpy.data.objects[sysGaveName]
                bpy.data.objects[sysGaveName].select_set(True)
                bpy.ops.object.vertex_group_remove(all=True, all_unlocked=False)
                bpy.ops.object.editmode_toggle()        # enter 'EDIT_MESH' mode
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.dissolve_degenerate(threshold=0.15)
                bpy.ops.mesh.remove_doubles(threshold=1.3)
                # add surface subdivision modifier
                bpy.ops.object.modifier_add(type='SUBSURF')
                bpy.context.object.modifiers["Subdivision"].levels = 2
                # add shrinkwrap modifier
                bpy.ops.object.modifier_add(type='SHRINKWRAP')
                bpy.context.object.modifiers["Shrinkwrap"].target = bpy.data.objects[mainObjectName]
                bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'NEAREST_SURFACEPOINT'
                bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'ABOVE_SURFACE'
                bpy.context.object.modifiers["Shrinkwrap"].offset = 0.3
                # add smooth modifier 
                bpy.ops.object.modifier_add(type='SMOOTH')
                bpy.context.object.modifiers["Smooth"].iterations = 5 
                bpy.context.object.modifiers["Smooth"].show_in_editmode = True
                bpy.context.object.modifiers["Smooth"].show_on_cage = True
                bpy.context.object.modifiers["Smooth"].factor = 1.0
                
                bpy.context.object.modifiers["Shrinkwrap"].show_on_cage = True
                bpy.context.object.modifiers["Subdivision"].show_on_cage = True
                if up_down == 'UP_':
                    bpy.data.objects[sysGaveName].data.name = 'Curve_U_' + s_index
                    bpy.data.objects[sysGaveName].name = 'Curve_U_' + s_index
                else:
                    bpy.data.objects[sysGaveName].data.name = 'Curve_D_' + s_index
                    bpy.data.objects[sysGaveName].name = 'Curve_D_' + s_index

                bpy.ops.object.editmode_toggle()        # return 'OBJECT' mode
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = bpy.data.objects[mainObjectName]

            if up_down == 'UP_':
                if not bpy.data.collections.get('Curves_U'):
                    curves_coll = bpy.data.collections.new('Curves_U')
                    context.scene.collection.children.link(curves_coll)
                curves_collection = bpy.data.collections['Curves_U']
                mytool.curve_collection_name_U = 'Curves_U'
            else:
                if not bpy.data.collections.get('Curves_D'):
                    curves_coll = bpy.data.collections.new('Curves_D')
                    context.scene.collection.children.link(curves_coll)
                curves_collection = bpy.data.collections['Curves_D']
                mytool.curve_collection_name_D = 'Curves_D'

            # remove extra vertices and faces
            for obj in context.collection.objects:
                if obj.name.startswith('Curve'):
                    context.view_layer.objects.active = obj
                    obj.select_set(True)
                    remove_extra_vetrices_faces(obj)
                    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                    bpy.data.collections['Collection'].objects.unlink(obj)
                    curves_collection.objects.link(obj)
        
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = bpy.data.objects[mainObjectName]
            bpy.data.objects[mainObjectName].select_set(True)
            
            # remove original vertex group
            bpy.ops.object.vertex_group_remove(all=True, all_unlocked=False)        # remove all vertex groups
            bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_remove_curve(bpy.types.Operator):
    """"Remove A Single Curve"""
    bl_idname = "mesh.remove_curve"
    bl_label = "Remove"
    
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            if context.object.name.startswith('Curve'):
                bpy.ops.object.delete(use_global=False, confirm=False)
        return {'FINISHED'}

class MESH_TO_amend_curve(bpy.types.Operator):
    """"Amend A Single Curve"""
    bl_idname = "mesh.amend_curve"
    bl_label = "Amend"
    
    def execute(self, context):
        if len(bpy.context.selected_objects) == 1:
            if context.mode == 'EDIT_MESH':
                bpy.ops.view3d.toggle_xray()
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
            elif context.mode == 'OBJECT':
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.wm.tool_set_by_id(name="builtin.select")
                bpy.ops.view3d.toggle_xray()
                bpy.context.scene.tool_settings.use_snap = True
            else:
                bpy.ops.object.mode_set(mode='OBJECT')

        return {'FINISHED'}
    
class MESH_TO_draw_line(bpy.types.Operator):
    bl_idname = "mesh.draw_line"
    bl_label = "Draw Line"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        up_down = mytool.up_down

        if len(bpy.context.selected_objects) == 1:
            if bpy.context.object.name == mytool.up_teeth_object_name:
                curve_collection = bpy.data.collections[mytool.curve_collection_name_U]
                prefix = 'Curve_U_'
                mian_obj = bpy.context.object
                bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']

            elif bpy.context.object.name == mytool.down_teeth_object_name:
                curve_collection = bpy.data.collections[mytool.curve_collection_name_D]
                prefix = 'Curve_D_'
                mian_obj = bpy.context.object
                bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
            else:
                return {'FINISHED'}
            
            # set second collection as active
            bpy.context.scene.tool_settings.use_snap = True
            bpy.ops.mesh.primitive_vert_add()
            max_index  = 0
            for obj in context.collection.objects:
                if obj.name.startswith('Curve'):
                    index  = obj.name.lstrip(prefix)
                    if int(index) > max_index:
                        max_index = int(index)

            bpy.context.object.name = prefix + str(max_index+1)
            bpy.context.object.data.name = prefix + str(max_index+1)

            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(1, 0, 0), "orient_type":'VIEW',  "orient_matrix_type":'VIEW', "constraint_axis":(True, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})

            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.ops.ed.undo_push()

            bpy.ops.object.modifier_add(type='SUBSURF')
            bpy.context.object.modifiers["Subdivision"].levels = 2
            # add shrinkwrap modifier
            bpy.ops.object.modifier_add(type='SHRINKWRAP')
            bpy.context.object.modifiers["Shrinkwrap"].target = mian_obj
            bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'NEAREST_SURFACEPOINT'
            bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'ABOVE_SURFACE'
            bpy.context.object.modifiers["Shrinkwrap"].offset = 0.2
            # add smooth modifier 
            bpy.ops.object.modifier_add(type='SMOOTH')
            bpy.context.object.modifiers["Smooth"].iterations = 10 
            bpy.context.object.modifiers["Smooth"].show_in_editmode = True
            bpy.context.object.modifiers["Smooth"].show_on_cage = True
            bpy.context.object.modifiers["Smooth"].factor = 0.5
        
            bpy.context.object.modifiers["Shrinkwrap"].show_on_cage = True
            bpy.context.object.modifiers["Subdivision"].show_on_cage = True

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.wm.tool_set_by_id(name="builtin.select")
            bpy.ops.ed.undo_push()

        return {'FINISHED'}

class MESH_TO_apply_draw(bpy.types.Operator):
    """"Apply Draw Line"""
    bl_idname = "mesh.apply_draw"
    bl_label = "Appliy Draw"
    
    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
     
            bpy.context.scene.cursor.location = mathutils.Vector((0.0,0.0,0.0))
            bpy.context.scene.cursor.rotation_euler = mathutils.Vector((0,0,0))
            bpy.ops.object.select_all(action='DESELECT')
        return {'FINISHED'}

class MESH_TO_sort_curve(bpy.types.Operator):
    """sort curve name by x axis"""
    bl_idname = "mesh.sort_curve"
    bl_label = "Sort Curve"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        up_down = mytool.up_down
        if up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
            main_object = bpy.data.objects[mytool.up_teeth_object_name]
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
            main_object = bpy.data.objects[mytool.down_teeth_object_name]

        z_co_index = dict()
        bpy.ops.object.select_all(action='DESELECT')
        for index, obj in enumerate(context.collection.objects):
            if obj.name.startswith('Curve'):                                        # sort all the Curves by it's location
                context.view_layer.objects.active = obj
                obj.select_set(True)
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                location = obj.location
                
                if location[1] == 0 and location[0] < 0 :
                    angle = math.atan((-location[0])/location[1])
                    angle = math.pi / 2
                elif location[1] == 0 and location[0] > 0:
                    angle = math.atan((-location[0])/location[1])
                    angle = math.pi + math.pi / 2
                elif location[0] > 0 and location[1] > 0:
                    angle = math.atan((-location[0])/location[1])
                    angle = angle + 2 * math.pi
                elif location[0] > 0 and location[1] < 0:
                    angle = math.atan((-location[0])/location[1])
                    angle = angle + math.pi
                elif location[0] < 0 and location[1] < 0:
                    angle = math.atan((-location[0])/location[1])
                    angle = angle + math.pi
                else:
                    angle = math.atan((-location[0])/location[1])
                # print(obj.name,angle/math.pi*180)
                z_co_index[index] =  angle                      # store object index in collection                    
                obj.select_set(False)
        sort_list = sorted(z_co_index.items(), key=lambda item:item[1])
        print(sort_list)
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = main_object
        main_object.select_set(True)
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')


        for index, elem in enumerate(sort_list):
            key_value = elem[0]
            curve_obj = context.collection.objects[key_value]

            local = curve_obj.location
            if up_down == 'UP_':
                for vertice in main_object.data.vertices:
                    if abs(vertice.co[0] - local[0]) < 0.8 and abs(vertice.co[1] - local[1]) < 0.8 and vertice.co[2] < local[2]:
                        vertice.select = True
            else:
                for vertice in main_object.data.vertices:
                    if abs(vertice.co[0] - local[0]) < 0.8 and abs(vertice.co[1] - local[1]) < 0.8 and vertice.co[2] > local[2]:
                        vertice.select = True
            
            bpy.ops.object.mode_set(mode='EDIT')
            if context.object.data.total_vert_sel > 0:
                bpy.ops.object.vertex_group_add()                   
                main_object.vertex_groups['Group'].name = 'Origin_' + str(index)
                bpy.ops.object.vertex_group_assign()
            else:
                error_message = ("Curve: %s can not not select some vertices in up side or down side" % (curve_obj.name))
                self.report({'ERROR'}, error_message)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            curve_obj.show_name = True
            curve_obj.data.name = str(index)
            curve_obj.name = str(index)
            curve_obj.pass_index = index


        bpy.ops.ed.undo_push()

        return {'FINISHED'}

class MESH_TO_exchange_name(bpy.types.Operator):
    """exchange two object name"""  
    bl_idname = "mesh.exchange_name"
    bl_label = "Exchange name"
    
    def execute(self, context):

        scene = context.scene
        mytool = scene.my_tool

        if mytool.up_down == 'UP_':
            # bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
            mian_obj = bpy.data.objects[mytool.up_teeth_object_name]
        else:
            # bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
            mian_obj = bpy.data.objects[mytool.down_teeth_object_name]

        if len(bpy.context.selected_objects) == 2:
            context.view_layer.objects.active = mian_obj

            temp_name1 = bpy.context.selected_objects[0].name
            vertex_group_name1 = 'Origin_' + temp_name1
            mian_obj.vertex_groups[vertex_group_name1].name = 'none1'

            temp_name2 = bpy.context.selected_objects[1].name
            vertex_group_name2 = 'Origin_' + temp_name2
            mian_obj.vertex_groups[vertex_group_name2].name = 'none2'


            temp_index1 = bpy.context.selected_objects[0].pass_index
            temp_index2 = bpy.context.selected_objects[1].pass_index
            bpy.context.selected_objects[0].name = 'none1'
            bpy.context.selected_objects[1].name = 'none2'
            bpy.context.selected_objects[0].name = temp_name2
            bpy.context.selected_objects[1].name = temp_name1
            bpy.context.selected_objects[0].pass_index = temp_index2
            bpy.context.selected_objects[1].pass_index = temp_index1
            mian_obj.vertex_groups['none1'].name = vertex_group_name2
            mian_obj.vertex_groups['none2'].name = vertex_group_name1

            bpy.ops.object.select_all(action='DESELECT')



        bpy.ops.ed.undo_push()
        
        return{'FINISHED'}

class MESH_TO_to_sphere_curve(bpy.types.Operator):
    """to sphere the cutting tools"""  
    bl_idname = "mesh.to_sphere"
    bl_label = "Sphere Curves"
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
            mian_obj = bpy.data.objects[mytool.up_teeth_object_name]
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
            mian_obj = bpy.data.objects[mytool.down_teeth_object_name]
        
        for obj in bpy.context.collection.objects:
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.mesh.select_all(action = 'DESELECT')
            bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.ops.object.select_all(action = 'DESELECT')

        for index, obj in enumerate(context.collection.objects):
            if obj.pass_index == 0:
                obj2 = bpy.context.collection.objects[str(obj.pass_index+1)]
                bpy.context.view_layer.objects.active = obj2
                obj2.select_set(True)
                for vrt1 in obj.data.vertices:
                    for vrt2 in obj2.data.vertices:
                        dis_c = distance(vrt1.co, vrt2.co)
                        if dis_c < 3.2:             # distance threshold
                            vrt2.select = True
                bpy.ops.object.mode_set(mode = 'EDIT')
                bpy.ops.transform.tosphere(value=0.1, mirror=True, use_proportional_edit=True, proportional_edit_falloff='SPHERE', proportional_size=0.15, use_proportional_connected=False, use_proportional_projected=False)
                
                bpy.ops.mesh.select_all(action = 'DESELECT')
                bpy.ops.object.mode_set(mode = 'OBJECT')
                bpy.ops.object.select_all(action = 'DESELECT')
            elif obj.pass_index == (len(context.collection.objects)-1):
                print(obj.name)
                obj2 = context.collection.objects[str(obj.pass_index-1)]
                bpy.context.view_layer.objects.active = obj2
                obj2.select_set(True)
                for vrt1 in obj.data.vertices:
                    for vrt2 in obj2.data.vertices:
                        dis_c = distance(vrt1.co, vrt2.co)
                        if dis_c < 3.2:             # distance threshold
                            vrt2.select = True
                bpy.ops.object.mode_set(mode = 'EDIT')
                bpy.ops.transform.tosphere(value=0.1, mirror=True, use_proportional_edit=True, proportional_edit_falloff='SPHERE', proportional_size=0.15, use_proportional_connected=False, use_proportional_projected=False)
                
                bpy.ops.mesh.select_all(action = 'DESELECT')
                bpy.ops.object.mode_set(mode = 'OBJECT')
                bpy.ops.object.select_all(action = 'DESELECT')
            else:
                for vrt1 in obj.data.vertices:
                    obj2 = bpy.context.collection.objects[str(obj.pass_index+1)]  # right object 
                    bpy.context.view_layer.objects.active = obj2
                    obj2.select_set(True)
                    for vrt2 in obj2.data.vertices:
                        dis_c = distance(vrt1.co, vrt2.co)
                        if dis_c < 3.2:             # distance threshold
                            vrt2.select = True
                bpy.ops.object.mode_set(mode = 'EDIT')
                if obj.pass_index > 2 and obj.pass_index < len(context.collection.objects)-3:
                    bpy.ops.transform.tosphere(value=0.1, mirror=True, use_proportional_edit=True, proportional_edit_falloff='INVERSE_SQUARE', proportional_size=0.2, use_proportional_connected=False, use_proportional_projected=False)
                else : 
                    bpy.ops.transform.tosphere(value=0.1, mirror=True, use_proportional_edit=True, proportional_edit_falloff='SPHERE', proportional_size=0.15, use_proportional_connected=False, use_proportional_projected=False)
                    
                bpy.ops.mesh.select_all(action = 'DESELECT')
                bpy.ops.object.mode_set(mode = 'OBJECT')
                bpy.ops.object.select_all(action = 'DESELECT')
                
                for vrt1 in obj.data.vertices:
                    obj2 = bpy.context.collection.objects[str(obj.pass_index-1)]        # left object
                    bpy.context.view_layer.objects.active = obj2
                    obj2.select_set(True)
                    for vrt2 in obj2.data.vertices:
                        dis_c = distance(vrt1.co, vrt2.co)
                        if dis_c < 4:             # distance threshold
                            vrt2.select = True
                bpy.ops.object.mode_set(mode = 'EDIT')
                if obj.pass_index > 3 and obj.pass_index < len(context.collection.objects)-3:
                    bpy.ops.transform.tosphere(value=0.1, mirror=True, use_proportional_edit=True, proportional_edit_falloff='INVERSE_SQUARE', proportional_size=0.2, use_proportional_connected=False, use_proportional_projected=False)
                else:
                    bpy.ops.transform.tosphere(value=0.1, mirror=True, use_proportional_edit=True, proportional_edit_falloff='SPHERE', proportional_size=0.15, use_proportional_connected=False, use_proportional_projected=False)

                bpy.ops.mesh.select_all(action = 'DESELECT')
                bpy.ops.object.mode_set(mode = 'OBJECT')
                bpy.ops.object.select_all(action = 'DESELECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
        bpy.ops.object.select_all(action='DESELECT') 
        return{'FINISHED'}

class MESH_TO_adjust_curve(bpy.types.Operator):
    """" Adjust Vertex which on curve in edit mode"""
    bl_idname = "mesh.adjust_curve"
    bl_label = "Adjust Curve"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
            mian_obj = bpy.data.objects[mytool.up_teeth_object_name]
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
            mian_obj = bpy.data.objects[mytool.down_teeth_object_name]
        
        if context.mode == 'OBJECT':
            for obj in context.collection.objects:
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = obj
                obj.select_set(True)

                obj = bpy.context.object
                vertices = obj.data.vertices
                a = []
                b = [] 
                c = []
                for edge_key in obj.data.edge_keys:
                    a.append(edge_key[0])
                    a.append(edge_key[1])
                a.sort()
                print(a)
                from collections import Counter
                count = dict(Counter(a))
                b.append([key for key, value in count.items() if value == 4])
                c.append([key for key, value in count.items() if value == 1])
                print('b:',b)
                print('c:',c)

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.context.tool_settings.mesh_select_mode = (True, False, False)   
                bpy.ops.object.mode_set(mode='OBJECT')

                for index in c[0]:
                    vertices[index].select = True
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.delete(type='VERT')
                bpy.ops.object.mode_set(mode='OBJECT')

                if len(b[0]) == 1:
                    first_vertex = b[0][0]
                    connect_vertex = b[0][0]
                    edge_keys = obj.data.edge_keys.copy()
                    point = []
                    for i in range(len(obj.data.vertices)):
                        for edge_key in edge_keys:
                            if edge_key[0] == connect_vertex:
                #                print('connect_vertex', connect_vertex)

                                connect_vertex = edge_key[1]
                                edge_keys.remove(edge_key)
                #                print('edge_key',edge_key)
                                break
                            if edge_key[1] == connect_vertex:
                #                print('connect_vertex', connect_vertex)
                                connect_vertex = edge_key[0]
                                edge_keys.remove(edge_key)
                #                print('edge_key',edge_key)
                                break
                        print('last vertex',connect_vertex)
                        if connect_vertex != first_vertex:
                            point.append(connect_vertex)
                        else:
                            break
                #        print('edge_keys', edge_keys)
                #        print('===============')
                    if len(point) > 7:
                        point.append(first_vertex)
                        for index in point:
                            vertices[index].select = True
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='INVERT')
                        bpy.ops.mesh.delete(type='VERT')
                    else:
                        for index in point:
                            vertices[index].select = True
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.delete(type='VERT') 
                    bpy.ops.object.mode_set(mode='OBJECT')    
                #    print('point',point)

                if len(b[0]) == 2:
                    first_vertex = b[0][0]
                    second_vertex = b[0][1]
                    connect_vertex = b[0][0]
                    edge_keys = obj.data.edge_keys.copy()
                    total_point = []
                    sub_point = []
                    time = 0
                    for i in range(len(obj.data.vertices)):
                        for edge_key in edge_keys:
                            if edge_key[0] == connect_vertex:
                #                print('connect_vertex', connect_vertex)
                                connect_vertex = edge_key[1]
                                edge_keys.remove(edge_key)
                #                print('edge_key',edge_key)
                                break
                            if edge_key[1] == connect_vertex:
                #                print('connect_vertex', connect_vertex)
                                connect_vertex = edge_key[0]
                                edge_keys.remove(edge_key)
                #                print('edge_key',edge_key)
                                break
                #        print('last vertex',connect_vertex)
                        sub_point.append(connect_vertex)
                        if connect_vertex == first_vertex:
                            sub_point.remove(first_vertex)
                #            print('back to first_vertex',sub_point)
                            sub_point.clear()
                        if connect_vertex == second_vertex:
                #            print('sub_point',sub_point)
                            total_point.extend(sub_point)
                            sub_point.clear()
                            connect_vertex = first_vertex
                #        print('edge_keys', edge_keys)
                #        print('===============')
                #    print('total_point',total_point)
                    total_point.append(first_vertex)
                    for index in total_point:
                        vertices[index].select = True
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_all(action='INVERT')
                    bpy.ops.mesh.delete(type='VERT') 
                    bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')
                        
            for obj in context.collection.objects:
                context.view_layer.objects.active = obj
                obj.select_set(True)

            bpy.ops.object.mode_set(mode = 'EDIT')            # enter 'MESH_EDIT' mode
            bpy.ops.wm.tool_set_by_id(name="builtin.select")
            bpy.context.scene.tool_settings.use_snap = True
            bpy.context.scene.tool_settings.snap_elements = {'FACE'}
            bpy.ops.mesh.select_all(action='DESELECT')
        return {'FINISHED'}

class MESH_TO_apply_adjust(bpy.types.Operator):
    """" Apply Adjustment In Edit Mode"""
    bl_idname = "mesh.apply_adjust"
    bl_label = "Apply Adjust"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
            mian_obj = bpy.data.objects[mytool.up_teeth_object_name]
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
            mian_obj = bpy.data.objects[mytool.down_teeth_object_name]


        if context.mode == 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = mian_obj

            bpy.ops.scene.saveblend(filename="cuttooth")
        return {'FINISHED'}

class MESH_TO_finde_intersect(bpy.types.Operator):
    """" Find Intersection In Seam between two teeth"""
    bl_idname = "mesh.find_interscetion"
    bl_label = "Find Intersection"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        up_down = mytool.up_down


        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
            main_object = bpy.data.objects[mytool.up_teeth_object_name]
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
            main_object = bpy.data.objects[mytool.down_teeth_object_name]

        polygons = main_object.data.polygons
        vertices = main_object.data.vertices
        
        # Find Intersction
        for obj in context.collection.objects:
            # apply the modifiers
            context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.convert(target='MESH')
        bpy.ops.object.select_all(action='DESELECT')
        total_info = []
        for obj in context.collection.objects:
            context.view_layer.objects.active = main_object
            main_object.select_set(True)
            context.scene.cursor.location = obj.location
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            
            edge_keys = obj.data.edge_keys
            curve_vertices = obj.data.vertices
            through_triangle_info = []
            pair_triangle_info = []

            # calculate the through mesh region by ray_cast
            for edge_key in edge_keys:
                # First Direction
                dir = curve_vertices[edge_key[1]].co - curve_vertices[edge_key[0]].co
                dist = distance(curve_vertices[edge_key[1]].co, curve_vertices[edge_key[0]].co)
                direction = dir.normalized()
                origin = curve_vertices[edge_key[0]].co
                result1 = main_object.ray_cast(origin,direction,distance=dist)
                
                # Second Direction
                dir = curve_vertices[edge_key[0]].co - curve_vertices[edge_key[1]].co
                dist = distance(curve_vertices[edge_key[1]].co, curve_vertices[edge_key[0]].co)
                direction = dir.normalized()
                origin = curve_vertices[edge_key[1]].co
                result2 = main_object.ray_cast(origin,direction,distance=dist)
                
                
                if result1[0] == True and result2[0] == True:
                    if result1[3] != result2[3]:                # find pairs triangle in one thread,which through different triangles
                        pair_triangle_info.append(((result1[1],result1[3]),(result2[1],result2[3])))
                        center_pt = (result1[1] + result2[1]) / 2
                        dir = curve_vertices[edge_key[0]].co - center_pt
                        dist = distance(curve_vertices[edge_key[0]].co, center_pt)
                        direction1 = dir.normalized()
                        result1_1 = main_object.ray_cast(center_pt,direction1,distance=dist)
                        print(result1_1)
                        
                        dir = curve_vertices[edge_key[1]].co - center_pt
                        dist = distance(curve_vertices[edge_key[1]].co, center_pt)
                        direction2 = dir.normalized()
                        result2_1 = main_object.ray_cast(center_pt,direction2,distance=dist)
                        print(result2_1)

                        if result1_1[3] == result1[3]:
                            through_triangle_info.append((result1[1],result1[3]))   
                            pair_triangle_info.append(((result1_1[1],result1_1[3]),(result2_1[1],result2_1[3])))
                        else:
                            pair_triangle_info.append(((result1[1],result1[3]),(result1_1[1],result1_1[3])))
                        
                        if result2_1[3] == result2[3]:  
                            through_triangle_info.append((result2[1],result2[3]))
                            pair_triangle_info.append(((result1_1[1],result1_1[3]),(result2_1[1],result2_1[3])))
                        else:
                            pair_triangle_info.append(((result2[1],result2[3]),(result2_1[1],result2_1[3])))

                    else:                                       # find single triangle in one thread,which through the same triangle
                        through_triangle_info.append((result1[1],result1[3]))
            print("======================================================================================")
            print(obj.name, "Pair Triangle:", pair_triangle_info)
            print("Through Triangle Index:", through_triangle_info)
            
            if len(through_triangle_info) % 2 == 0:
                sorted_list = pair_traingles(through_triangle_info)
            else:   
                error_message = obj.name + ' has a special situation! Can not find intersection! Please check!'
                print(error_message)
                break

            exist_triangle_info = []
            rest_triangle_info = []
            for index, elem in enumerate(sorted_list):
                if index == 0:
                    pair_triangle_info.append(elem[1])
                    exist_triangle_info.append(elem[1][0])
                    exist_triangle_info.append(elem[1][1])
                else:
                    if elem[1][0] in exist_triangle_info and elem[1][1] not in exist_triangle_info:
                        rest_triangle_info.append(elem[1][1])
                    elif elem[1][1] in exist_triangle_info and elem[1][0] not in exist_triangle_info:
                        rest_triangle_info.append(elem[1][0])
                    elif elem[1][0] not in exist_triangle_info and elem[1][1] not in exist_triangle_info:
                        pair_triangle_info.append(elem[1])
                        exist_triangle_info.append(elem[1][0])
                        exist_triangle_info.append(elem[1][1])
                    else:
                        pass

            # handle rest triangle info              
            if len(rest_triangle_info) == 1:
                pass
            
            if len(rest_triangle_info) == 2:
                pair_triangle_info.append((rest_triangle_info[0],rest_triangle_info[1]))

            if len(rest_triangle_info) == 4:
                sort_list_ = pair_traingles(rest_triangle_info)
                for index, elem in enumerate(sorted_list):
                    if index == 0:
                        pair_triangle_info.append(elem[1])
                        exist_triangle_info.append(elem[1][0])
                        exist_triangle_info.append(elem[1][1])
                    else:
                        if elem[1][0] in exist_triangle_info and elem[1][1] not in exist_triangle_info:
                            rest_triangle_info.append(elem[1][1])
                        elif elem[1][1] in exist_triangle_info and elem[1][0] not in exist_triangle_info:
                            rest_triangle_info.append(elem[1][0])
                        elif elem[1][0] not in exist_triangle_info and elem[1][1] not in exist_triangle_info:
                            pair_triangle_info.append(elem[1])
                            exist_triangle_info.append(elem[1][0])
                            exist_triangle_info.append(elem[1][1])
                        else:
                            pass
            total_info.append((obj.pass_index, pair_triangle_info))
            print(len(pair_triangle_info), "Pair Triangle Info:", pair_triangle_info)
            print("Exist Triangle Info", exist_triangle_info)
            print("Rest Triangle Info", rest_triangle_info)
            print("======================================================================================")
        # print("Total Info", total_info)
        

        for item in total_info:
            obj_pass_index = item[0]
            pair_tri_info = item[1]
            context.scene.cursor.location = context.collection.objects[str(obj_pass_index)].location
            context.view_layer.objects.active = main_object
            main_object.select_set(True)
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            times = 0
            for pair_info in pair_tri_info:
                times = times + 1
                first_tri_index = pair_info[0][1]
                second_tri_index = pair_info[1][1]
                polygons[first_tri_index].select = True
                polygons[second_tri_index].select = True
                bpy.ops.object.mode_set(mode='EDIT')

                vertex_name = str(obj_pass_index) + '_' + str(times) + '_Tri'
                bpy.ops.object.vertex_group_add()                   
                main_object.vertex_groups['Group'].name = vertex_name
                bpy.ops.object.vertex_group_assign()
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')

                repeat_tri_index_cnt = 0
                for vertex_index1 in polygons[first_tri_index].vertices:
                    for vertex_index2 in polygons[second_tri_index].vertices:
                         if vertex_index1 == vertex_index2:
                            repeat_tri_index_cnt = repeat_tri_index_cnt + 1
                
                if repeat_tri_index_cnt == 0:
                    vertices[polygons[first_tri_index].vertices[0]].select = True
                    vertices[polygons[second_tri_index].vertices[0]].select = True
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
                    bpy.ops.mesh.shortest_path_select(edge_mode='SELECT')
                    bpy.ops.object.vertex_group_add()                   
                    main_object.vertex_groups['Group'].name = str(obj_pass_index) + '_' + str(times) + '_path'
                    bpy.ops.object.vertex_group_assign()
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.select_all(action='DESELECT')
        context.scene.cursor.location = mathutils.Vector((0.0, 0.0, 0.0))
        context.view_layer.objects.active = main_object
        main_object.select_set(True)
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

        bpy.ops.ed.undo_push()
        
        return {'FINISHED'}

class MESH_TO_knife_panel(bpy.types.Operator):
    """" Generate A Knife Panel for intersect """
    """ Attention: You can keep curve is above surface !!!"""
    bl_idname = "mesh.knife_panel"
    bl_label = "Knife Panel"
    
    def execute(self, context):
        bpy.ops.scene.saveblend(filename="cuttooth")
        scene = context.scene
        mytool = scene.my_tool
        
        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
            main_object = bpy.data.objects[mytool.up_teeth_object_name]
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
            main_object = bpy.data.objects[mytool.down_teeth_object_name]
        
        sysGaveName = main_object.name + '.001'

        # Get material
        mat = bpy.data.materials.get("Knife Panel Color")
        if mat is None:
            # create material
            mat = bpy.data.materials.new(name="Knife Panel Color")
            mat.diffuse_color =  (0.0801147, 0.747253, 0.8, 1)
            mat.metallic = 0.254
            mat.roughness = 0.211

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')              # enter 'OBJECT' mode
            bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_all(action='DESELECT')
        
        # apply modifiers and copy curves out
        num = len(context.collection.objects)
        index_list = list(range(num))
        for index in index_list:
            obj = context.collection.objects[index]
            context.view_layer.objects.active = obj
            obj.select_set(True)
            # duplicate objects
            bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')
            bpy.ops.object.select_all(action='DESELECT')
        # add modifiers and offset curves under Teeth
        num = len(context.collection.objects)
        index_list = list(range(int(num/2), num))
        for index in index_list:
            obj = context.collection.objects[index]
            # select duplicated object and add modifiers
            context.view_layer.objects.active = obj
            obj.select_set(True)
            
            # add modifies
            bpy.ops.object.modifier_add(type='SHRINKWRAP')
            bpy.context.object.modifiers["Shrinkwrap"].target = main_object
            bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'ABOVE_SURFACE'
            bpy.context.object.modifiers["Shrinkwrap"].offset = -0.92

            bpy.ops.object.modifier_add(type='SMOOTH')
            bpy.context.object.modifiers["Smooth"].factor = 1.0
            bpy.context.object.modifiers["Smooth"].iterations = 100

            bpy.ops.object.mode_set(mode='OBJECT')      # enter 'OBJECT' mode
            bpy.ops.object.convert(target='MESH')

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.context.scene.tool_settings.use_snap = False
            bpy.ops.mesh.remove_doubles(threshold=0.3, use_unselected=False)
            bpy.ops.mesh.edge_face_add()
            if mytool.up_down == 'UP_':
                bpy.ops.transform.resize(value=(0.86, 0.86, 0.86), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
                
                bpy.ops.transform.translate(value=(0, 0, 2.63), orient_type='NORMAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='NORMAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
            else:
                bpy.ops.transform.resize(value=(0.86, 0.86, 0.86), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
                
                bpy.ops.transform.translate(value=(0, 0, -2.63), orient_type='NORMAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='NORMAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')

        index_list = list(range(int(num/2)))
        # join two objects bridge edge loop
        for index in index_list:
            bpy.ops.object.select_all(action='DESELECT')
            obj = context.collection.objects[index]
            context.view_layer.objects.active = obj
            obj.select_set(True)
            temp_name = str(obj.pass_index)+'.001'
            context.collection.objects[temp_name].select_set(True)
            bpy.ops.object.join()
            bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='EDIT')        # enter 'EDIT' mode
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.bridge_edge_loops(type='PAIRS')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

            mat = context.object.data.materials.get("Knife Panel Color")
            if mat is None:
                m = bpy.data.materials['Knife Panel Color']
                context.object.data.materials.append(m)
            else:
                pass
        bpy.ops.ed.undo_push()

        return {'FINISHED'}

class MESH_TO_cut_teeth(bpy.types.Operator):
    """ Cut Out Teeth By Knife Panel"""
    bl_idname = "mesh.cut_teeth"
    bl_label = "Cut Teeth"

    def execute(self, context):
        bpy.ops.scene.saveblend(filename="cuttooth")
        scene = context.scene
        mytool = scene.my_tool

        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
            main_object = bpy.data.objects[mytool.up_teeth_object_name]
            curves_collection = bpy.data.collections['Curves_U']
            main_object_copy_name = main_object.name + '.001'
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
            main_object = bpy.data.objects[mytool.down_teeth_object_name]
            curves_collection = bpy.data.collections['Curves_D']
            main_object_copy_name = main_object.name + '.001'
        
        vertex_groups = main_object.vertex_groups
        sysGaveName2 = main_object.name + '.002'
        sysGaveName3 = main_object.name + '.003'

        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')              # enter 'OBJECT' mode
            bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_all(action='DESELECT')

        # hide knife panel
        for obj in bpy.context.collection.objects:
            obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        for obj in bpy.context.collection.objects:
                obj.hide_set(True)


        # join knife panel into main object tooth
        for obj in context.collection.objects:
            pass_index = obj.pass_index
            temp_name = obj.name + '_'
            origin_name = 'Origin_' + str(pass_index)
            print('=================================')
            print('Object Pass Index:', pass_index)
            print('Object Name:', temp_name)
            obj.hide_set(False) 

            context.view_layer.objects.active = main_object
            main_object.select_set(True)
            bpy.ops.object.duplicate()
            main_object.select_set(False)

            main_object_copy = bpy.data.objects[main_object_copy_name]
            context.view_layer.objects.active = main_object_copy

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            obj.select_set(True)
            bpy.ops.object.join()
            bpy.ops.object.mode_set(mode='EDIT')

            seam_name = 'seam_' + temp_name
            bpy.ops.object.vertex_group_add()
            main_object_copy.vertex_groups['Group'].name = seam_name
            bpy.ops.object.vertex_group_assign()
            bpy.ops.mesh.intersect(mode='SELECT_UNSELECT', separate_mode='CUT', threshold=0.0)
            bpy.ops.object.vertex_group_assign()
            bpy.ops.object.vertex_group_select()

            bpy.ops.mesh.separate(type='SELECTED')

            bpy.data.objects[sysGaveName2].select_set(False)

            path = []
            for vertex_group in vertex_groups:
                if vertex_group.name.startswith(temp_name): 
                    main_object_copy.vertex_groups.active = main_object_copy.vertex_groups[vertex_group.name]
                    bpy.ops.object.vertex_group_select()
                    bpy.ops.object.vertex_group_remove()                

            main_object_copy.vertex_groups.active = main_object_copy.vertex_groups[seam_name]
            bpy.ops.object.vertex_group_select()

            bpy.ops.mesh.hide(unselected=False)
            main_object_copy.vertex_groups.active = main_object_copy.vertex_groups[origin_name]
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_remove()

            bpy.ops.mesh.select_linked(delimit=set())

            bpy.ops.mesh.reveal()
            if bpy.context.active_object.data.total_vert_sel > 8000 or bpy.context.active_object.data.total_vert_sel < 1000:
                error_message = temp_name + ' has error situation please check!'
                print(error_message)
                self.report({'ERROR'}, error_message)
                break
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.data.objects[sysGaveName3].select_set(False)

            if mytool.up_down == 'UP_':
                bpy.data.objects[sysGaveName3].data.name = 'Tooth_U_' + temp_name
                bpy.data.objects[sysGaveName3].name = 'Tooth_U_' + temp_name
            else:
                bpy.data.objects[sysGaveName3].data.name = 'Tooth_D_' + temp_name
                bpy.data.objects[sysGaveName3].name = 'Tooth_D_' + temp_name
            
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')

            main_object_copy.select_set(True)
            bpy.data.objects[sysGaveName2].select_set(True)
            bpy.ops.object.delete(use_global=True, confirm=False)
            message = 'Cut ' + temp_name + ' Tooth Finished!'
            print(message)

        print('Cut All Teeth Finish!!')  
        self.report({'INFO'}, 'OK! Cut All Teeth Finish!')
        
        context.collection.objects.link(main_object)
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Collection'] 
        
        mat = bpy.data.materials.get("Whole Teeth Color")
        if mat is None:
            # create material
            mat = bpy.data.materials.new(name="Whole Teeth Color")
            mat.diffuse_color = (0.8, 0.8, 0.8, 0.4)
        main_object.data.materials.append(mat)
        context.collection.objects.unlink(main_object)

        for tooth in context.collection.objects:
            if tooth.name.startswith('Tooth'):
                context.view_layer.objects.active = tooth
                bpy.ops.object.vertex_group_remove(all=True, all_unlocked=False)
                context.collection.objects.unlink(tooth)
                curves_collection.objects.link(tooth)
        context.view_layer.objects.active = main_object
        bpy.ops.object.vertex_group_remove(all=True, all_unlocked=False)
        context.object.hide_set(True)
        
        bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_draw_annotate(bpy.types.Operator):
    bl_idname = "mesh.draw_annotate"
    bl_label = "Draw Annotate"
    bl_description = "Draw An Annotation"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']

        if len(context.selected_objects) == 1 and context.selected_objects[0].name.startswith('Tooth'):
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
            bpy.ops.wm.tool_set_by_id(name="builtin.annotate_line")
            context.scene.tool_settings.annotation_stroke_placement_view3d = 'SURFACE'
            context.space_data.show_gizmo_object_translate = False
            mytool.selected_object_name = context.object.name
        bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_generate_coordinate(bpy.types.Operator):
    bl_idname = "mesh.generate_coordinate"
    bl_label = "Generate Coordinate"
    bl_description = "Generate a Coordinate of selected tooth"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        selected_object_name = mytool.selected_object_name

        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']

        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set('INVOKE_REGION_WIN', mode='OBJECT')

        # Convert annotation to curve
        curve = conver_gpencil_to_curve(self, context, None, selected_object_name)

        if curve != None:
            # Delete annotation strokes
            try:
                bpy.context.annotation_data.layers.active.clear()
            except:
                pass

            # Clean up curves
            bpy.ops.object.select_all(action='DESELECT')
            curve.select_set(True)
            bpy.context.view_layer.objects.active = curve

            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
            bpy.ops.object.convert(target='MESH')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles(threshold=0.18, use_unselected=False)
            bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='linear', lock_x=False, lock_y=False, lock_z=False)
            bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='25', regular=True)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
            bpy.ops.object.duplicate()

            tooth_object = context.collection.objects[selected_object_name]
            loca = tooth_object.location
            curve_copy_name =  curve.name + '.001'
            curve_copy = context.collection.objects[curve_copy_name]
            curve_copy.location = loca
            context.view_layer.objects.active = curve
            curve.select_set(True)
            bpy.ops.object.join()
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.bridge_edge_loops(type='PAIRS')
            bpy.context.scene.transform_orientation_slots[0].type = 'NORMAL'
            bpy.context.scene.transform_orientation_slots[1].type = 'NORMAL'
            bpy.context.space_data.show_gizmo_object_translate = True

            bpy.context.scene.tool_settings.use_snap = False
            bpy.ops.transform.create_orientation(name="normal", use=True)
            normal_orientation_matirx = bpy.context.scene.transform_orientation_slots[0].custom_orientation.matrix.copy()
            bpy.ops.transform.delete_orientation()
            bpy.context.scene.transform_orientation_slots[0].type = 'LOCAL'
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.delete(use_global=False, confirm=False)
            normal_orientation_matirx.normalize()
            print(normal_orientation_matirx)
            M = normal_orientation_matirx.to_4x4()

            bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.mesh.primitive_vert_add()       # add a vertex in origin(3D Cursor)
            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(8, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(True, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.editmode_toggle()
            bpy.context.object.data.vertices[0].select = True
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(-8, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(True, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.editmode_toggle()
            bpy.context.object.data.vertices[0].select = True
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 8, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(True, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.editmode_toggle()
            bpy.context.object.data.vertices[0].select = True
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, -8, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(True, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.editmode_toggle()
            bpy.context.object.data.vertices[0].select = True
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, 8), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(True, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.editmode_toggle()
            bpy.context.object.data.vertices[0].select = True
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, -8), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(True, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.editmode_toggle()

            bpy.ops.object.modifier_add(type='SKIN')
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Skin")

            bpy.ops.ed.undo_push()

            context.object.data.name = '_' + tooth_object.name + '_coordinate'
            context.object.name = '_' + tooth_object.name + '_coordinate'

            M.row[0][3] = tooth_object.matrix_local.row[0][3]
            M.row[1][3] = tooth_object.matrix_local.row[1][3]
            M.row[2][3] = tooth_object.matrix_local.row[2][3]
            context.object.matrix_local = M
            bpy.context.scene.transform_orientation_slots[1].type = 'LOCAL'
            bpy.context.space_data.show_gizmo_object_rotate = True
            bpy.context.space_data.show_gizmo_object_translate = True
        bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_filp_z_orientation(bpy.types.Operator):
    bl_idname = "mesh.filp_z_orientation"
    bl_label = "Filp Z Orientation"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']

        if len(context.selected_objects) == 1 and context.selected_objects[0].name.startswith('Tooth') and not context.selected_objects[0].name.endswith('_coord'):
        
            bpy.context.scene.transform_orientation_slots[0].type = 'LOCAL'
            bpy.context.scene.transform_orientation_slots[1].type = 'LOCAL'
            bpy.context.space_data.show_gizmo_object_rotate = False
            bpy.context.space_data.show_gizmo_object_translate = True
            bpy.context.scene.tool_settings.use_transform_data_origin = True
            
            bpy.ops.transform.create_orientation(name="local_", use=True)
            local_orientation_matirx = bpy.context.scene.transform_orientation_slots[0].custom_orientation.matrix.copy()
            local_orientation_matirx.transpose()
            # print(normal_orientation_matirx)
            a = (local_orientation_matirx.row[0][0], local_orientation_matirx.row[0][1], local_orientation_matirx.row[0][2])
            b = (local_orientation_matirx.row[1][0], local_orientation_matirx.row[1][1], local_orientation_matirx.row[1][2])
            c = (local_orientation_matirx.row[2][0], local_orientation_matirx.row[2][1], local_orientation_matirx.row[2][2])
            bpy.ops.transform.delete_orientation()
            bpy.context.scene.transform_orientation_slots[0].type = 'LOCAL'
            bpy.ops.transform.rotate(value=3.14159, orient_axis='Y', orient_type='LOCAL', orient_matrix=(a, b, c), orient_matrix_type='LOCAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
            bpy.context.scene.tool_settings.use_transform_data_origin = False

        bpy.ops.ed.undo_push()    
        return {'FINISHED'}

class MESH_TO_change_local_orientation(bpy.types.Operator):
    """Change local frame orientation"""
    bl_idname = "mesh.change_local_orientation"
    bl_label = "Change Local Orientation"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']

        if len(context.selected_objects) == 1 and context.selected_objects[0].name.startswith('Tooth') and not context.selected_objects[0].name.endswith('_coord'):
            matirx_local = context.object.matrix_local.copy()
            coord_name = context.object.name + '_coord'
            coord_object = context.collection.objects[coord_name]
            coord_object.hide_set(False)
            coord_object.matrix_local = matirx_local
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = coord_object
            coord_object.select_set(True)

            bpy.context.scene.transform_orientation_slots[1].type = 'LOCAL'
            bpy.context.space_data.show_gizmo_object_translate = True
            bpy.context.space_data.show_gizmo_object_rotate = True

            bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_apply_orientation(bpy.types.Operator):
    """Apply the changed local Frame Orientation"""
    bl_idname = "mesh.apply_orientation"
    bl_label = "Apply Orientation"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']

        if len(context.selected_objects) and context.object.name.endswith('_coord'):
            tooth_name = context.object.name.rstrip('_coord')
            tooth_name = tooth_name.lstrip('_')
            tooth_object = context.collection.objects[tooth_name]
            coord_object = context.object
            context.view_layer.objects.active = tooth_object
            tooth_object.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = coord_object
            coord_object.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            tooth_object.select_set(True)
            bpy.ops.object.join()
            bpy.ops.object.material_slot_remove()
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.mode_set(mode = 'OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            coord_name = context.object.name
            context.object.hide_set(True)
            # context.objects.data.material.
            sysGaveName = coord_name + '.001'
            newName = coord_name.rstrip('_coord')

            mat = bpy.data.materials.get("Teeth Color")
            if mat is None:
                # create material
                mat = bpy.data.materials.new(name="Teeth Color")
                mat.diffuse_color = (0.656, 0.577, 0.906, 1)
                mat.metallic = 0
                mat.roughness = 0.4
            context.collection.objects[sysGaveName].data.materials.append(mat)

            tooth_obj = context.collection.objects[sysGaveName]
            tooth_obj.data.name = newName
            tooth_obj.name = newName
            context.view_layer.objects.active = tooth_obj
            tooth_obj.select_set(True)
            bpy.context.space_data.show_gizmo_object_rotate = False

            bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_automatic_orientation(bpy.types.Operator):
    """Auto Orientate Teeth Axis"""
    bl_idname = "mesh.auto_orientation"
    bl_label = "Auto Orientation"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        bpy.context.scene.cursor.location = mathutils.Vector((0.0, 0.0, 0.0))
        bpy.context.scene.cursor.rotation_euler = mathutils.Vector((0.0, 0.0, 0.0))
        context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Collection']
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.mesh.primitive_vert_add()
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)       
        bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(8, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(True, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.editmode_toggle()
        bpy.context.object.data.vertices[0].select = True
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(-8, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(True, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.editmode_toggle()
        bpy.context.object.data.vertices[0].select = True
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 8, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(True, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.editmode_toggle()
        bpy.context.object.data.vertices[0].select = True
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, -8, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(True, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.editmode_toggle()
        bpy.context.object.data.vertices[0].select = True
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, 8), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(True, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.editmode_toggle()
        bpy.context.object.data.vertices[0].select = True
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, -8), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(True, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.editmode_toggle()
    
        bpy.ops.object.modifier_add(type='SKIN')
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Skin")
        coordinate_obj = context.object
        coordinate_obj.data.name = 'Vert'
        coordinate_obj.name = 'Vert'
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        
        if mytool.up_down == 'UP_':
            collection_name = 'Curves_U'
        else:
            collection_name = 'Curves_D'
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]
        
        for obj in context.collection.objects:
            if obj.name.startswith('Tooth') and not obj.name.endswith('_coord'):
                context.view_layer.objects.active = obj
                obj.select_set(True)    
                tooth_name = obj.name
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.context.tool_settings.mesh_select_mode = (True, False, False)
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.region_to_loop()
                bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='25', regular=True)
                bpy.ops.mesh.edge_face_add()
                bpy.ops.mesh.poke(offset=1, use_relative_offset=True, center_mode='BOUNDS')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
                location = obj.location
                last_vertice = obj.data.vertices[len(obj.data.vertices)-1]
                last_vertice.select = True
                last_vrt_co = last_vertice.co.copy()
                last_vrt_co_world = obj.matrix_world @ last_vrt_co
                z_direction = last_vrt_co_world - location 
                z_direction.normalize()
                print('z_direction', obj.name, z_direction)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.context.scene.transform_orientation_slots[0].type = 'NORMAL'
                bpy.ops.transform.create_orientation(name="normal", use=True)
                normal_orientation_matirx = bpy.context.scene.transform_orientation_slots[0].custom_orientation.matrix.copy()
                bpy.ops.transform.delete_orientation()
                bpy.context.scene.transform_orientation_slots[0].type = 'LOCAL'
                normal_orientation_matirx.normalize()
                print('normal_orientation_matirx', normal_orientation_matirx)
                normal_orientation_matirx.row[0][2] = z_direction[0]    
                normal_orientation_matirx.row[1][2] = z_direction[1]    
                normal_orientation_matirx.row[2][2] = z_direction[2]
                normal_orientation_matirx.normalize()
                print('apply_z_direction',normal_orientation_matirx)
                vrt_normal_matrix = normal_orientation_matirx.to_4x4()
                print('4x4', vrt_normal_matrix)
                bpy.ops.mesh.delete(type='VERT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')

                mat_local = obj.matrix_local.copy()
                print('mat_local', mat_local)
                vrt_normal_matrix.row[0][3] = mat_local.row[0][3]
                vrt_normal_matrix.row[1][3] = mat_local.row[1][3]
                vrt_normal_matrix.row[2][3] = mat_local.row[2][3]
                vrt_normal_matrix.normalize()
                print('with_z_direction_matrix', vrt_normal_matrix)

                obj.select_set(False)
                bpy.data.collections['Collection'].objects.link(obj)
                context.collection.objects.unlink(obj)

                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Collection']
                context.view_layer.objects.active = context.collection.objects['Vert']
                context.collection.objects['Vert'].select_set(True)  
                bpy.ops.object.duplicate()
                coord_object = context.object
                coord_object.matrix_local = vrt_normal_matrix 
                coord_object.data.name = tooth_name + '_coord'
                coord_object.name = tooth_name + '_coord'
                obj.select_set(True)
                bpy.ops.object.join()
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.separate(type='SELECTED')
                coord_object = context.object
                sys_gave_name = context.object.name + '.001'
                tooth_objet = context.collection.objects[sys_gave_name]
                tooth_objet.data.name = tooth_name
                tooth_objet.name = tooth_name

                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = tooth_objet
                tooth_objet.select_set(True)

                M = tooth_objet.matrix_local.copy()
                x_co = M.row[0][2]
                y_co = M.row[1][2]
                z_co = M.row[2][2]
                z_axis_dir = mathutils.Vector((x_co, y_co, z_co))

                box = tooth_objet.bound_box
                max_z = box[0][2]
                for elem in box:
                    if elem[2] > max_z:
                        max_z = elem[2]
                        break
                print('max_z', max_z)
            
                for face in tooth_objet.data.polygons:
                    if abs(face.center[2] - max_z) < 1:
                        face.select = True

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.duplicate()
                bpy.ops.mesh.separate(type='SELECTED')
                bpy.ops.object.mode_set(mode='OBJECT')

                part_object_name = tooth_objet.name + '.001'
                part_object = context.collection.objects[part_object_name]
                part_object.data.name = 'part_' + tooth_objet.name
                part_object.name = 'part_' + tooth_objet.name
                bpy.ops.object.select_all(action='DESELECT')

                context.view_layer.objects.active = part_object
                part_object.select_set(True)

                total_vrt = len(part_object.data.vertices)
                part_object.data.polygons[0].select = True
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_linked(delimit={'SEAM'})
                if context.object.data.total_vert_sel != total_vrt:
                    bpy.ops.mesh.separate(type='SELECTED')
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                    if len(context.selected_objects) == 2:
                        loca1 = context.selected_objects[0].location
                        loca2 = context.selected_objects[1].location
                        temp_dir  = loca1 - loca2
                        temp_dir.normalize()
                        if temp_dir[1] < 0:
                            temp_dir = loca2 - loca1
                            temp_dir.normalize()
                        print('temp_dir', temp_dir)
                        print('z_axis_dir', z_axis_dir)

                        x_dir = temp_dir.cross(z_axis_dir)
                        x_dir.normalize()
                        print('cross_dir', x_dir)
                        z_dir = x_dir.cross(z_axis_dir)
                        z_dir.normalize()
                        print('cross_dir', z_dir)
                        M_orient = mathutils.Matrix([x_dir, z_axis_dir, z_dir])
                        M_orient.transpose()
                        M_orient.normalize()
                        M_orient = M_orient.to_4x4()

                        N = tooth_objet.matrix_local.copy()
                        M_orient.row[0][3] = N.row[0][3]
                        M_orient.row[1][3] = N.row[1][3]
                        M_orient.row[2][3] = N.row[2][3]
                        print('orient', M_orient)
                        coord_object.matrix_local = M_orient
                    bpy.ops.object.select_all(action='DESELECT')
                else:
                    print('just has one part or connected vertices exist')
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                    local = part_object.location
                    print('part object location', local)
                    tooth_location = tooth_objet.location
                    print('tooth location', tooth_location)
                    word_m = tooth_objet.matrix_world.copy()
                    print('word matrix', word_m)
                    in_word_m = word_m.inverted()
                    print('world invert matrix', in_word_m)
                    local_co = (in_word_m @ local)
                    print('local location', local_co)
                    a_v = mathutils.Vector((0, 0, local_co[2]))
                    z_vector = local_co - a_v
                    world_z_vector = word_m @ z_vector - tooth_location
                    print('world z vector', world_z_vector)
                    world_z_vector.normalize()
                    x_dir = world_z_vector.cross(z_axis_dir)
                    x_dir.normalize()
                    z_dir = x_dir.cross(z_axis_dir)

                    M_orient = mathutils.Matrix([x_dir, z_axis_dir, z_dir])
                    M_orient.transpose()
                    M_orient.normalize()
                    M_orient = M_orient.to_4x4()

                    N = tooth_objet.matrix_local.copy()
                    M_orient.row[0][3] = N.row[0][3]
                    M_orient.row[1][3] = N.row[1][3]
                    M_orient.row[2][3] = N.row[2][3]
                    coord_object.matrix_local = M_orient

                bpy.ops.object.mode_set(mode='OBJECT')

                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = coord_object
                coord_object.select_set(True)  
                if coord_object.matrix_local.row[1][2] < 0:
                    matrix_local = coord_object.matrix_local.copy()
                    M = matrix_local.to_3x3()
                    M.transpose()
                    a = (M.row[0][0], M.row[0][1], M.row[0][2])
                    b = (M.row[1][0], M.row[1][1], M.row[1][2])
                    c = (M.row[2][0], M.row[2][1], M.row[2][2])
                    bpy.ops.transform.rotate(value=3.14159, orient_axis='Y', orient_type='LOCAL', orient_matrix=(a, b, c), orient_matrix_type='LOCAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]

        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Collection']
        bpy.ops.object.select_all(action='DESELECT')
        
        for obj in context.collection.objects:
            if obj.name.startswith('Vert') or obj.name.startswith('part_'):
                context.view_layer.objects.active = obj
                obj.select_set(True) 
                bpy.ops.object.delete(use_global=True, confirm=False)
                bpy.ops.object.select_all(action='DESELECT')

        context.scene.transform_orientation_slots[1].type = 'LOCAL'
        context.space_data.show_gizmo_object_translate = True
        bpy.context.space_data.show_gizmo_object_rotate = True
        bpy.context.scene.tool_settings.use_snap = False

        bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_apply_auto_orientation(bpy.types.Operator):
    """Apply Auto Orientation"""
    bl_idname = "mesh.apply_auto_orientation"
    bl_label = "Apply Auto Orientation"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        
        if mytool.up_down == 'UP_':
            collection_name = 'Curves_U'
        else:
            collection_name = 'Curves_D'

        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Collection']

        for obj in context.collection.objects:
            if obj.name.startswith('Tooth') and not obj.name.endswith('_coord'):
                context.view_layer.objects.active = obj
                obj.select_set(True)
                tooth_name = context.object.name
                tooth_object = context.object
                coord_name = tooth_name + '_coord'
                coord_object = context.collection.objects[coord_name]
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')    
                context.view_layer.objects.active = coord_object
                coord_object.select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                tooth_object.select_set(True)
                bpy.ops.object.join()
                bpy.data.collections[collection_name].objects.link(coord_object)
                context.collection.objects.unlink(coord_object)
                context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.separate(type='SELECTED')
                bpy.ops.object.mode_set(mode='OBJECT')
                for obj in context.selected_objects:
                    if obj.name.endswith('.001'):
                        obj.data.name = tooth_name
                        obj.name = tooth_name
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Collection']
        
        context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]
        bpy.ops.object.select_all(action='DESELECT')
        
        for obj in context.collection.objects:
            if obj.name.endswith('_coord'):
                obj.hide_set(True)
        
        for material in bpy.data.materials:
            if not material.name.startswith('Whole'):
                bpy.data.materials.remove(material, do_unlink=True, do_id_user=True, do_ui_user=True)
        
        context.scene.transform_orientation_slots[1].type = 'LOCAL'
        bpy.context.space_data.show_gizmo_object_rotate = False
        bpy.context.scene.tool_settings.use_snap = False
        bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_apply_picked_orientation(bpy.types.Operator):
    """Apply Picked Orientation"""
    bl_idname = "mesh.apply_picked_orientation"
    bl_label = "Apply Picked Orientation"

    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            if context.object.data.total_face_sel == 1:
                bpy.context.scene.transform_orientation_slots[0].type = 'NORMAL'
                bpy.ops.transform.create_orientation(name="normal", use=True)
                normal_orientation_matirx = bpy.context.scene.transform_orientation_slots[0].custom_orientation.matrix.copy()
                bpy.ops.transform.delete_orientation()
                bpy.context.scene.transform_orientation_slots[0].type = 'LOCAL'
                normal_orientation_matirx.normalize()


                bpy.ops.object.mode_set(mode='OBJECT')
                tooth_obj = context.object
                coord_name = tooth_obj.name.strip('.001')
                print(coord_name)
                coord_obj = context.collection.objects[coord_name]
                M_local = coord_obj.matrix_local.copy()
                M_local.row[0][1] = normal_orientation_matirx.row[0][2]
                M_local.row[1][1] = normal_orientation_matirx.row[1][2]
                M_local.row[2][1] = normal_orientation_matirx.row[2][2]
                coord_obj.matrix_local = M_local
                print(M_local)
                print(normal_orientation_matirx)
                # for face in tooth_obj.data.polygons:
                #     if face.select == True:
                #         face_normal = face.normal.copy()
                #         face_normal.normalize()
                #         print(M_local)
                #         print(face_normal)

            else:
                print('Selcted Face Quantity is not 1!')


        return {'FINISHED'}

class MESH_TO_find_emboss_curves(bpy.types.Operator):
    """"Find Emboss Curves"""
    bl_idname = "mesh.find_emboss_curves"
    bl_label = "Find Curves"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
        tooth_obj_name_list = []
        bpy.ops.object.select_all(action='DESELECT')
        for obj in context.collection.objects:
            if obj.name.startswith('Tooth') and not obj.name.endswith('_coord'):
                tooth_obj_name_list.append(obj.name)
                for face in obj.data.polygons:
                    if face.center[2] > 0.3:
                        face.select = True
        for obj in context.collection.objects:
            context.view_layer.objects.active = obj
            obj.select_set(True) 
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)
        bpy.ops.mesh.duplicate(mode=1)
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        number_list = [11, 12, 13, 21, 22, 23, 31, 32, 33, 41, 42, 43]
        for tooth_name in tooth_obj_name_list:
            inside_obj_name = tooth_name + '.001'
            main_obj = context.collection.objects[inside_obj_name]
            context.view_layer.objects.active = main_obj
            main_obj.select_set(True)
            number = int(tooth_name.split('_')[1])
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
 
            vertices = main_obj.data.vertices
            bound_box = main_obj.bound_box

            # use bound box center as object center
            half_length_x = abs(bound_box[0][0])
            half_length_y = abs(bound_box[0][1])

            middle_index_list = []
            y_co_list = dict()
            pos_y_co_list = dict()
            neg_y_co_list = dict()
            six_vertice = []
            if number in number_list:
                for vrt in vertices:
                    if abs(vrt.co[0]) < 0.2 :
                        y_co_list[vrt.index] = vrt.co[1]
                sorted_list = sorted(y_co_list.items(), key=lambda item:item[1], reverse=True)
                max_y = sorted_list[0][1]
                min_y = sorted_list[len(sorted_list)-1][1]

                up_y_co = 0.7 * min_y
                down_y_co = 0.4 * max_y

                up_index = []
                down_index = []
                for elem in sorted_list:
                    if abs(elem[1] - 0.8 * max_y) < 0.25:
                        down_index.append(elem[0])
                    if abs(elem[1] - 0.95 * min_y) < 0.25:
                        up_index.append(elem[0])

                if len(up_index) == 0:
                    up_index.append(sorted_list[len(sorted_list)-1][0])
                if len(down_index) == 0:
                    down_index.append(sorted_list[0][0])
                
                temp_z = -100
                max_z_index = 0
                for idx in up_index:
                    if vertices[idx].co[2] > temp_z:
                        temp_z = vertices[idx].co[2]
                        max_z_index = idx
                six_vertice.append(max_z_index)             # middle up vertex

                temp_z = -100
                max_z_index = 0
                for idx in down_index:
                    if vertices[idx].co[2] > temp_z:
                        temp_z = vertices[idx].co[2]
                        max_z_index = idx
                six_vertice.append(max_z_index)             # middle down vertex

                pos_dis = 100   
                pos_nes_index = 0
                neg_dis = 100
                neg_nes_index = 0
                d_pos_dis = 100
                d_pos_nes_index = 0
                d_neg_dis = 100
                d_neg_nes_index = 0
                for vrt in vertices:
                    if abs(vrt.co[1] - up_y_co) < 0.2:
                        p_dis = abs(vrt.co[0] - 2.8)
                        n_dis = abs(vrt.co[0] - (-2.8))
                        if p_dis < pos_dis:
                            pos_dis = p_dis
                            pos_nes_index = vrt.index       
                        if n_dis < neg_dis:
                            neg_dis = n_dis
                            neg_nes_index = vrt.index

                    if abs(vrt.co[1] - down_y_co) < 0.2:
                        p_dis = abs(vrt.co[0] - 2.1)
                        n_dis = abs(vrt.co[0] - (-2.1))
                        if p_dis < d_pos_dis:
                            d_pos_dis = p_dis
                            d_pos_nes_index = vrt.index
                        if n_dis < d_neg_dis:
                            d_neg_dis = n_dis
                            d_neg_nes_index = vrt.index

                six_vertice.append(pos_nes_index)               # left up vertex
                six_vertice.append(neg_nes_index)               # right up vertex
                six_vertice.append(d_pos_nes_index)             # left down vertex
                six_vertice.append(d_neg_nes_index)             # right down vertex
                    
                # exchange vertices sequence
                six_vertice[1], six_vertice[2] = six_vertice[2], six_vertice[1]
                six_vertice[4], six_vertice[2] = six_vertice[2], six_vertice[4]
                six_vertice[3], six_vertice[4] = six_vertice[4], six_vertice[3]
                six_vertice[4], six_vertice[5] = six_vertice[5], six_vertice[4]

            else:
                for vrt in vertices:
                    if abs(vrt.co[0]) < 0.2 :
                        if vrt.co[2] > 0:
                            y_co_list[vrt.index] = vrt.co[1]
                    if abs(vrt.co[0] - 0.65 * half_length_x) < 0.2 :
                            pos_y_co_list[vrt.index] = vrt.co[1]
                    if abs(vrt.co[0] - 0.65 * (-half_length_x)) < 0.2 :
                            neg_y_co_list[vrt.index] = vrt.co[1]
                
                sorted_list = sorted(y_co_list.items(), key=lambda item:item[1], reverse=True)
                max_y = sorted_list[0][1]
                min_y = sorted_list[len(sorted_list)-1][1]

                pos_sorted_list = sorted(pos_y_co_list.items(), key=lambda item:item[1], reverse=True)
                neg_sorted_list = sorted(neg_y_co_list.items(), key=lambda item:item[1], reverse=True)
            
                pos_max_y = pos_sorted_list[0][1]
                pos_min_y = pos_sorted_list[len(pos_sorted_list)-1][1]

                neg_max_y = neg_sorted_list[0][1]
                neg_min_y = neg_sorted_list[len(neg_sorted_list)-1][1]


                up_index = []
                down_index = []
                for elem in sorted_list:
                    if abs(elem[1] - 0.75 * max_y) < 0.2:
                        down_index.append(elem[0])
                    if abs(elem[1] - 0.7 * min_y) < 0.2:
                        up_index.append(elem[0])
                    
                if len(up_index) == 0:
                    up_index.append(sorted_list[len(sorted_list)-1][0])
                if len(down_index) == 0:
                    down_index.append(sorted_list[0][0])
            
                temp_z = -100
                max_z_index = 0
                for idx in up_index:
                    if vertices[idx].co[2] > temp_z:
                        temp_z = vertices[idx].co[2]
                        max_z_index = idx
                six_vertice.append(max_z_index)         # middle up vertex

                temp_z = -100
                max_z_index = 0
                for idx in down_index:
                    if vertices[idx].co[2] > temp_z:
                        temp_z = vertices[idx].co[2]
                        max_z_index = idx
                six_vertice.append(max_z_index)         # middle donw vertex
                
                # negitive x vertices
                neg_up_index = []
                neg_down_index = []
                for elem in neg_sorted_list:
                    if abs(elem[1] - 0.5 * neg_max_y) < 0.2:
                        neg_down_index.append(elem[0])
                    if abs(elem[1] - 0.8 * neg_min_y) < 0.2:
                        neg_up_index.append(elem[0])

                if len(neg_up_index) == 0:
                    neg_up_index.append(neg_sorted_list[len(pos_sorted_list)-1][0])
                if len(neg_down_index) == 0:
                    neg_down_index.append(neg_sorted_list[0][0])

                temp_z = -100
                max_z_index = 0
                for idx in neg_up_index:
                    if vertices[idx].co[2] > temp_z:
                        temp_z = vertices[idx].co[2]
                        max_z_index = idx
                six_vertice.append(max_z_index)

                temp_z = -100
                max_z_index = 0
                for idx in neg_down_index:
                    if vertices[idx].co[2] > temp_z:
                        temp_z = vertices[idx].co[2]
                        max_z_index = idx
                six_vertice.append(max_z_index)

                # pos_x_vertices
                pos_up_index = []
                pos_down_index = []
                for elem in pos_sorted_list:
                    if abs(elem[1] - 0.5 * pos_max_y) < 0.2:
                        pos_down_index.append(elem[0])
                    if abs(elem[1] - 0.8 * pos_min_y) < 0.2:
                        pos_up_index.append(elem[0])

                if len(pos_up_index) == 0:
                    pos_up_index.append(pos_sorted_list[len(pos_sorted_list)-1][0])
                if len(pos_down_index) == 0:
                    pos_down_index.append(pos_sorted_list[0][0])

                temp_z = -100
                max_z_index = 0
                for idx in pos_up_index:
                    if vertices[idx].co[2] > temp_z:
                        temp_z = vertices[idx].co[2]
                        max_z_index = idx
                six_vertice.append(max_z_index)

                temp_z = -100
                max_z_index = 0
                for idx in pos_down_index:
                    if vertices[idx].co[2] > temp_z:
                        temp_z = vertices[idx].co[2]
                        max_z_index = idx
                six_vertice.append(max_z_index)

                # exchange vertices sequence
                six_vertice[1], six_vertice[2] = six_vertice[2], six_vertice[1]
                six_vertice[2], six_vertice[3] = six_vertice[3], six_vertice[2]
                six_vertice[4], six_vertice[5] = six_vertice[5], six_vertice[4]

            bpy.ops.object.vertex_group_add()
            main_obj.vertex_groups['Group'].name = 'emboss_curve'

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

            for index in range(len(six_vertice)):                
                if index == 5:                
                    vertices[six_vertice[index]].select = True
                    vertices[six_vertice[0]].select = True
                else:
                    vertices[six_vertice[index]].select = True
                    vertices[six_vertice[index+1]].select = True
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.shortest_path_select(edge_mode='SELECT')
                bpy.ops.object.vertex_group_assign()
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
            
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            
            context.view_layer.objects.active = main_obj
            main_obj.select_set(True)
            bpy.ops.object.delete()
            
            emboss_curve_name = tooth_name + '.002' 
            emboss_curve_obj = context.collection.objects[emboss_curve_name]
            emboss_curve_obj.data.name = 'emboss_' + tooth_name
            emboss_curve_obj.name = 'emboss_' + tooth_name

            context.view_layer.objects.active = emboss_curve_obj
            emboss_curve_obj.select_set(True)
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)

            polygons = emboss_curve_obj.data.polygons
            for face in polygons:
                face.select = True
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.remove_doubles(threshold=1)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

            vertices = emboss_curve_obj.data.vertices
            a = []
            c = []
            for edge_key in emboss_curve_obj.data.edge_keys:
                a.append(edge_key[0])
                a.append(edge_key[1])
            a.sort()
            from collections import Counter
            count = dict(Counter(a))
            c.append([key for key, value in count.items() if value == 1])
            print()
            print('c:',c)

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)   
            bpy.ops.object.mode_set(mode='OBJECT')

            for index in c[0]:
                vertices[index].select = True
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.delete(type='VERT')
            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='1', regular=True)
            bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='cubic', lock_x=False, lock_y=False, lock_z=False)
            bpy.ops.mesh.remove_doubles(threshold=1.2)
            bpy.ops.mesh.vertices_smooth(factor=0.5)


            bpy.ops.object.modifier_add(type='SUBSURF')
            bpy.context.object.modifiers["Subdivision"].levels = 4
            bpy.context.object.modifiers["Subdivision"].show_on_cage = True

            bpy.ops.object.modifier_add(type='SHRINKWRAP')
            bpy.context.object.modifiers["Shrinkwrap"].target = context.collection.objects[tooth_name]
            bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'NEAREST_SURFACEPOINT'
            bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'ON_SURFACE'
            bpy.context.object.modifiers["Shrinkwrap"].offset = 0
            bpy.context.object.modifiers["Shrinkwrap"].show_on_cage = True

            bpy.ops.object.modifier_add(type='SMOOTH')
            bpy.context.object.modifiers["Smooth"].iterations = 15
            bpy.context.object.modifiers["Smooth"].show_in_editmode = True
            bpy.context.object.modifiers["Smooth"].show_on_cage = True
            bpy.context.object.modifiers["Smooth"].factor = 0.5

            bpy.ops.object.mode_set(mode='OBJECT')
            context.object.data.name = 'curve_' + tooth_name
            context.object.name = 'curve_' + tooth_name
            bpy.ops.object.select_all(action='DESELECT')

        for obj in context.collection.objects:
            if obj.name.startswith('curve_'):
                obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.space_data.show_gizmo_object_translate = False
        bpy.ops.ed.undo_push()

        return {'FINISHED'}

class MESH_TO_draw_region_curve(bpy.types.Operator):
    """" Draw Curves To Define Emboss Region"""
    bl_idname = "mesh.draw_curve"
    bl_label = "Draw Curve"
    
    def execute(self, context):
        if len(context.selected_objects) == 1 and context.selected_objects[0].name.startswith('Tooth') and not context.selected_objects[0].name.endswith('_coord'):
            scene = context.scene
            mytool = scene.my_tool

            if mytool.up_down == 'UP_':
                bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
            else:
                bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']

            tooth_object = bpy.context.object

            mytool.tooth_name = tooth_object.name
            bpy.context.scene.tool_settings.use_snap = True

            bpy.context.space_data.show_gizmo_object_translate = False
            bpy.context.space_data.overlay.show_floor = False
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)

            bpy.ops.mesh.primitive_vert_add()

            bpy.context.object.name = 'curve_' + tooth_object.name
            bpy.context.object.data.name = 'curve_' + tooth_object.name

            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(1, 0, 0), "orient_type":'VIEW',  "orient_matrix_type":'VIEW', "constraint_axis":(True, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})

            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.ops.ed.undo_push()

            bpy.ops.object.modifier_add(type='SUBSURF')
            bpy.context.object.modifiers["Subdivision"].levels = 2
            # add shrinkwrap modifier
            bpy.ops.object.modifier_add(type='SHRINKWRAP')
            bpy.context.object.modifiers["Shrinkwrap"].target = tooth_object
            bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'NEAREST_SURFACEPOINT'
            bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'ABOVE_SURFACE'
            bpy.context.object.modifiers["Shrinkwrap"].offset = 0.2
            # add smooth modifier 
            bpy.ops.object.modifier_add(type='SMOOTH')
            bpy.context.object.modifiers["Smooth"].iterations = 20 
            bpy.context.object.modifiers["Smooth"].show_in_editmode = True
            bpy.context.object.modifiers["Smooth"].show_on_cage = True
            bpy.context.object.modifiers["Smooth"].factor = 0.5
            
            bpy.context.object.modifiers["Shrinkwrap"].show_on_cage = True
            bpy.context.object.modifiers["Subdivision"].show_on_cage = True

            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.wm.tool_set_by_id(name="builtin.select")

            self.report({'INFO'}, 'OK!')
            bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_apply_curve(bpy.types.Operator):
    """"Apply curve and find emboss region"""
    bl_idname = "mesh.apply_curve_generate_panel"
    bl_label = "Apply Curve And Generate Emboss Panel"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        bpy.ops.ed.undo_push()

        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
        
        if len(context.selected_objects) > 0:
            if context.mode == 'EDIT_MESH':
                bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.convert(target='MESH')
            selected_obejcts_list = context.selected_objects.copy()
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected_obejcts_list:
                context.view_layer.objects.active = obj
                obj.select_set(True)
                tooth_object_name = obj.name.lstrip('curve_')
                tooth_object = context.collection.objects[tooth_object_name]
                
                curve_object = context.object
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.context.tool_settings.mesh_select_mode = (True, False, False)
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='cubic', lock_x=False, lock_y=False, lock_z=False)
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')

                context.view_layer.objects.active = curve_object
                curve_object.select_set(True)

                bpy.ops.object.modifier_add(type='SUBSURF')
                bpy.context.object.modifiers["Subdivision"].levels = 1
                bpy.ops.object.modifier_add(type='SHRINKWRAP')
                bpy.context.object.modifiers["Shrinkwrap"].target = tooth_object
                bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'OUTSIDE_SURFACE'
                bpy.context.object.modifiers["Shrinkwrap"].offset = -0.2
                bpy.ops.object.modifier_add(type='SMOOTH')
                bpy.context.object.modifiers["Smooth"].iterations = 100

                bpy.ops.object.duplicate()
                curve_object_copy = context.object
                bpy.context.object.modifiers["Shrinkwrap"].offset = 0.7 
                bpy.context.object.modifiers["Smooth"].iterations = 200
                context.view_layer.objects.active = curve_object
                curve_object.select_set(True)

                bpy.ops.object.convert(target='MESH')

                bpy.ops.object.join()
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='cubic', lock_x=False, lock_y=False, lock_z=False)
                bpy.ops.mesh.bridge_edge_loops(type='PAIRS')
                bpy.ops.object.mode_set(mode='OBJECT')

                context.view_layer.objects.active = tooth_object
                tooth_object.select_set(True)
                bpy.ops.object.join()
                
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_add()
                tooth_object.vertex_groups['Group'].name = 'panel'
                bpy.ops.object.vertex_group_assign()

                bpy.ops.mesh.intersect(threshold=0.0)

                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')

            for obj in context.collection.objects:
                if obj.name.startswith('Tooth') and not obj.name.endswith('_coord'):
                    context.view_layer.objects.active = obj
                    obj.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.loop_to_region()
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')

            for obj in context.collection.objects:
                if obj.name.startswith('Tooth') and not obj.name.endswith('_coord'):
                    context.view_layer.objects.active = obj
                    obj.select_set(True)
                    bpy.ops.object.mode_set(mode='EDIT')
                    if context.object.data.total_vert_sel < 3000:
                        bpy.ops.object.vertex_group_add()
                        obj.vertex_groups['Group'].name = 'inner_plane'
                        bpy.ops.object.vertex_group_assign()

                        bpy.ops.mesh.select_all(action='DESELECT')
                        obj.vertex_groups.active = obj.vertex_groups['panel']
                        bpy.ops.object.vertex_group_select()
                        bpy.ops.object.vertex_group_remove()
                        
                        bpy.ops.mesh.select_linked(delimit=set())
                        bpy.ops.mesh.delete(type='VERT')

                        bpy.ops.mesh.select_all(action='DESELECT')
                        obj.vertex_groups.active = obj.vertex_groups['inner_plane']
                        bpy.ops.object.vertex_group_select()
                        bpy.ops.mesh.duplicate(mode=1)
                        bpy.ops.mesh.separate(type='SELECTED')
                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.object.select_all(action='DESELECT')
                        
                        panel_name = obj.name + '.001'
                        panel_object = bpy.data.objects[panel_name]
                        panel_object.data.name = 'panel_' + obj.name
                        panel_object.name = 'panel_' + obj.name

                        context.view_layer.objects.active = panel_object    
                        panel_object.select_set(True)
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='SELECT')
                        bpy.ops.mesh.remove_doubles(threshold=0.005, use_unselected=True)
                        bpy.ops.mesh.region_to_loop()
                        bpy.ops.mesh.dissolve_limited(angle_limit=3.14)
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.object.select_all(action='DESELECT')
                    else:
                        bpy.ops.object.mode_set(mode='OBJECT')
                        bpy.ops.object.select_all(action='DESELECT')
                # bpy.ops.mesh.hide()
                # bpy.ops.object.mode_set(mode='OBJECT')

                # dir = mathutils.Vector((0, 0, 1))
                # dist = 10
                # origin = mathutils.Vector((0, 0, 0))
                # result1 = tooth_object.ray_cast(origin, dir, distance=dist)
                # print(result1)
                # tooth_object.data.polygons[result1[3]].select = True
                # bpy.ops.object.mode_set(mode='EDIT')
                # bpy.ops.mesh.select_linked(delimit=set())
                # bpy.ops.mesh.reveal()

                # bpy.ops.object.mode_set(mode='OBJECT')
                # bpy.ops.object.select_all(action='DESELECT')

            bpy.context.scene.cursor.location = mathutils.Vector((0.0, 0.0, 0.0))
            bpy.context.scene.cursor.rotation_euler = mathutils.Vector((0.0, 0.0, 0.0))

            self.report({'INFO'}, 'OK!')
            bpy.ops.ed.undo_push()
            
        return {'FINISHED'}

class MESH_TO_exturde_emboss_panel(bpy.types.Operator):
    """"Extrude An Emboss Panel"""
    bl_idname = "mesh.extrude_panel"
    bl_label = "Extrude panel"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']

        bpy.ops.object.select_all(action='DESELECT')
        for obj in context.collection.objects:
            if obj.name.startswith('Tooth') and not obj.name.endswith('_coord'):
                context.view_layer.objects.active = obj
                obj.select_set(True)

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.context.tool_settings.mesh_select_mode = (True, False, False)
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.mesh.select_non_manifold()
                bpy.ops.mesh.edge_face_add()
                bpy.ops.mesh.poke(offset=-1, use_relative_offset=True, center_mode='BOUNDS')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')

                obj.select_set(False)

        bpy.ops.object.select_all(action='DESELECT')
        for obj in context.collection.objects:
            if obj.name.startswith('panel'):
                context.view_layer.objects.active = obj
                obj.select_set(True)

                tooth_name = obj.name.lstrip('panel_')
                tooth_object = context.collection.objects[tooth_name]

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.context.tool_settings.mesh_select_mode = (False, True, False)
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.region_to_loop()
                bpy.ops.mesh.duplicate(mode=1)
                bpy.ops.mesh.separate(type='SELECTED')
                bpy.context.tool_settings.mesh_select_mode = (True, False, False)
                bpy.ops.object.mode_set(mode='OBJECT')
                for object in context.selected_objects:
                    if object.name.endswith('.001'):
                        object.data.name = 'emCurve_' + tooth_name
                        object.name = 'emCurve_' + tooth_name
                        context.view_layer.objects.active = object
                        object.select_set(True)
                    else:
                        object.select_set(False)
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='cubic', lock_x=False, lock_y=False, lock_z=False)
                bpy.ops.object.mode_set(mode='OBJECT')
                ref_curve_object = context.object
                bpy.ops.object.duplicate()
                ref_curve_object.select_set(True)
                bpy.ops.object.convert(target='CURVE')

                for curve in context.selected_objects:
                    if curve.name.endswith('.001'):
                        context.view_layer.objects.active = curve
                        curve.select_set(True)
                        # curve.data.taper_object = ref_curve_object
                        curve.data.extrude = 0.001
                        curve.data.offset = -0.3
                    else:
                        curve.select_set(False)
                bpy.ops.object.select_all(action='DESELECT') 

        for obj in context.collection.objects:
            if obj.name.startswith('emCurve') and not obj.name.endswith('.001'):
                small_curve_name = obj.name + '.001'
                small_curve_object = context.collection.objects[small_curve_name]
                tooth_name = obj.name.lstrip('emCurve_')
                tooth_object = context.collection.objects[tooth_name]
                panel_name = 'panel_' + tooth_name
                panel_object = context.collection.objects[panel_name]
                ref_volume = get_bound_box_volume(obj)
                small_volume = get_bound_box_volume(small_curve_object)
                context.view_layer.objects.active = small_curve_object
                small_curve_object.select_set(True)
                if small_volume > ref_volume:
                    print('Need to change direction object', obj.name)
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.curve.switch_direction()
                    bpy.ops.object.mode_set(mode='OBJECT')

                bpy.ops.object.modifier_add(type='SHRINKWRAP')
                bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'TARGET_PROJECT'
                bpy.context.object.modifiers["Shrinkwrap"].target = panel_object

                # bpy.ops.object.modifier_add(type='SMOOTH')
                # bpy.context.object.modifiers["Smooth"].iterations = 100
                # bpy.context.object.modifiers["Smooth"].factor = 0.7

                bpy.ops.object.convert(target='MESH')
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.remove_doubles(threshold=0.01)
                bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='cubic', lock_x=False, lock_y=False, lock_z=False)
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = obj
                obj.select_set(True)
                bpy.ops.object.delete(use_global=False, confirm=True)
                bpy.ops.object.select_all(action='DESELECT')    

                context.view_layer.objects.active = panel_object
                panel_object.select_set(True)

                bpy.ops.object.modifier_add(type='SOLIDIFY')
                bpy.context.object.modifiers["Solidify"].thickness = 1
                bpy.context.object.modifiers["Solidify"].offset = 0
                bpy.context.object.modifiers["Solidify"].use_even_offset = True

                bpy.ops.object.modifier_add(type='REMESH')
                bpy.context.object.modifiers["Remesh"].voxel_size = 0.1
                
                bpy.ops.object.modifier_add(type='SMOOTH')
                bpy.context.object.modifiers["Smooth"].factor = 0.5
                bpy.context.object.modifiers["Smooth"].iterations = 100

                bpy.ops.object.modifier_add(type='BOOLEAN')
                bpy.context.object.modifiers["Boolean"].object = tooth_object

                bpy.ops.object.select_all(action='DESELECT')
                
        bpy.ops.object.select_all(action='DESELECT')
        self.report({'INFO'}, 'OK!')
        bpy.ops.ed.undo_push()

        return {'FINISHED'}

class MESH_TO_resize_emboss_panel(bpy.types.Operator):
    """"Resize Emboss Panel"""
    bl_idname = "mesh.resize_panel"
    bl_label = "Resize Panel"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        extrude_factor = mytool.factor

        if context.mode == 'EDIT_MESH':
            bpy.ops.object.vertex_group_select()
            bpy.ops.transform.resize(value=(1.02, 1.02, 1.02), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
            bpy.ops.mesh.select_all(action='DESELECT')
            mytool.factor = extrude_factor + 0.02
            
        return {'FINISHED'}

class MESH_TO_smooth_panel_edge(bpy.types.Operator):
    """Smooth Panel Edge"""
    bl_idname = "mesh.smooth_panel_edge"
    bl_label = "Smooth Edge"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        mytool.factor = 1.0

        bpy.ops.wm.tool_set_by_id(name="builtin.select")
        if context.object.data.total_edge_sel > 100:
            bpy.ops.transform.shrink_fatten(value=-0.25, use_even_offset=True, mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
            bpy.ops.mesh.bevel(offset_type='OFFSET', offset=0.33, offset_pct=0, segments=7, profile=0.7, vertex_only=False, harden_normals=True)
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            context.object.data.remesh_voxel_size = 0.05
            bpy.ops.object.voxel_remesh()
            bpy.ops.object.modifier_add(type='SMOOTH')
            bpy.context.object.modifiers["Smooth"].iterations = 15
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Smooth")
            bpy.context.scene.transform_orientation_slots[0].type = 'LOCAL'
            bpy.context.scene.transform_orientation_slots[1].type = 'LOCAL'

            self.report({'INFO'}, 'OK!')
            bpy.ops.ed.undo_push()

            
        return {'FINISHED'}

class MESH_TO_emboss_image(bpy.types.Operator):
    """Emboss Image"""
    bl_idname = "mesh.emboss_image"
    bl_label = "emboss_image"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']

        bpy.ops.object.select_all(action='DESELECT')
        for obj in context.collection.objects:
            if obj.name.startswith('panel'):
                context.view_layer.objects.active = obj
                obj.select_set(True)

                bpy.ops.object.convert(target='MESH')
                bpy.ops.object.vertex_group_remove(all=True, all_unlocked=False)

                tooth_name = obj.name.lstrip('panel_')
                tooth_object = context.collection.objects[tooth_name]

                obj.select_set(False)

                curve_name =  'emCurve_' + tooth_name + '.001'
                curve_object = context.collection.objects[curve_name]
                context.view_layer.objects.active = curve_object
                curve_object.select_set(True)
                bpy.ops.object.vertex_group_remove(all=True, all_unlocked=False)
                bpy.context.scene.tool_settings.use_snap = True

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.subdivide()
                bpy.ops.mesh.subdivide()
                bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='cubic', lock_x=False, lock_y=False, lock_z=False)
                bpy.ops.object.mode_set(mode='OBJECT')

                bpy.ops.object.modifier_add(type='SHRINKWRAP')
                bpy.context.object.modifiers["Shrinkwrap"].target = obj
                bpy.ops.object.convert(target='MESH')

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='cubic', lock_x=False, lock_y=False, lock_z=False)
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')

                bpy.ops.object.modifier_add(type='SHRINKWRAP')
                bpy.context.object.modifiers["Shrinkwrap"].target = obj
                bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'NEAREST_SURFACEPOINT'
                bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'ABOVE_SURFACE'   
                bpy.context.object.modifiers["Shrinkwrap"].offset = -0.12

                bpy.ops.object.modifier_add(type='SMOOTH')
                bpy.context.object.modifiers["Smooth"].iterations = 100

                bpy.ops.object.duplicate()    
                bpy.context.object.modifiers["Shrinkwrap"].offset = 0.15
                curve_object.select_set(True)
                bpy.ops.object.convert(target='MESH')

                context.view_layer.objects.active = curve_object
                curve_object.select_set(True)
                bpy.ops.object.join()

                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.bridge_edge_loops(type='PAIRS')

                bpy.ops.object.vertex_group_add()
                curve_object.vertex_groups['Group'].name = 'panel'
                bpy.ops.object.vertex_group_assign()
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = obj
                obj.select_set(True)

                bpy.context.object.data.remesh_voxel_size = 0.03
                bpy.context.object.data.use_remesh_smooth_normals = True
                bpy.ops.object.voxel_remesh()
                bpy.ops.object.select_all(action='DESELECT')
                bpy.ops.ed.undo_push()

        for obj in context.collection.objects:
            if obj.name.startswith('panel'):    
                tooth_name = obj.name.lstrip('panel_')
                tooth_object = context.collection.objects[tooth_name]
                curve_name =  'emCurve_' + tooth_name + '.001'
                curve_object = context.collection.objects[curve_name]

                context.view_layer.objects.active = obj
                obj.select_set(True)

                curve_object.select_set(True)

                bpy.ops.object.join()
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.context.tool_settings.mesh_select_mode = (True, False, False)
                bpy.ops.mesh.intersect()

                bpy.ops.mesh.hide()
                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')


                dir = mathutils.Vector((0, 0, 1))
                dist = 10
                origin = mathutils.Vector((0, 0, 0))
                result1 = obj.ray_cast(origin, dir, distance=dist)
                obj.data.polygons[result1[3]].select = True
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_linked(delimit=set())
                bpy.ops.mesh.reveal()

                bpy.ops.object.vertex_group_add()
                context.object.vertex_groups['Group'].name = 'inner_panel'
                bpy.ops.object.vertex_group_assign()
                bpy.ops.mesh.select_all(action='DESELECT')

                context.object.vertex_groups.active = context.object.vertex_groups['panel']
                bpy.ops.object.vertex_group_select()
                bpy.ops.object.vertex_group_remove()

                bpy.ops.mesh.select_linked(delimit=set())
                bpy.ops.mesh.delete(type='VERT')
                bpy.ops.mesh.select_all(action='DESELECT')
                context.object.vertex_groups.active = context.object.vertex_groups['inner_panel']
                bpy.ops.object.vertex_group_select()
                bpy.ops.mesh.subdivide()
                bpy.ops.mesh.select_all(action='INVERT')
                bpy.ops.mesh.unsubdivide(iterations=9)
                bpy.ops.mesh.select_all(action='INVERT')
                bpy.ops.object.mode_set(mode='OBJECT')

                bpy.ops.object.modifier_add(type='SHRINKWRAP')
                context.object.modifiers["Shrinkwrap"].target = tooth_object
                context.object.modifiers["Shrinkwrap"].wrap_method = 'TARGET_PROJECT'
                context.object.modifiers["Shrinkwrap"].wrap_mode = 'ON_SURFACE'
                context.object.modifiers["Shrinkwrap"].vertex_group = "inner_panel"

                context.object.modifiers.new(name='Displace', type='DISPLACE')
                context.object.modifiers['Displace'].mid_level = 0
                context.object.modifiers['Displace'].strength = -0.2
                context.object.modifiers['Displace'].vertex_group = 'inner_panel'
                context.object.modifiers['Displace'].direction = 'NORMAL'
                context.object.modifiers["Displace"].texture_coords = 'LOCAL'

                image_name = 'Grid_pic\\' + bpy.context.object.name.split('_')[2] + '-1.jpg'
                file_name = bpy.context.object.name.split('_')[2] + '-1.jpg'
                
                image_file_path = os.path.expanduser('~') +'\\AppData\\Roaming\\Blender Foundation\\Blender\\2.83\\config\\Grid_Pic'
                bpy.ops.image.open(filepath=image_name, 
                    directory=image_file_path, 
                    files=[{"name":file_name, "name":file_name}], 
                    relative_path=True, 
                    show_multiview=False)
                print('image file path', image_file_path)
                img = bpy.data.images[file_name]
                bpy.ops.texture.new()

                texture = bpy.data.textures.get('Texture')
                if texture is not None:
                    texture.name = 'texture_' + tooth_name
                    texture.image = img
                    texture.repeat_x = 1
                    texture.repeat_y = 2
                    texture.crop_min_x = 0.6
                    texture.crop_min_y = 0.6
                    texture.crop_max_x = 0.82
                    texture.crop_max_y = 0.82
                    texture.use_flip_axis = False
                    texture.factor_red = 1.5
                    texture.factor_green = 1.5
                    texture.factor_blue = 1.5
                else:
                    texture.image = img
                context.object.modifiers['Displace'].texture = texture

                bpy.context.scene.transform_orientation_slots[0].type = 'LOCAL'
                context.view_layer.objects.active = obj
                obj.select_set(True)
                orientation_matirx = obj.matrix_local.copy()
                orientation_matirx.transpose()
                a = (orientation_matirx.row[0][0], orientation_matirx.row[0][1], orientation_matirx.row[0][2])
                b = (orientation_matirx.row[1][0], orientation_matirx.row[1][1], orientation_matirx.row[1][2])
                c = (orientation_matirx.row[2][0], orientation_matirx.row[2][1], orientation_matirx.row[2][2])
                bpy.context.scene.tool_settings.use_transform_data_origin = True
                bpy.ops.transform.rotate(value=3.14159, orient_axis='Z', orient_type='LOCAL', orient_matrix=(a, b, c), orient_matrix_type='LOCAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
                bpy.context.scene.tool_settings.use_transform_data_origin = False

                bpy.ops.object.select_all(action='DESELECT')
                print(context.object.name, 'Context name emboss finished!')

        bpy.context.scene.tool_settings.use_transform_data_origin = True
        bpy.context.scene.transform_orientation_slots[0].type = 'LOCAL'
        bpy.context.scene.transform_orientation_slots[1].type = 'LOCAL'
        bpy.context.space_data.show_gizmo_object_rotate = True
        bpy.context.space_data.show_gizmo_object_translate = True
        bpy.context.scene.tool_settings.use_snap = False

        self.report({'INFO'}, 'OK!')
        bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_apply_emboss(bpy.types.Operator):
    """Apply Emboss"""
    bl_idname = "mesh.apply_emboss"
    bl_label = "Apply Emboss"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']

        bpy.ops.object.select_all(action='DESELECT')
        for obj in context.collection.objects:
            if obj.name.startswith('panel'):
                context.view_layer.objects.active = obj
                obj.select_set(True)

                bpy.ops.object.convert(target='MESH')

                bpy.ops.object.modifier_add(type='REMESH')
                bpy.context.object.modifiers["Remesh"].voxel_size = 0.02
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Remesh")

                bpy.ops.object.modifier_add(type='DECIMATE')
                bpy.context.object.modifiers["Decimate"].ratio = 0.15
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Decimate")

                bpy.ops.object.modifier_add(type='DECIMATE')
                bpy.context.object.modifiers["Decimate"].ratio = 0.5
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Decimate")

                bpy.ops.object.select_all(action='DESELECT')
                print('info:', obj.name ,' Remesh Finished!')
            else:
                if obj.name.startswith('Tooth') and not obj.name.endswith('_coord'):
                  pass

                bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_show_teeth(bpy.types.Operator):
    """"Show Teeth"""
    bl_idname = "mesh.show_teeth"
    bl_label = "Show Teeth"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
        
        for obj in context.collection.objects:
            if obj.name.startswith('Tooth') and not obj.name.endswith('_coord'):
                obj.hide_set(False)
        bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_hide_teeth(bpy.types.Operator):
    """"Show Teeth"""
    bl_idname = "mesh.hide_teeth"
    bl_label = "Hide Teeth"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
        
        for obj in context.collection.objects:
            if obj.name.startswith('Tooth') and not obj.name.endswith('_coord'):
                obj.hide_set(True)
        bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_sort_teeth(bpy.types.Operator):
    """"Sort Teeth"""
    bl_idname = "mesh.sort_teeth"
    bl_label = "Sort Teeth"

    def execute(self, context):
        filename = os.path.expanduser('~')+"\\AppData\\Roaming\\Blender Foundation\\Blender\\2.83\\scripts\\addons\\pie_menu_editor\\scripts\\sort_teeth.py" 
        exec(compile(open(filename).read(), filename, 'exec'))
        return {'FINISHED'}

class MESH_TO_pick_tooth(bpy.types.Operator):
    """"Pick A Select Tooth Out"""
    bl_idname = "mesh.pick_tooth"
    bl_label = "Pick A Tooth"

    def execute(self, context):   
        if len(context.selected_objects) == 1 and context.selected_objects[0].name.startswith('Tooth'):
            if bpy.data.collections.get('Pick_Teeth') is None:
                pick_teeth_coll = bpy.data.collections.new('Pick_Teeth')
                context.scene.collection.children.link(pick_teeth_coll)

            bpy.data.collections['Pick_Teeth'].objects.link(context.object)
            unlink_coll = context.object.users_collection
            unlink_coll[0].objects.unlink(context.object)
            context.object.data.name = 'pick_' + context.object.data.name
            context.object.name = 'pick_' + context.object.name
            context.object.hide_set(True)
            bpy.ops.ed.undo_push()

        return {'FINISHED'}

class MESH_TO_restore(bpy.types.Operator):
    """"Restore A Select Tooth From Picked Teeth Collection"""
    bl_idname = "mesh.restore"
    bl_label = "Restore"

    def execute(self, context): 
        scene = context.scene
        mytool = scene.my_tool

        if bpy.data.collections.get('Pick_Teeth'):
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Pick_Teeth']
            restore_tooth_name = mytool.picked_tooth_name
            number = int(restore_tooth_name.split('_')[2])
            if number > 10 and number < 30:
                link_collection = bpy.data.collections['Curves_U']
            else:
                link_collection = bpy.data.collections['Curves_D']
            restore_object = context.collection.objects[restore_tooth_name]
            restore_object.hide_set(False)
            restore_object.data.name = restore_tooth_name.lstrip('pick')
            restore_object.name = restore_tooth_name.lstrip('pick')
            link_collection.objects.link(restore_object)
            context.collection.objects.unlink(restore_object)
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[link_collection.name]
            bpy.ops.ed.undo_push()

        return {'FINISHED'}

class MESH_TO_complement_tooth_bottom(bpy.types.Operator):
    """"Complement Teeth Bottom"""
    bl_idname = "mesh.complement_teet_bottom"
    bl_label = "complement Teeth Bottom"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']

        # fill_all_teeth_hide()
        bpy.ops.ed.undo_push()

        return {'FINISHED'}

class MESH_TO_select_three_points(bpy.types.Operator):
    """"Pick Three Triangle To Specific A Panel"""
    bl_idname = "mesh.select_three_points"
    bl_label = "Select Three Point"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']

        jawplaneName = 'jawPlane_' + mytool.up_down
        delete_object(jawplaneName)
        into_select_faces_mode_jaw()
        bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_generate_adjust_arch(bpy.types.Operator):
    """"Generate Teeth Arch Line And Adjust it"""
    bl_idname = "mesh.generate_adjust_arch"
    bl_label = "Generate Arch Line"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
            curve_name = 'up_arch'
            jawplaneName = 'jawPlane_' + mytool.up_down
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
            curve_name = 'down_arch'
            jawplaneName = 'jawPlane_' + mytool.up_down

        create_plane(jawplaneName)
        print('================== Successfully Genertate Plane ========================')
        
        bpy.ops.object.select_all(action='DESELECT')
        for obj in context.collection.objects:
            if obj.name.startswith('Tooth') and not obj.name.endswith('_coord'):
                context.view_layer.objects.active = obj
                obj.select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')

                jaw_plane_object = bpy.data.objects[jawplaneName]
                tooth_number = int(obj.name.split('_')[1])
                M_orient = get_plane_ref_coord_matrix(jaw_plane_object, obj, mytool.up_down)
                tip_angle = get_tip(obj, M_orient.copy(), tooth_number)
                tor_angle = get_torque(obj, M_orient.copy())
                # bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
                # context.object.matrix_local = M_orient
                bpy.ops.object.select_all(action='DESELECT')
                
                for prefix in ('Tip', 'Tor'):
                    prop_name = prefix + '_' + str(tooth_number)
                    if prefix == 'Tip':
                        setattr(mytool, prop_name, tip_angle)
                    if prefix == 'Tor':
                        setattr(mytool, prop_name, tor_angle) 
                print('==============================================')

        # Generate arch and enter edit mode for adjust
        sum_location = 0
        qunatity = 0
        for idx, obj in enumerate(context.collection.objects):
            if obj.name.startswith('Tooth') and not obj.name.endswith('_coord'):
                loca = obj.location
                sum_location = sum_location + loca[2]
                qunatity = qunatity + 1
                scene.cursor.location = loca
                bpy.ops.mesh.primitive_vert_add()
                bpy.ops.object.mode_set(mode='OBJECT')
                context.object.data.name = curve_name + '_vert_' + str(idx)
                context.object.name = curve_name + '_vert_' + str(idx)
                context.object.location[2] = 0.0
                if bpy.data.collections.get('Arch') is None:
                    arch_coll = bpy.data.collections.new('Arch')
                    context.scene.collection.children.link(arch_coll)
                bpy.data.collections['Arch'].objects.link(context.object)
                context.collection.objects.unlink(context.object)

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Arch']        
        for obj in context.collection.objects: 
            if obj.name.startswith(curve_name): 
                context.view_layer.objects.active = obj
                obj.select_set(True)
        bpy.ops.object.join()
        
        dental_arch = context.object
        dental_arch.data.name = curve_name
        dental_arch.name = curve_name
        dental_arch.show_name = True

        if mytool.up_down == 'UP_':
            dental_arch.location[2] = (sum_location / qunatity) - 5
        else:
            dental_arch.location[2] = (sum_location / qunatity) + 5

        context.scene.cursor.location = mathutils.Vector((0.0, 0.0, 0.0))
        context.scene.cursor.rotation_euler = mathutils.Vector((0.0, 0.0, 0.0))
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = (True, False, False)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        
        vertices = dental_arch.data.vertices

        angle_inde_dict = dict()
        for index, vrt in enumerate(vertices):
            location = vrt.co

            if location[1] == 0 and location[0] < 0 :
                angle = math.atan((-location[0])/location[1])
                angle = math.pi / 2
            elif location[1] == 0 and location[0] > 0:
                angle = math.atan((-location[0])/location[1])
                angle = math.pi + math.pi / 2
            elif location[0] > 0 and location[1] > 0:
                angle = math.atan((-location[0])/location[1])
                angle = angle + 2 * math.pi
            elif location[0] > 0 and location[1] < 0:
                angle = math.atan((-location[0])/location[1])
                angle = angle + math.pi
            elif location[0] < 0 and location[1] < 0:
                angle = math.atan((-location[0])/location[1])
                angle = angle + math.pi
            else:
                angle = math.atan((-location[0])/location[1])
            # print(index,angle/math.pi*180)
            angle_inde_dict[index] =  angle                                         
        sort_list = sorted(angle_inde_dict.items(), key=lambda item:item[1])
        print(sort_list)

        for idx, item in enumerate(sort_list):
            if idx == len(sort_list)-1:
                break   
            vertices[sort_list[idx][0]].select = True
            vertices[sort_list[idx+1][0]].select = True
            
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)
            bpy.ops.mesh.edge_face_add()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

        end = len(sort_list) - 1
        start = 0
        vertices[sort_list[end][0]].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(4.0, 10.0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
        bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(2.0, 10.0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        vertices[sort_list[start][0]].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(-4.0, 10.0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
        bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(-2.0, 10.0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.modifier_add(type='SUBSURF')
        bpy.context.object.modifiers["Subdivision"].levels = 2
        bpy.context.object.modifiers["Subdivision"].show_on_cage = True
        
        bpy.ops.object.modifier_add(type='SMOOTH')
        bpy.context.object.modifiers["Smooth"].iterations = 20
        bpy.context.object.modifiers["Smooth"].show_in_editmode = True
        bpy.context.object.modifiers["Smooth"].show_on_cage = True
        bpy.context.object.modifiers["Smooth"].factor = 0.7

        bpy.ops.object.modifier_add(type='SKIN')

        bpy.ops.object.modifier_add(type='MIRROR')
        bpy.context.object.modifiers["Mirror"].use_bisect_axis[0] = True
        

        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
        if mytool.up_down == 'UP_' and mytool.scale_up_arch == False:
            bpy.ops.transform.resize(value=(1.12, 1.12, 1.12), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
            mytool.scale_up_arch == True
        if mytool.up_down == 'DOWN_' and mytool.scale_down_arch == False:
            bpy.ops.transform.resize(value=(1.15, 1.15, 1.15), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
            mytool.scale_down_arch == True

        if bpy.data.materials.get('Arch') is None:
            mat = bpy.data.materials.new(name="Arch")
            mat.diffuse_color = (0, 0.56, 1, 1)
            context.object.active_material = mat
        else:
            mat = bpy.data.materials['Arch']
            context.object.active_material = mat

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.vertices_smooth(factor=0.5)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.context.scene.tool_settings.use_snap = False
        bpy.ops.wm.tool_set_by_id(name="builtin.select")
        bpy.context.space_data.show_gizmo_object_translate = False

        bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_automatic_arrange_teeth(bpy.types.Operator):
    """"Automatic Arrange Teeth"""
    bl_idname = "mesh.automatic_arrange"
    bl_label = "Auto Arrage"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        
        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
            tip_torque = {'11':[5,7],'12':[9,4],'13':[11,0],'14':[2,0],'15':[2,0],'16':[0,-8],'17':[0,-8],'18':[0,0],'21':[5,7],'22':[9,4],'23':[11,0],'24':[2,0],'25':[2,0],'26':[0,-8],'27':[0,-8],'28':[0,0]}
            arch_name = 'up_arch'
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
            tip_torque = {'41':[2,2],'42':[2,2],'43':[5,-3],'44':[2,0],'45':[2,-5],'46':[0,-15],'47':[0,-15],'48':[0,0],'31':[2,2],'32':[2,2],'33':[5,-3],'34':[2,-5],'35':[2,-8],'36':[0,-15],'37':[0,-15],'38':[0,-15]}
            arch_name = 'down_arch'

        bpy.ops.object.select_all(action='DESELECT')
        for obj in context.collection.objects:
            if obj.name.startswith('Tooth') and not obj.name.endswith('_coord'):
                tooth_number = obj.name.split('_')[1]
                tip_angle = tip_torque[tooth_number][0] * (math.pi / 180)
                tor_angle = tip_torque[tooth_number][1] * (math.pi / 180)
                for prefix in ('Tip', 'Tor'):
                    prop_name = prefix + '_' + tooth_number
                    if prefix == 'Tip':
                        setattr(mytool, prop_name, tip_angle)
                    if prefix == 'Tor':
                        setattr(mytool, prop_name, tor_angle) 

        dental_arch_name = 'dental_arch_' + mytool.up_down
        if bpy.data.objects.get(dental_arch_name):
            print('find dental_arch')
            context.view_layer.objects.active = bpy.data.objects[dental_arch_name]
            bpy.data.objects[dental_arch_name].select_set(True)
            bpy.ops.object.delete()

        edit_arch = bpy.data.objects[arch_name]
        context.view_layer.objects.active = edit_arch
        edit_arch.select_set(True)

        bpy.ops.object.duplicate()
        bpy.ops.object.modifier_remove(modifier="Skin")
        bpy.ops.object.convert(target='MESH')
        dental_arch = context.object
        dental_arch.data.name = dental_arch_name
        dental_arch.name = dental_arch_name

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='cubic', lock_x=False, lock_y=False, lock_z=False)
        bpy.ops.mesh.subdivide()
        bpy.ops.mesh.subdivide()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        context.scene.cursor.location = mathutils.Vector((0.0, 0.0, 0.0))
        context.scene.cursor.rotation_euler = mathutils.Vector((0.0, 0.0, 0.0))
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

        bpy.ops.object.select_all(action='DESELECT')

        vertices = dental_arch.data.vertices
        edges = dental_arch.data.edges
        arch_matrix = dental_arch.matrix_world.copy()

        bpy.ops.object.select_all(action='DESELECT')
        for obj in context.collection.objects:
            if obj.name.startswith('Tooth') and not obj.name.endswith('_coord'):
                context.view_layer.objects.active = obj
                obj.select_set(True) 

                min_dis = 100
                min_index = 0
                loca = obj.location
                tooth_matrix = obj.matrix_world.copy()
                
                for vertice in vertices:
                    disp = loca - vertice.co
                    dis = math.sqrt(disp[0]*disp[0] + disp[1]*disp[1])
                    if dis < 5: 
                        if dis < min_dis:
                            min_dis = dis
                            min_index = vertice.index
                a = []
                for edge in edges:
                    if edge.vertices[0] == min_index :
                        a.append(edge.vertices[1])
                    if edge.vertices[1] == min_index :
                        a.append(edge.vertices[0])
        
                vrt_1 = arch_matrix @ vertices[a[0]].co
                vrt_2 = arch_matrix @ vertices[a[1]].co
                middle_vrt = arch_matrix @ vertices[min_index].co
                w_x1 = vrt_1[0]
                w_y1 = vrt_1[1]

                w_x2 = vrt_2[0]
                w_y2 = vrt_2[1]
                # print('v1:', (w_x1, w_y1), 'v2:', (w_x2, w_y2))

                if (w_x2 - w_x1) != 0:
                        k = (w_y2 - w_y1) / (w_x2 - w_x1)
                        if k != 0:
                            k2 = -(1/k)
                            b2 = middle_vrt[1] - middle_vrt[0] * k2
                            print('k is :', k, k2, obj.name)
                            point_x = 0
                            point_y = b2
                            
                            vector1_x = point_x - middle_vrt[0]
                            vector1_y = point_y - middle_vrt[1]
                        else:
                            vector1_x = 0
                            vector1_y = -1
                else:
                    if w_x1 < 0:
                        vector1_x = 1
                        vector1_y = 0
                    else:
                        vector1_x = -1
                        vector1_y = 0
                axis_x = tooth_matrix.row[0][2]
                axis_y = tooth_matrix.row[1][2]
                print(tooth_matrix)

                len1 = math.sqrt((vector1_x * vector1_x) + (vector1_y * vector1_y))
                len2 = math.sqrt((axis_x * axis_x) + (axis_y * axis_y))
                vector1_x = vector1_x / len1
                vector1_y = vector1_y / len1
                axis_x = axis_x / len2
                axis_y = axis_y / len2
                print('Vector', (vector1_x, vector1_y))
                print('Axis:', (axis_x,axis_y))

                dot = vector1_x * axis_x + vector1_y * axis_y 
                theta  = math.acos(dot)
                P_N = axis_x * vector1_y - vector1_x * axis_y
                if (P_N < 0 and mytool.up_down == 'UP_'):
                    theta = -theta
                if (P_N > 0 and mytool.up_down == 'DOWN_'):
                    theta = -theta
                z_axis = mathutils.Vector((axis_x, axis_y, 0))
                z_axis.normalize()
                print('z_axis', z_axis)
                temp_x = vrt_1 - vrt_2
                temp_x.normalize()
                y_axis = temp_x.cross(z_axis)
                y_axis.normalize()
                if mytool.up_down == "UP_":
                    if y_axis[2] < 0:
                        y_axis[2] = abs(y_axis[2])
                else:
                    if y_axis[2] > 0:
                        y_axis[2] = -abs(y_axis[2])
                print('y_axis', y_axis)
                x_axis = y_axis.cross(z_axis)
                x_axis.normalize()
                print('x_axis', x_axis)
            
                M_orient = mathutils.Matrix([x_axis, y_axis, z_axis])
                M_orient.normalize()

                print('M_orient')
                print(M_orient)
                print('angle is:', theta * (180 / math.pi), 'P_N:', P_N)
                
                a = (M_orient.row[0][0],M_orient.row[0][1],M_orient.row[0][2])
                b = (M_orient.row[1][0],M_orient.row[1][1],M_orient.row[1][2])
                c = (M_orient.row[2][0],M_orient.row[2][1],M_orient.row[2][2])

                bpy.ops.transform.rotate(value=theta, orient_axis='Y', orient_type='LOCAL', orient_matrix=(a, b, c), orient_matrix_type='LOCAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
                if mytool.up_down == 'UP_':
                    a = M_orient.copy()
                    a.transpose()
                    b = a.to_4x4()
                    b.row[0][3] = obj.location[0]
                    b.row[1][3] = obj.location[1]
                    b.row[2][3] = obj.location[2]
                    # bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0))
                    # context.object.matrix_local = b
                    bpy.ops.object.select_all(action='DESELECT')
                    # move tooth into right position
                    # temp_min = 100
                    # temp_max = -100
                    # tooth_vertices = obj.data.vertices
                    # for vrt in tooth_vertices:
                    #     if vrt.co[2] < 0 and abs(vrt.co[0]) < 0.3:
                    #         vrt.select = True
                    #         if vrt.co[2] < temp_min:
                    #             temp_min = vrt.co[2]
                    #         if vrt.co[2] > temp_max:
                    #             temp_max = vrt.co[2]
                    # print(temp_min,temp_max)
                    # z_co = (temp_max + temp_min) / 2
                    # co = mathutils.Vector((0,0,z_co))
                    # new_co = tooth_matrix @ co
                    # print('world co', new_co)
                    # loca_x = new_co[0]
                    # loca_y = new_co[1]
                    # cursor = mathutils.Vector((loca_x, loca_y, 0))
                    # context.scene.cursor.location = cursor
                    # bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
                    # loca_af = obj.location
                    # print('loca_after', loca_af)
                    # min_dis = 20
                    # for vertice in vertices:
                    #     vrt_co = arch_matrix @ vertice.co
                    #     disp = loca_af - vrt_co
                    #     dis = math.sqrt(disp[0]*disp[0] + disp[1]*disp[1])
                    #     if dis < 3:
                    #         print('calculte dist', dis, vertice.index) 
                    #         if dis < min_dis:
                    #             min_dis = dis
                    #             min_index = vertice.index
                    # vertices[min_index].select = True
                    # vrt_co_ = arch_matrix @ vertices[min_index].co
                    # obj.location[0] = vrt_co_[0]
                    # obj.location[1] = vrt_co_[1]
                    # bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                # else:
                #     temp_loca = mathutils.Vector((0, 0, 0))
                #     num = 0
                #     tooth_vertices = obj.data.vertices
                #     for vrt in tooth_vertices:
                #         if vrt.co[2] < 0 and abs(vrt.co[0]) < 0.3 and abs(vrt.co[1]) < 0.3:
                #             temp_co = tooth_matrix @ vrt.co
                #             temp_loca = temp_loca + temp_co
                #             num = num + 1
                #     world_loca = temp_loca / num
                #     print('world_loca', world_loca)
                #     context.scene.cursor.location = world_loca
                #     bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
                #     min_dis = 20
                #     for vertice in vertices:
                #         vrt_co = arch_matrix @ vertice.co
                #         disp = world_loca - vrt_co
                #         dis = math.sqrt(disp[0]*disp[0] + disp[1]*disp[1])
                #         if dis < 5:
                #             print('calculte dist', dis, vertice.index) 
                #             if dis < min_dis:
                #                 min_dis = dis
                #                 min_index = vertice.index
                #     vertices[min_index].select = True
                #     vrt_co_ = arch_matrix @ vertices[min_index].co
                #     obj.location[0] = vrt_co_[0]
                #     obj.location[1] = vrt_co_[1]
                #     bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
                print('-----------------------------------------------------------------')
                obj.select_set(False) 


                 
        bpy.ops.ed.undo_push()
        

        return {'FINISHED'}

class MESH_TO_edit_arch(bpy.types.Operator):
    """"Edit Arch"""
    bl_idname = "mesh.edit_arch"
    bl_label = "Edit Arch"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Arch']
        if mytool.up_down == 'UP_':
            arch_name = 'up_arch'
        else:
            arch_name = 'down_arch'

        if context.mode == 'EDIT_MESH':  
            bpy.ops.object.mode_set(mode='OBJECT')
        
        bpy.ops.object.select_all(action='DESELECT')
        arch_object = context.collection.objects.get(arch_name)
        if arch_object is not None:
            arch_object = context.collection.objects[arch_name]
            context.view_layer.objects.active = arch_object
            arch_object.select_set(True) 
            bpy.ops.object.mode_set(mode='EDIT')
        else:
            print('There is not arch object!')

        bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_auto_tip(bpy.types.Operator):
    """"Auto Rotate Tip"""
    bl_idname = "mesh.auto_rotate_tip"
    bl_label = "Auto Rotate Tip"
         
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['plane']
        if mytool.up_down == 'UP_':
            plane_name = 'jawPlane_UP_'
        else:
            plane_name = 'jawPlane_DOWN_'
        plane_object = context.collection.objects[plane_name]
        plane_location = plane_object.location
        plane_normal_local = plane_object.data.polygons[0].normal
        plane_matrix_world = plane_object.matrix_world.copy()
        plane_normal_world = (plane_matrix_world @ plane_normal_local) - plane_location
        plane_normal_world.normalize()
        print('normal', plane_normal_world)
        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
        
        for obj in context.collection.objects:
            if obj.name.startswith('Tooth') and not obj.name.endswith('coord'):
                obj_matrix_world = obj.matrix_world.copy() 
                obj_matrix_world_invert = obj_matrix_world.inverted()
                normal_local = obj_matrix_world_invert @ (plane_normal_world + obj.location)
                normal_local.normalize()
                print(normal_local, obj.name)
                theta = -math.atan2(normal_local[0] , -normal_local[1]) 
                print(theta * (180 / math.pi))
                bpy.ops.object.select_all(action='DESELECT')
                context.view_layer.objects.active = obj
                obj.select_set(True)
                bpy.context.scene.transform_orientation_slots[0].type = 'LOCAL'
                bpy.ops.transform.create_orientation(name="local_orient", use=True)
                bpy.context.scene.transform_orientation_slots[0].type = 'local_orient'
                orientation_matirx = bpy.context.scene.transform_orientation_slots[0].custom_orientation.matrix.copy()
                orientation_matirx.transpose()
                a = (orientation_matirx.row[0][0], orientation_matirx.row[0][1], orientation_matirx.row[0][2])
                b = (orientation_matirx.row[1][0], orientation_matirx.row[1][1], orientation_matirx.row[1][2])
                c = (orientation_matirx.row[2][0], orientation_matirx.row[2][1], orientation_matirx.row[2][2])
                bpy.ops.transform.delete_orientation()
                bpy.context.scene.transform_orientation_slots[0].type = 'LOCAL'
                bpy.context.space_data.show_gizmo_object_translate = True
                bpy.context.space_data.show_gizmo_object_rotate = False

                bpy.ops.transform.rotate(value=-theta, orient_axis='Z', orient_type='LOCAL', orient_matrix=(a, b, c), orient_matrix_type='LOCAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
                
                bpy.ops.object.select_all(action='DESELECT')

                


        return {'FINISHED'}

class MESH_TO_put_on_brackets(bpy.types.Operator):
    """"Put Brackets On Teeth"""
    bl_idname = "mesh.put_on_brackets"
    bl_label = "Put On Bracket"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
        
        filespath = os.path.expanduser('~') + "\\AppData\\Roaming\\Blender Foundation\\Blender\\2.83\\config\\bracker\\new_bracker"
        if os.path.isdir(filespath):
            info = os.walk(filespath)
            for root, dirs, files in info:
                pass
        else:
            self.report({'ERROR'}, 'Brackets Path Error!')
            return {'CANCELLED'}
                 

        for panel_obj in context.collection.objects:
            if panel_obj.name.startswith('panel_'):
                tooth_number = panel_obj.name.split('_')[2]
                for file_name in files:
                    print('bb',tooth_number,file_name)
                    if file_name.startswith(str(tooth_number)):
                        print('aa',file_name)
                        bpy.ops.import_mesh.stl(filepath=(root + '\\' + file_name), 
                            filter_glob="*.stl", 
                            files=[{"name":file_name, "name":file_name}], 
                            directory=root, 
                            global_scale=1.0, 
                            use_scene_unit=False, 
                            use_facet_normal=False, 
                            axis_forward='Y', axis_up='Z')
                        # bpy.ops.import_mesh.stl(filepath="C://Users//Dom//Documents//DomCorp.//mymodel.stl", 
                        #     filter_glob="*.stl",  files=[{"name":"mymodel.stl", "name":"mymodel.stl"}], 
                        #     directory="C://Users//Dom//Documents//DomCorp.")

        bpy.ops.ed.undo_push()

        return {'FINISHED'}

class WM_OT_inter_capacity(bpy.types.Operator):
    """"Adjust Intercalation Capacity"""
    bl_idname = "wm.inter_capacity"
    bl_label = "Intercalation Capacity"
    
    intercalation1 : bpy.props.FloatProperty(name="Capacity", default=1)
         
    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add()
        return {'FINISHED'} 
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_popup(self, event)

class MESH_TO_test(bpy.types.Operator):
    """"Test"""
    bl_idname = "mesh.test"
    bl_label = "Test"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        if mytool.up_down == 'UP_':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']
            jawplaneName = 'jawPlane_' + mytool.up_down
        else:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_D']
            jawplaneName = 'jawPlane_' + mytool.up_down

        bpy.ops.object.select_all(action='DESELECT')
        for obj in context.collection.objects:
            if obj.name.startswith('Tooth') and not obj.name.endswith('_coord'):
                context.view_layer.objects.active = obj
                obj.select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                matrix_world = obj.matrix_world.copy()
                obj_loca = obj.location.copy()
                polygons = obj.data.polygons
                vertex_index = []
                cusp_points_hight=polygons[0].center[1]
                for face in polygons:
                    if face.center[2]<0 and cusp_points_hight>face.center[1]:
                        cusp_points_hight = face.center[1]
                        vertex_index.append(face.index)
                print(obj.name, 'min hight:', cusp_points_hight)

                dir = mathutils.Vector((0, 0, 1))
                dist = 10
                origin = mathutils.Vector((0, cusp_points_hight/4, -10))
                result = obj.ray_cast(origin, dir, distance=dist)
                polygons[result[3]].select = True
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_more()
                bpy.ops.mesh.select_more()
                bpy.ops.object.mode_set(mode='OBJECT')
                normal_vector = mathutils.Vector((0, 0, 0))
                num = 0
                for face in polygons:
                    if face.select == True:
                        normal_vector = normal_vector + face.normal
                        num = num + 1
                obj.select_set(False)
                normal_vector = normal_vector / num
                normal_vector.normalize()
                face_normal = (matrix_world @ normal_vector) - obj_loca
                face_normal.normalize()
                print('face_normal', face_normal)
                x_axis = mathutils.Vector((matrix_world.row[0][0], matrix_world.row[1][0], matrix_world[2][0]))
                y_axis = x_axis.cross(face_normal)
                y_axis.normalize()
                x_axis = face_normal.cross(y_axis)
                x_axis.normalize()

                # get_torque(obj)
        
        return {'FINISHED'}

class VIEW3D_PT_smooth_tooth_edge(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SmoothToothEdge'
    bl_label = 'SmoothToothEdge'

    def draw(self, context):
        scene = context.scene
        mytool = scene.my_tool

        # up or down property button
        row = self.layout.row(align=True)
        import_stl = row.operator('import_mesh.stl', text='Import STL')
        row = self.layout.row(align=True)
        ready_seperating = row.operator('mesh.ready_seperating', text='Read For Seperating')
        row = self.layout.row(align=True)
        up_donw = row.prop(mytool,'up_down', text='Up/Down')
        row = self.layout.row(align=True)
        quantity_of_teeth = row.prop(mytool, 'quantity_of_teeth', text='Quantity')

        # Trim tool and arch cut
        row = self.layout.row(align=True)
        draw_arch = row.operator('mesh.draw_arch', text='Draw Arch', icon='SEQ_LUMA_WAVEFORM')
        trim_cut = row.operator('mesh.trim_cut', text='Trim Cut', icon='MOD_SIMPLEDEFORM')
        clean = row.operator('mesh.clean', text='Clean', icon='CON_TRANSFORM_CACHE')
        # make base and adjust base height
        row = self.layout.row(align=True)
        make_base = row.operator('mesh.make_base', text='Make Base', icon='MOD_BUILD')
        move_up = row.operator('mesh.move_up', text='', icon='SORT_DESC')
        move_down = row.operator('mesh.move_down', text='', icon='SORT_ASC')
        apply_bas = row.operator('mesh.apply_base', text='', icon='CHECKMARK')
        row = self.layout.row(align=True)
        seperate_teeth = row.operator('mesh.seperate_teeth', text='Seperate Teeth')

        self.layout.separator()
        # smooth tooth edge button
        row = self.layout.row(align=True)
        smooth_tooth_edge = row.operator('mesh.smooth_tooth_edge', text='Smooth Edge', icon='VIS_SEL_01')
        # draw, remove, amend, apply curve
        remove = row.operator('mesh.remove_curve', text='',icon='CANCEL')
        amend = row.operator('mesh.amend_curve', text='', icon='MODIFIER_ON')
        drawLine = row.operator('mesh.draw_line', text='', icon='GREASEPENCIL')
        applyDraw = row.operator('mesh.apply_draw', text='', icon='CHECKMARK')
        # sort curve and exchange name
        row = self.layout.row(align=True)
        sortCurve = row.operator('mesh.sort_curve', text='Sort Curves', icon='SORTSIZE')
        exchangeName = row.operator('mesh.exchange_name', text='Exchange Name', icon='UV_SYNC_SELECT')
        # To sphere curves
        row = self.layout.row(align=True)
        sphereCurves = row.operator('mesh.to_sphere', text='Sphere Curves', icon='ANTIALIASED')
        # adjust curve button
        disssolveVertex = row.operator('mesh.adjust_curve', text='Adjust Curve', icon='IPO_EASE_OUT')
        subdivideVertex = row.operator('mesh.subdivide', text='', icon='ADD')
        dissolveVertex = row.operator('mesh.dissolve_verts', text='', icon='REMOVE')
        applyAdjust = row.operator('mesh.apply_adjust', text='', icon='CHECKMARK')
        # find intersection
        row = self.layout.row(align=True)
        findIntersect = row.operator("mesh.find_interscetion",text='Find Intersection', icon='SELECT_INTERSECT')
        # create knife panel and cut
        row = self.layout.row(align=True)
        knifePanel = row.operator('mesh.knife_panel', text='Knife Panel', icon='MOD_OFFSET')
        cutTeeth = row.operator('mesh.cut_teeth', text='Cut Teeth', icon='SCULPTMODE_HLT')
        # separator bar
        self.layout.separator()
        row = self.layout.row(align=True)
        U_18 = row.prop(mytool, 'U_18', text='18', toggle=1)
        U_17 = row.prop(mytool, 'U_17', text='17', toggle=1)
        U_16 = row.prop(mytool, 'U_16', text='16', toggle=1)
        U_15 = row.prop(mytool, 'U_15', text='15', toggle=1)
        U_14 = row.prop(mytool, 'U_14', text='14', toggle=1)
        U_13 = row.prop(mytool, 'U_13', text='13', toggle=1)
        U_12 = row.prop(mytool, 'U_12', text='12', toggle=1)
        U_11 = row.prop(mytool, 'U_11', text='11', toggle=1)
        U_21 = row.prop(mytool, 'U_21', text='21', toggle=1)
        U_22 = row.prop(mytool, 'U_22', text='22', toggle=1)
        U_23 = row.prop(mytool, 'U_23', text='23', toggle=1)
        U_24 = row.prop(mytool, 'U_24', text='24', toggle=1)
        U_25 = row.prop(mytool, 'U_25', text='25', toggle=1)
        U_26 = row.prop(mytool, 'U_26', text='26', toggle=1)
        U_27 = row.prop(mytool, 'U_27', text='27', toggle=1)
        U_28 = row.prop(mytool, 'U_28', text='28', toggle=1)
        row = self.layout.row(align=True)
        
        D_48 = row.prop(mytool, 'D_48', text='48', toggle=1)
        D_47 = row.prop(mytool, 'D_47', text='47', toggle=1)
        D_46 = row.prop(mytool, 'D_46', text='46', toggle=1)
        D_45 = row.prop(mytool, 'D_45', text='45', toggle=1)
        D_44 = row.prop(mytool, 'D_44', text='44', toggle=1)
        D_43 = row.prop(mytool, 'D_43', text='43', toggle=1)
        D_42 = row.prop(mytool, 'D_42', text='42', toggle=1)
        D_41 = row.prop(mytool, 'D_41', text='41', toggle=1)
        D_31 = row.prop(mytool, 'D_31', text='31', toggle=1)
        D_32 = row.prop(mytool, 'D_32', text='32', toggle=1)
        D_33 = row.prop(mytool, 'D_33', text='33', toggle=1)
        D_34 = row.prop(mytool, 'D_34', text='34', toggle=1)
        D_35 = row.prop(mytool, 'D_35', text='35', toggle=1)
        D_36 = row.prop(mytool, 'D_36', text='36', toggle=1)
        D_37 = row.prop(mytool, 'D_37', text='37', toggle=1)
        D_38 = row.prop(mytool, 'D_38', text='38', toggle=1)
        row = self.layout.row(align=True)
        sort_teeth = row.operator('mesh.sort_teeth', text='Sort Teeth')
        row = self.layout.row(align=True)
        pick_tooth = row.operator('mesh.pick_tooth', text='Pick Tooth')
        picked_tooth = row.prop(mytool, 'picked_tooth_name', text='')
        restore = row.operator('mesh.restore', text='Restore')

        row = self.layout.row(align=True)
        auto_orientation = row.operator('mesh.auto_orientation', text='Auto Orientation')
        apply_auto_orientation = row.operator('mesh.apply_auto_orientation', text='',icon='CHECKMARK')

        # change local Frame orientation buttons
        row = self.layout.row(align=True)
        # draw_annotate = row.operator('mesh.draw_annotate', text='', icon='GREASEPENCIL')
        changeOrientation = row.operator('mesh.change_local_orientation', text='', icon='ORIENTATION_GIMBAL')
        filp_z_orientation = row.operator('mesh.filp_z_orientation', text='', icon='MOD_TRIANGULATE')
        applyOrientation = row.operator('mesh.apply_orientation', text='', icon='CHECKMARK')
        
        self.layout.separator()
        row = self.layout.row(align=True)
        select_three_points = row.operator('mesh.select_three_points', text='Select Points') 
        generate_adjust_arch = row.operator('mesh.generate_adjust_arch', text='Arch')
        automatic_arrange = row.operator('mesh.automatic_arrange', text='Auto Arrange')
        edit_arch = row.operator('mesh.edit_arch', text='', icon='EDITMODE_HLT')
        row = self.layout.row(align=True)
        complement_teeth_bottom = row.operator('mesh.complement_teet_bottom', text='Complement Bottom')
        # intercalation_capacity = row.operator('wm.inter_capacity', text='Intercalation Capacity')
        # draw emboss region curve
        row = self.layout.row(align=True)
        find_curves = row.operator('mesh.find_emboss_curves', text='Find Curves')
        draw_curves = row.operator('mesh.draw_curve', text='Draw')
        apply_draw = row.operator('mesh.apply_curve_generate_panel', text='', icon='CHECKMARK')
        row = self.layout.row(align=True)
        extrude_panel = row.operator('mesh.extrude_panel', text='Extrude')
        if len(context.selected_objects) != 0:
            if context.object.name.startswith('panel') and context.object.select_get() == True:
                if context.object.modifiers.get('Solidify'):
                    pops = context.object.modifiers['Solidify']
                    exturde_thinkness = row.prop(pops, 'thickness', text='')
                if context.object.modifiers.get('Boolean'):
                    pops = context.object.modifiers['Boolean']
                    boolean_operation = row.prop(pops, 'operation', text='')
        show_teeth = row.operator('mesh.show_teeth', text='', icon='HIDE_OFF')
        hide_teeth = row.operator('mesh.hide_teeth', text='', icon='HIDE_ON')
        row = self.layout.row(align=True)
        emboss_image = row.operator('mesh.emboss_image', text='Emboss')
        if len(context.selected_objects) != 0:
            if context.object.name.startswith('panel') and context.object.select_get() == True:
                if context.object.modifiers.get('Displace'):
                    pops = context.object.modifiers['Displace']
                    exturde_thinkness = row.prop(pops, 'strength', text='')
        apply_emboss = row.operator('mesh.apply_emboss', text='', icon='CHECKMARK')
        # row = self.layout.row(align=True)
        # put_on_brackets = row.operator('mesh.put_on_brackets', text='Put On Brackets')
        if (context.mode == 'OBJECT'):
            row = self.layout.row(align=True)
            row.prop(mytool, "UP_tipTorExpand",
                icon="TRIA_DOWN" if mytool.UP_tipTorExpand else "TRIA_RIGHT",
                icon_only=True, emboss=False
            )
            row.label(text='Tip Torque')
            if mytool.UP_tipTorExpand:
                col = self.layout.column(align=True)
                row = col.row(align=True)  
                split = row.split(factor= 0.1, align=True)
                split.label(text="", text_ctxt="", translate=True, icon='NONE', icon_value=0)
                split.label(text="Tip", text_ctxt="Tip Value", translate=True, icon='NONE', icon_value=0)
                split.label(text="Torque", text_ctxt="Torque Value", translate=True, icon='NONE', icon_value=0)
                if mytool.up_down == 'UP_':
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="11", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_11', text='')
                    split.prop(mytool, 'Tor_11', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="12", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_12', text='')
                    split.prop(mytool, 'Tor_12', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="13", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_13', text='')
                    split.prop(mytool, 'Tor_13', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="14", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_14', text='')
                    split.prop(mytool, 'Tor_14', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="15", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_15', text='')
                    split.prop(mytool, 'Tor_15', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="16", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_16', text='')
                    split.prop(mytool, 'Tor_16', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="17", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_17', text='')
                    split.prop(mytool, 'Tor_17', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="18", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_18', text='')
                    split.prop(mytool, 'Tor_18', text='')

                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="21", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_21', text='')
                    split.prop(mytool, 'Tor_21', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="22", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_22', text='')
                    split.prop(mytool, 'Tor_22', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="23", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_23', text='')
                    split.prop(mytool, 'Tor_23', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="24", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_24', text='')
                    split.prop(mytool, 'Tor_24', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="25", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_25', text='')
                    split.prop(mytool, 'Tor_25', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="26", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_26', text='')
                    split.prop(mytool, 'Tor_26', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="27", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_27', text='')
                    split.prop(mytool, 'Tor_27', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="28", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_28', text='')
                    split.prop(mytool, 'Tor_28', text='')
                else:

                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="31", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_31', text='')
                    split.prop(mytool, 'Tor_31', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="32", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_32', text='')
                    split.prop(mytool, 'Tor_32', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="33", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_33', text='')
                    split.prop(mytool, 'Tor_33', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="34", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_34', text='')
                    split.prop(mytool, 'Tor_34', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="35", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_35', text='')
                    split.prop(mytool, 'Tor_35', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="36", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_36', text='')
                    split.prop(mytool, 'Tor_36', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="37", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_37', text='')
                    split.prop(mytool, 'Tor_37', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="38", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_38', text='')
                    split.prop(mytool, 'Tor_38', text='')

                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="41", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_41', text='')
                    split.prop(mytool, 'Tor_41', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="42", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_42', text='')
                    split.prop(mytool, 'Tor_42', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="43", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_43', text='')
                    split.prop(mytool, 'Tor_43', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="44", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_44', text='')
                    split.prop(mytool, 'Tor_44', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="45", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_45', text='')
                    split.prop(mytool, 'Tor_45', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="46", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_46', text='')
                    split.prop(mytool, 'Tor_46', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="47", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_47', text='')
                    split.prop(mytool, 'Tor_47', text='')
                    row = col.row(align=True)
                    split = row.split(factor= 0.1, align=True)
                    split.label(text="48", text_ctxt="", translate=False, icon='NONE', icon_value=0)
                    split.prop(mytool, 'Tip_48', text='')
                    split.prop(mytool, 'Tor_48', text='')

    
def exec_read_global_peremeter(commend,key):
    _locals = locals()
    exec(commend,globals(),_locals)
    if key in _locals:
        return _locals[key]
    return commend
 
#DSC sort
def compare(A, B):
    numA=int(re.split("[_.]",A)[1])
    numB=int(re.split("[_.]",B)[1])
    if numA>numB:
        return -1
    elif numA<numB:
        return 1
    return 0 

max_autosave=20

class SCENE_AUTO_save_blend(bpy.types.Operator):
    bl_idname = "scene.saveblend"
    bl_label = "automaticly save blend"
    filename:bpy.props.StringProperty(
        name='id',
        description='',
        default="autosave"
    )
    def execute(self, context):
        if False:
            return {'FINISHED'}
        #the number of autosave blend file must small than max_autosave
        oldist_filepath = autosave_blendpath + os.sep +self.filename+'_'+str(max_autosave)+'.blend'
        if os.path.exists(oldist_filepath):
            os.remove(oldist_filepath)

        allfileList=os.listdir(autosave_blendpath)
        fileList=[]
        for name in allfileList:
            strlist=re.split("[_.]",name)
            if len(strlist)==3 and strlist[0]==self.filename and strlist[2]=='blend':
                fileList.append(name) 
        fileList.sort(key=functools.cmp_to_key(compare))
        print(fileList)

        n=0
        for name in fileList:
            strlist=re.split("[_.]",name)
            oldname=autosave_blendpath+ os.sep + fileList[n] 
            num=int(re.split("[_.]",name)[1])
            newname=autosave_blendpath + os.sep +self.filename+'_'+str(num+1)+'.blend'
            os.rename(oldname,newname)  
            print(oldname,'======>',newname)
            n+=1

        bpy.ops.wm.save_as_mainfile(filepath=autosave_blendpath + os.sep+self.filename+"_1.blend")
        return {'FINISHED'}

class SCENE_AUTO_open_blend(bpy.types.Operator):
    bl_idname = "scene.openblend"
    bl_label = "open blend"
    
    orderNum:bpy.props.IntProperty(
        name='id',
        description='',
        default=1
    )
    filename:bpy.props.StringProperty(
        name='id',
        description='',
        default="autosave"
    )
    def execute(self, context):
        #the number of autosave blend file must small than max_autosave
        open_filepath = autosave_blendpath + os.sep +self.filename+"_"+str(self.orderNum)+'.blend'
        if os.path.exists(open_filepath):
            bpy.ops.wm.open_mainfile(filepath=open_filepath)
            return {'FINISHED'}
        message = "there is no blend  "+open_filepath+"!"
        self.report({'ERROR'}, message)
        return {'CANCELLED'}  

class BlendFileProperties(bpy.types.PropertyGroup):
    dialog_name : bpy.props.EnumProperty(
        name="Dialog Name",
        description="select the differet version of different  dialog",
        items=[
            ('preSeperation', 'preSeperation', 'prepore for tooth Seperation'),
            ('seperation', 'seperation tooth', 'seperation tooth'),
            ('cuttooth', 'cut tooth', 'seperation tooth'),
        ]
    )
    version_number:bpy.props.EnumProperty(
        name="version number",
        description="the smaller number is laster version",
        items=[
            ('1', '1', 'lastist version'),
            ('2', '2', ''),
            ('3', '3', ''),
            ('4', '4', ''),
            ('5', '5', ''),
            ('6', '6', ''),
            ('7', '7', ''),
            ('8', '8', ''),
            ('9', '9', ''),
            ('10', '10', ''),
            ('11', '11', ''),
            ('12', '12', ''),
            ('13', '13', ''),
            ('14', '14', ''),
            ('15', '15', ''),
            ('16', '16', ''),
            ('17', '17', ''),
            ('18', '18', ''),
            ('19', '19', ''),
            ('10', '10', '')
            ]
    )  
    panel_Tooth_11 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_13 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_12 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_14 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_15 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_16 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_17 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_18 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_21 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_22 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_23 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_24 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_25 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_26 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_27 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_28 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_31 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_32 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_33 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_34 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_35 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_36 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_37 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_38 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_41 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_42 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_43 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_44 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_45 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_46 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_47 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    panel_Tooth_48 : bpy.props.FloatVectorProperty(default=(0.0, 0.0, 0.0))
    
class VIEW3D_PT_reload_blend(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'ReloadBlend'
    bl_label = 'ReloadBlend'

    def draw(self, context):
        scene = context.scene
        reloadBlend = scene.reloadBlend

        #selcet version name
        row = self.layout.row(align=True)
        version_number = row.prop(reloadBlend,"version_number")
        
        # selcet dialog name
        row = self.layout.row(align=True)
        openblend = row.operator('scene.openblend', text='preSeperation', icon='FILE')
        openblend.orderNum=int(reloadBlend.version_number)
        openblend.filename='preSeperation'

        row = self.layout.row(align=True)
        openblend = row.operator('scene.openblend', text='seperation', icon='FILE')
        openblend.orderNum=int(reloadBlend.version_number)
        openblend.filename='seperation'

        row = self.layout.row(align=True)
        openblend = row.operator('scene.openblend', text='cuttooth', icon='FILE')
        openblend.orderNum=int(reloadBlend.version_number)
        openblend.filename='cuttooth'

classes = [MESH_TO_smooth_tooth_edge, 
    VIEW3D_PT_smooth_tooth_edge,
    MESH_TO_change_local_orientation,
    MESH_TO_apply_orientation,
    MESH_TO_adjust_curve,
    MESH_TO_apply_adjust,
    MESH_TO_draw_line,
    MESH_TO_knife_panel,
    MESH_TO_cut_teeth,
    MESH_TO_exchange_name,
    MESH_TO_apply_draw,
    MESH_TO_draw_annotate,
    MESH_TO_generate_coordinate,
    MESH_TO_filp_z_orientation,
    MESH_TO_sort_curve,
    MESH_TO_to_sphere_curve,
    MESH_TO_finde_intersect,
    MESH_TO_make_base,
    MESH_TO_apply_base,
    MESH_TO_base_move_up,
    MESH_TO_base_move_donw,
    MESH_TO_draw_arch,
    MESH_TO_trim_cut,
    MESH_TO_clean,
    MESH_TO_draw_region_curve,
    MESH_TO_apply_curve,
    MESH_TO_exturde_emboss_panel,
    MESH_TO_resize_emboss_panel,
    MESH_TO_remove_curve,
    MESH_TO_amend_curve,
    MESH_TO_smooth_panel_edge,
    MESH_TO_emboss_image,
    MESH_TO_apply_emboss,
    MESH_TO_find_emboss_curves,
    MESH_TO_show_teeth,
    MESH_TO_hide_teeth,
    MyProperties,
    SCENE_AUTO_save_blend,
    SCENE_AUTO_open_blend,
    BlendFileProperties,
    VIEW3D_PT_reload_blend,
    MESH_TO_ready_seperate_teeth,
    MESH_TO_seperate_Teeth,
    MESH_TO_sort_teeth,
    MESH_TO_pick_tooth,
    MESH_TO_restore,
    MESH_TO_complement_tooth_bottom,
    MESH_TO_put_on_brackets,
    MESH_TO_automatic_arrange_teeth,
    MESH_TO_generate_adjust_arch,
    MESH_TO_automatic_orientation,
    MESH_TO_apply_auto_orientation,
    WM_OT_inter_capacity,
    MESH_TO_auto_tip,
    MESH_TO_test,
    MESH_TO_edit_arch,
    MESH_TO_select_three_points,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=MyProperties)
    bpy.types.Scene.reloadBlend = bpy.props.PointerProperty(type=BlendFileProperties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.my_tool
    del bpy.types.Scene.reloadBlend

if __name__ == '__main__':
    register()
    
