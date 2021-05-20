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
from typing import Text
import bpy
import mathutils
import math
import numpy as np
import sys
from bpy_extras import object_utils
import functools
import re
import os
import json
import getpass

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

def  exec_read_global_peremeter(commend,key):
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
    """Calculate distance bewteen two points """
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

def generate_emboss_panel(self, context):
    if len(context.selected_objects) == 1 and context.object.name.endswith('curve'):
        scene = context.scene
        mytool = scene.my_tool
        tooth_name = mytool.tooth_name
        tooth_object = bpy.data.objects[tooth_name]
        

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
            return {'CANCELLED'}
        bpy.ops.mesh.duplicate(mode=1)
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        panel_name = tooth_name + '.001'
        panel_object = bpy.data.objects[panel_name]
        panel_object.data.name =  tooth_name + 'panel'
        panel_object.name = tooth_name + 'panel'

        return panel_object

def conver_gpencil_to_curve(self, context, pencil, type):
    newCurve = bpy.data.curves.new(type + 'line', type='CURVE')
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

class MyProperties(bpy.types.PropertyGroup):
    selected_object_name : bpy.props.StringProperty(name="")
    y_direction : bpy.props.FloatVectorProperty(name="Y axis direction of tooth in local coordinate", subtype='XYZ', precision=2, size=3, default=(0.0, 0.0,0.0))
    z_direction : bpy.props.FloatVectorProperty(name="Z axis direction of tooth in local coordinate", subtype='XYZ', precision=2, size=3, default=(0.0, 0.0,0.0))
    up_teeth_object_name : bpy.props.StringProperty(name="")
    down_teeth_object_name : bpy.props.StringProperty(name="")
    trim_cut_object_name : bpy.props.StringProperty(name="")
    tooth_name : bpy.props.StringProperty(name="")
    U_curve_collection_name : bpy.props.StringProperty(name="")
    D_curve_collection_name : bpy.props.StringProperty(name="")

    up_down : bpy.props.EnumProperty(
        name="UP/DOWN",
        description="Choose up or down side of teeth",
        items=[
            ('UP_', 'UP', 'It is UP side'),
            ('DOWN_', 'DOWN', 'It is DOWN side'),
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

    press_extrude_button : bpy.props.BoolProperty(name="extrude_press")
    
    factor : bpy.props.FloatProperty(name="extrude_factor", 
                description="The Factor control resize scale", 
                default=1.0, 
                min=1.0, max=1.3, 
                soft_min=1.0, soft_max=1.3, 
                step=0.01)

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
                mytool.U_curve_collection_name = 'Curves_U'
            else:
                if not bpy.data.collections.get('Curves_D'):
                    curves_coll = bpy.data.collections.new('Curves_D')
                    context.scene.collection.children.link(curves_coll)
                curves_collection = bpy.data.collections['Curves_D']
                mytool.D_curve_collection_name = 'Curves_D'

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
                curve_collection = bpy.data.collections[mytool.U_curve_collection_name]
                prefix = 'Curve_U_'
                mian_obj = bpy.context.object
                bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children['Curves_U']

            elif bpy.context.object.name == mytool.down_teeth_object_name:
                curve_collection = bpy.data.collections[mytool.D_curve_collection_name]
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
                angle = math.atan((-location[0])/location[1])

                if location[1] == 0 and location[0] < 0 :
                    angle = math.pi / 2
                elif location[1] == 0 and location[0] > 0:
                    angle = math.pi + math.pi / 2
                elif location[0] > 0 and location[1] > 0:
                    angle = angle + 2 * math.pi
                elif location[0] > 0 and location[1] < 0:
                    angle = angle + math.pi
                elif location[0] < 0 and location[1] < 0:
                    angle = angle + math.pi
                # print(obj.name,angle/math.pi*180)
                z_co_index[index] =  angle                      # store object index in collection                    
                obj.select_set(False)
        sort_list = sorted(z_co_index.items(), key=lambda item:item[1])
        print(sort_list)
        context.view_layer.objects.active = main_object

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
            self.report({'INFO'}, message)

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

            context.object.name = tooth_object.name + 'coordinate'

            M.row[0][3] = tooth_object.matrix_local.row[0][3]
            M.row[1][3] = tooth_object.matrix_local.row[1][3]
            M.row[2][3] = tooth_object.matrix_local.row[2][3]
            context.object.matrix_local = M
            bpy.context.scene.transform_orientation_slots[1].type = 'LOCAL'
            bpy.context.space_data.show_gizmo_object_rotate = True
            bpy.context.space_data.show_gizmo_object_translate = True

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

        if len(context.selected_objects) == 1 and context.selected_objects[0].name.endswith('coordinate'):
            matrix_local = context.object.matrix_local.copy()
            M = matrix_local.to_3x3()
            print(M)
            M.invert()
            print(M)
            a = (M.row[0][0], M.row[0][1], M.row[0][2])
            b = (M.row[1][0], M.row[1][1], M.row[1][2])
            c = (M.row[2][0], M.row[2][1], M.row[2][2])
            print(a)
            print(b)
            print(c)
            bpy.ops.transform.rotate(value=3.14159, orient_axis='Y', orient_type='LOCAL', orient_matrix=(a, b, c), orient_matrix_type='LOCAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

            
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

        if len(context.selected_objects) == 1:
            coord_name = context.object.name + 'coordinate'
            context.collection.objects[coord_name].hide_set(False)
            bpy.ops.object.select_all(action='DESELECT')
            context.view_layer.objects.active = context.collection.objects[coord_name]
            context.collection.objects[coord_name].select_set(True)

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

        if len(context.selected_objects) and context.object.name.endswith('coordinate'):
            tooth_name = context.object.name.rstrip('coordinate')
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
            newName = coord_name.rstrip('coordinate')

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

class MESH_TO_find_emboss_curves(bpy.types.Operator):
    """"Find Emboss Curves"""
    bl_idname = "mesh.find_emboss_curves"
    bl_label = "Find Curves"
    
    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        for obj in context.collection.objects:
            context.view_layer.objects.active = obj
            obj.select_set(True)
            origin = mathutils.Vector((0, 0, 0))
            direction_x = mathutils.Vector((1, 0, 0))
            dis = 10
            result = obj.ray_cast(origin, direction_x, distance=dis, depsgraph=None)
            context.object.data.polygons[result[3]].select = True
            bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)
        for i in range(8):
            bpy.ops.mesh.select_more()
        bpy.ops.mesh.region_to_loop()
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        for obj in context.collection.objects:
            if obj.name.endswith('.001'):
                tooth_name = obj.name.rstrip('.001')
                tooth_object = context.collection.objects[tooth_name]
                context.view_layer.objects.active = obj
                obj.select_set(True)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.context.tool_settings.mesh_select_mode = (True, False, False)
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.dissolve_degenerate(threshold=0.1)
                bpy.ops.mesh.unsubdivide()
                bpy.ops.object.mode_set(mode='OBJECT')

                bpy.ops.object.modifier_add(type='SUBSURF')
                bpy.context.object.modifiers["Subdivision"].levels = 2
                bpy.context.object.modifiers["Subdivision"].show_on_cage = True

                bpy.ops.object.modifier_add(type='SHRINKWRAP')
                bpy.context.object.modifiers["Shrinkwrap"].target = tooth_object
                bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'NEAREST_SURFACEPOINT'
                bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'OUTSIDE_SURFACE'
                bpy.context.object.modifiers["Shrinkwrap"].offset = 0.1
                bpy.context.object.modifiers["Shrinkwrap"].show_on_cage = True

                bpy.ops.object.modifier_add(type='SMOOTH')
                bpy.context.object.modifiers["Smooth"].iterations = 10 
                bpy.context.object.modifiers["Smooth"].show_in_editmode = True
                bpy.context.object.modifiers["Smooth"].show_on_cage = True
                bpy.context.object.modifiers["Smooth"].factor = 0.5

                obj.data.name = tooth_name + '_panel'
                obj.name = tooth_name + '_panel'
                obj.select_set(False)

        for obj in context.collection.objects:
            if obj.name.endswith('_panel'):
                context.view_layer.objects.active = obj
                obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.context.scene.tool_settings.use_snap = True
        bpy.context.space_data.show_gizmo_object_translate = False

        return {'FINISHED'}

class MESH_TO_draw_region_curve(bpy.types.Operator):
    """" Draw Curves To Define Emboss Region"""
    bl_idname = "mesh.draw_curve"
    bl_label = "Draw Curve"
    
    def execute(self, context):
        if len(context.selected_objects) == 1:
            scene = context.scene
            mytool = scene.my_tool

            tooth_object = bpy.context.object
            bpy.ops.object.material_slot_remove()

            mytool.tooth_name = tooth_object.name
            bpy.context.scene.tool_settings.use_snap = True

            bpy.context.space_data.show_gizmo_object_translate = False
            bpy.context.space_data.overlay.show_floor = False
            bpy.context.tool_settings.mesh_select_mode = (True, False, False)

            bpy.ops.mesh.primitive_vert_add()

            bpy.context.object.name = tooth_object.name + '_emboss_curve'
            bpy.context.object.data.name = tooth_object.name + '_emboss_curve'

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
            bpy.context.object.modifiers["Shrinkwrap"].offset = 0.1
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
            bpy.ops.ed.undo_push()
        return {'FINISHED'}

class MESH_TO_apply_curve(bpy.types.Operator):
    """"Apply curve and find emboss region"""
    bl_idname = "mesh.apply_curve"
    bl_label = "Apply Curve"
    
    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            context.scene.cursor.location = mathutils.Vector((0.0,0.0,0.0))
            context.scene.cursor.rotation_euler = mathutils.Vector((0,0,0))

            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
            curve_object = bpy.context.object
            bpy.ops.ed.undo_push()
            
        return {'FINISHED'}

class MESH_TO_exturde_emboss_panel(bpy.types.Operator):
    """"Extrude An Emboss Panel"""
    bl_idname = "mesh.extrude_panel"
    bl_label = "Extrude panel"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        
        mytool.press_extrude_button = True
        panel_object = generate_emboss_panel(self, context)
        context.view_layer.objects.active = panel_object
        panel_object.select_set(True)
        # thicken panel
        if len(context.selected_objects) == 1 and context.object.name.endswith('panel'):
            panel_object = context.object
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')

            bpy.context.tool_settings.mesh_select_mode = (False, True, False)
            bpy.ops.mesh.select_non_manifold()
            bpy.ops.mesh.looptools_relax(input='selected', interpolation='cubic', iterations='25', regular=True)
            bpy.ops.object.vertex_group_remove(all=True, all_unlocked=False)
            bpy.ops.mesh.duplicate(mode=1)
            bpy.ops.mesh.separate(type='SELECTED')

            panel_object_copy_name = bpy.context.object.name + '.001'
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            panel_object.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')

            bpy.ops.mesh.select_all(action='SELECT')
            bpy.context.scene.transform_orientation_slots[0].type = 'NORMAL'
            bpy.context.scene.transform_orientation_slots[1].type = 'NORMAL'
            bpy.context.space_data.show_gizmo_object_translate = True
            bpy.context.scene.tool_settings.use_snap = False
            bpy.ops.transform.create_orientation(name="normal", use=True)
            normal_orientation_matirx = bpy.context.scene.transform_orientation_slots[0].custom_orientation.matrix.copy()
            normal_orientation_matirx.invert()
            # print(normal_orientation_matirx)
            a = (normal_orientation_matirx.row[0][0], normal_orientation_matirx.row[0][1], normal_orientation_matirx.row[0][2])
            b = (normal_orientation_matirx.row[1][0], normal_orientation_matirx.row[1][1], normal_orientation_matirx.row[1][2])
            c = (normal_orientation_matirx.row[2][0], normal_orientation_matirx.row[2][1], normal_orientation_matirx.row[2][2])
            bpy.ops.transform.delete_orientation()
            bpy.context.scene.transform_orientation_slots[0].type = 'NORMAL'

            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, 0.45), "orient_type":'NORMAL', "orient_matrix":(a, b, c), "orient_matrix_type":'NORMAL', "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
            bpy.ops.object.vertex_group_add()
            panel_object.vertex_groups['Group'].name = 'extrude_panel'
            bpy.ops.object.vertex_group_assign()
            

            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.context.tool_settings.mesh_select_mode = (False, True, False)
            bpy.ops.wm.tool_set_by_id(name="builtin.loop_cut")

        bpy.ops.ed.undo_push()
        info = ('OK')
        self.report({'INFO'}, info)

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
            bpy.ops.ed.undo_push()
            
        return {'FINISHED'}

class MESH_TO_emboss_image(bpy.types.Operator):
    """Emboss Image"""
    bl_idname = "mesh.emboss_image"
    bl_label = "emboss_image"
    
    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool

        if len(context.selected_objects) == 1:
            if context.object.name.endswith('panel'):
                panel_object = context.object
                if len(panel_object.vertex_groups) != 0:
                    bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
                bpy.context.scene.transform_orientation_slots[0].type = 'LOCAL'
                bpy.ops.transform.create_orientation(name="panel_local", use=True)
                normal_orientation_matirx = bpy.context.scene.transform_orientation_slots[0].custom_orientation.matrix.copy()
                normal_orientation_matirx.invert()
                print(normal_orientation_matirx)
                a = (normal_orientation_matirx.row[0][0], normal_orientation_matirx.row[0][1], normal_orientation_matirx.row[0][2])
                b = (normal_orientation_matirx.row[1][0], normal_orientation_matirx.row[1][1], normal_orientation_matirx.row[1][2])
                c = (normal_orientation_matirx.row[2][0], normal_orientation_matirx.row[2][1], normal_orientation_matirx.row[2][2])
                # print(normal_orientation_matirx)
                bpy.ops.transform.delete_orientation()
                bpy.context.scene.transform_orientation_slots[0].type = 'LOCAL'
                bpy.context.scene.tool_settings.use_transform_data_origin = True
                bpy.ops.transform.rotate(value=1.5708, orient_axis='Y', orient_type='LOCAL', orient_matrix=(a, b, c), orient_matrix_type='LOCAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
                bpy.context.scene.tool_settings.use_transform_data_origin = False

                curve_name = context.object.name + '.001'
                bpy.ops.object.select_all(action='DESELECT')
                curve_object = bpy.data.objects[curve_name]
                context.view_layer.objects.active = curve_object
                curve_object.select_set(True)
                bpy.ops.object.modifier_add(type='SHRINKWRAP')
                bpy.context.object.modifiers["Shrinkwrap"].target = panel_object
                bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'NEAREST_SURFACEPOINT'
                bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'ON_SURFACE'
                bpy.context.object.modifiers["Shrinkwrap"].offset = -0.22

                bpy.ops.object.modifier_add(type='SMOOTH')
                bpy.context.object.modifiers["Smooth"].iterations = 10 
                bpy.context.object.modifiers["Smooth"].factor = 0.5
                bpy.ops.object.convert(target='MESH')
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.context.tool_settings.mesh_select_mode = (True, False, False)
                bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='linear', lock_x=False, lock_y=False, lock_z=False)
                bpy.ops.transform.resize(value=(0.98, 0.98, 0.98), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
                bpy.context.scene.transform_orientation_slots[0].type = 'NORMAL'
                bpy.ops.transform.create_orientation(name="normal", use=True)
                normal_orientation_matirx = bpy.context.scene.transform_orientation_slots[0].custom_orientation.matrix.copy()
                normal_orientation_matirx.invert()
                # print(normal_orientation_matirx)
                a = (normal_orientation_matirx.row[0][0], normal_orientation_matirx.row[0][1], normal_orientation_matirx.row[0][2])
                b = (normal_orientation_matirx.row[1][0], normal_orientation_matirx.row[1][1], normal_orientation_matirx.row[1][2])
                c = (normal_orientation_matirx.row[2][0], normal_orientation_matirx.row[2][1], normal_orientation_matirx.row[2][2])
                bpy.ops.transform.delete_orientation()
                bpy.context.scene.transform_orientation_slots[0].type = 'LOCAL'
                bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, -2.0), "orient_type":'NORMAL', "orient_matrix":(a, b, c), "orient_matrix_type":'NORMAL', "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False})
                bpy.ops.transform.resize(value=(0.713, 0.713, 0.713), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
                bpy.ops.transform.shrink_fatten(value=0.046, use_even_offset=False, mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
                bpy.ops.mesh.select_all(action='SELECT')
                
                bpy.ops.object.vertex_group_add()
                curve_object.vertex_groups['Group'].name = 'a'
                bpy.ops.object.vertex_group_assign()
                bpy.ops.object.mode_set(mode='OBJECT')
                context.view_layer.objects.active = panel_object
                panel_object.select_set(True)
                bpy.ops.object.join()
                bpy.ops.object.mode_set(mode='EDIT')
                
                bpy.context.tool_settings.mesh_select_mode = (False, True, False)
                bpy.ops.mesh.intersect()
                bpy.ops.object.vertex_group_assign()
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.vertex_group_select()
                bpy.ops.mesh.separate(type='SELECTED')
                bpy.ops.object.vertex_group_select()
                if bpy.context.object.data.total_edge_sel > 100:
                    bpy.ops.mesh.loop_to_region()
                    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
                    bpy.ops.mesh.subdivide()
                    bpy.ops.mesh.subdivide()
                    bpy.ops.object.vertex_group_assign()
                else:
                    error_message = 'Nothing Is Selecting! Please Check'
                    self.report({'ERROR'}, error_message)
                    return {'CANCELED'}

                bpy.ops.object.mode_set(mode='OBJECT')
                bpy.ops.object.select_all(action='DESELECT')    

                panel_object = context.object
                temp_name = context.object.name + '.001'
                context.view_layer.objects.active = context.collection.objects[temp_name]
                context.collection.objects[temp_name].select_set(True)
                bpy.ops.object.delete(use_global=False, confirm=True)

                context.view_layer.objects.active = panel_object
                panel_object.select_set(True)

                loca = panel_object.location
                context.scene.cursor.location = loca
                
                panel_object.modifiers.new(name='Displace', type='DISPLACE')
                panel_object.modifiers['Displace'].mid_level = 0
                panel_object.modifiers['Displace'].strength = 0.2
                panel_object.modifiers['Displace'].vertex_group = 'a'
                panel_object.modifiers['Displace'].direction = 'Z'
                panel_object.modifiers["Displace"].texture_coords = 'LOCAL'
                panel_object.modifiers["Displace"].space = 'LOCAL'

                bpy.ops.image.open(filepath="Grid_Pic\\23-1.jpg", 
                    directory="C:\\Users\\Huafei\Desktop\\BezierCurve\\Grid_Pic", 
                    files=[{"name":"23-1.jpg", "name":"23-1.jpg"}], 
                    relative_path=True, 
                    show_multiview=False)
                img = bpy.data.images['23-1.jpg']
                
                if not bpy.data.textures :
                    bpy.ops.texture.new()           
                    bpy.data.textures['Texture'].image = img
                    bpy.data.textures['Texture'].repeat_x = 2
                    bpy.data.textures['Texture'].repeat_y = 1
                    bpy.data.textures['Texture'].crop_min_x = 0.50
                    bpy.data.textures['Texture'].crop_min_y = 0.50
                    bpy.data.textures['Texture'].crop_max_x = 0.82
                    bpy.data.textures['Texture'].crop_max_y = 0.82
                    bpy.data.textures['Texture'].use_flip_axis = True
                    bpy.data.textures["Texture"].factor_red = 1.5
                    bpy.data.textures["Texture"].factor_green = 1.5
                    bpy.data.textures["Texture"].factor_blue = 1.5

                texture = bpy.data.textures['Texture']
                panel_object.modifiers['Displace'].texture = texture    

                bpy.context.scene.tool_settings.use_transform_data_origin = True
                bpy.context.scene.transform_orientation_slots[1].type = 'LOCAL'
                bpy.context.space_data.show_gizmo_object_rotate = True
                bpy.context.space_data.show_gizmo_object_translate = True

        return {'FINISHED'}

class MESH_TO_apply_emboss(bpy.types.Operator):
    """Apply Emboss"""
    bl_idname = "mesh.apply_emboss"
    bl_label = "Apply Emboss"
    
    def execute(self, context):
        if len(context.selected_objects) == 1 and context.object.name.endswith('panel'):
            context.space_data.show_gizmo_object_translate = False
            context.space_data.show_gizmo_object_rotate = False
            context.scene.tool_settings.use_transform_data_origin = False
            if context.object.modifiers[0].name == 'Displace':
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Displace")

            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
            if len(bpy.context.object.vertex_groups) != 0:
                bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)
            
            context.object.modifiers.new(name='Smooth', type='SMOOTH')
            context.object.modifiers["Smooth"].iterations = 5
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Smooth")

            context.object.modifiers.new(name='Decimate', type='DECIMATE')
            bpy.context.object.modifiers["Decimate"].ratio = 0.5
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Decimate")

            context.object.modifiers.new(name='Decimate', type='DECIMATE')
            bpy.context.object.modifiers["Decimate"].ratio = 0.5
            bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Decimate")

            bpy.ops.object.shade_smooth()

            # Get material
            mat = bpy.data.materials.get("Emboss Color")
            if mat is None:
                # create material
                mat = bpy.data.materials.new(name="Emboss Color")
                mat.diffuse_color =  (0.604, 0.33, 0.906, 1)
                mat.metallic = 0.077
                mat.roughness = 0.234
            bpy.context.object.data.materials.append(mat)
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
        up_donw = row.prop(mytool,"up_down")
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
        # change local Frame orientation buttons
        row = self.layout.row(align=True)
        draw_annotate = row.operator('mesh.draw_annotate', text='', icon='GREASEPENCIL')
        generate_coordinate = row.operator('mesh.generate_coordinate', text='', icon='OUTLINER_OB_EMPTY')
        filp_z_orientation = row.operator('mesh.filp_z_orientation', text='', icon='MOD_TRIANGULATE')
        changeOrientation = row.operator('mesh.change_local_orientation', text='', icon='ORIENTATION_GIMBAL')
        applyOrientation = row.operator('mesh.apply_orientation', text='', icon='CHECKMARK')
        # separator bar
        self.layout.separator()

        # draw emboss region curve
        row = self.layout.row(align=True)
        find_curves = row.operator('mesh.find_emboss_curves', text='Find Curves')
        draw_curves = row.operator('mesh.draw_curve', text='Draw')
        apply_draw = row.operator('mesh.apply_curve', text='', icon='CHECKMARK')
        extrude_panel = row.operator('mesh.extrude_panel', text='Extrude')
        adjust_panel = row.operator('mesh.resize_panel', text='', icon='LIGHT_AREA')
        factor = str(round(mytool.factor, 2)) 
        row.label(text=factor)

        row = self.layout.row(align=True)
        smooth_edge = row.operator('mesh.smooth_panel_edge', text='Smooth Edge')
        emboss_image = row.operator('mesh.emboss_image', text='Emboss')
        apply_emboss = row.operator('mesh.apply_emboss', text='', icon='CHECKMARK')

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
    MyProperties,
    SCENE_AUTO_save_blend,
    SCENE_AUTO_open_blend,
    BlendFileProperties,
    VIEW3D_PT_reload_blend
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