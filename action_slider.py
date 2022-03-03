
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Action Slider Create Tool",
    "author" : "Kumopult <kumopult@qq.com>",
    "description" : "将骨骼动作或姿态记录为“驱动关键帧”, 并自动创建控制滑块",
    "blender" : (2, 93, 0),
    "version" : (0, 0, 3),
    "location" : "View 3D > Toolshelf",
    "warning" : "因为作者很懒所以没写英文教学!",
    "category" : "Animation",
    "doc_url": "https://github.com/kumopult/blender_ActionSlider",
    "tracker_url": "https://space.bilibili.com/1628026",
    # VScode调试：Ctrl + Shift + P
}

import bpy
from mathutils import *

def get_collection():

    def new_collection():
        col = bpy.data.collections.new('ControllerShape')
        col.hide_viewport = True
        bpy.context.scene.collection.children.link(col)
        return col

    return bpy.data.collections.get('ControllerShape') or new_collection()

def get_handle():

    def new_handle():
        mesh_handle = bpy.data.meshes.new('C_Handle')
        mesh_handle.from_pydata(
            [( 0.1,    0, 0), (   0,  0.1, 0), (-0.1,    0, 0), (   0, -0.1, 0)], 
            [(0, 1), (1, 2), (2, 3), (3, 0)], 
            []
        )
        handle = bpy.data.objects.new('C_Handle', mesh_handle)
        mesh_handle.update()
        get_collection().objects.link(handle)
        return handle
        
    return bpy.data.objects.get('C_Handle') or new_handle()

def get_slider():

    def new_slider():
        mesh_slider = bpy.data.meshes.new('C_Slider')
        mesh_slider.from_pydata(
            [(-0.1,  0.1, 0), (-0.1, -0.1, 0), ( 1.1, -0.1, 0), ( 1.1,  0.1, 0)], 
            [(0, 1), (1, 2), (2, 3), (3, 0)], 
            []
        )
        slider = bpy.data.objects.new('C_Slider', mesh_slider)
        mesh_slider.update()
        get_collection().objects.link(slider)
        return slider
        
    return bpy.data.objects.get('C_Slider') or new_slider()

def get_text_slider(name):
    
    def new_text(str):
        curve_text = bpy.data.curves.new(name=str, type='FONT')
        curve_text.body = str
        curve_text.fill_mode = 'NONE'
        curve_text.size = 0.2
        curve_text.text_boxes[0].x = -0.1
        curve_text.text_boxes[0].y = 0.1
        curve_text.align_x = 'LEFT'
        curve_text.align_y = 'BOTTOM'
        text = bpy.data.objects.new('C_Slider_' + str, curve_text)
        get_collection().objects.link(text)
        return text
    
    def new_text_slider(name):
        arm = bpy.context.object
        text = new_text(name)
        slider = get_slider()

        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        get_collection().hide_viewport = False
        bpy.context.view_layer.objects.active = text
        text.select = True
        slider.select = True
        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.join()
        text.select = True
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='POSE', toggle=False)
        get_collection().hide_viewport = True
        return text

    return bpy.data.objects.get('C_Slider_' + name) or new_text_slider(name)

def record_pose():
    if bpy.context.object.animation_data == None:
        # 如果当前骨架上没有动作，则用脚本插帧生成动作
        for bone in bpy.context.selected_pose_bones:
            bone.keyframe_insert(data_path='location', frame=(11))
            bone.keyframe_insert(data_path='scale', frame=(11))
            bone.keyframe_insert(data_path='rotation_euler', frame=(11))
            bone.keyframe_insert(data_path='rotation_quaternion', frame=(11))

            bone.location = Vector((0.0, 0.0, 0.0))
            bone.scale = Vector((1.0, 1.0, 1.0))
            bone.rotation_quaternion = Quaternion((1.0, 0.0, 0.0, 0.0))
            bone.rotation_euler = Euler((0.0, 0.0, 0.0))

            bone.keyframe_insert(data_path='location', frame=(1))
            bone.keyframe_insert(data_path='scale', frame=(1))
            bone.keyframe_insert(data_path='rotation_euler', frame=(1))
            bone.keyframe_insert(data_path='rotation_quaternion', frame=(1))

        for fcurves in bpy.context.object.animation_data.action.fcurves:
            fcurves.extrapolation = 'LINEAR'

            for kp in fcurves.keyframe_points:
                kp.handle_left_type = 'VECTOR'
                kp.handle_right_type = 'VECTOR'
    
    action = bpy.context.object.animation_data.action
    bpy.context.active_object.animation_data_clear()
    return action

def create_controller(name, layers, group):
    arm = bpy.context.object

    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    edit_slider = arm.data.edit_bones.new('action_slider_' + name)
    edit_slider.length = 0.1
    edit_slider.layers = layers
    edit_slider.use_deform = False

    edit_handle = arm.data.edit_bones.new('action_handle_' + name)
    edit_handle.length = 0.1
    edit_handle.layers = layers
    edit_handle.use_deform = False
    edit_handle.parent = edit_slider
    
    bpy.ops.object.mode_set(mode='POSE', toggle=False)
    pose_slider = arm.pose.bones.get('action_slider_' + name)
    pose_slider.bone_group = arm.pose.bone_groups.get(group)
    pose_slider.custom_shape = get_text_slider(name)
    pose_slider.use_custom_shape_bone_size = False
    pose_handle = arm.pose.bones.get('action_handle_' + name)
    pose_handle.bone_group = arm.pose.bone_groups.get(group)
    pose_handle.custom_shape = get_handle()
    pose_handle.use_custom_shape_bone_size = False

    con = pose_handle.constraints.new(type='LIMIT_LOCATION')
    con.use_min_x = True
    con.use_min_y = True
    con.use_min_z = True
    con.use_max_x = True
    con.use_max_y = True
    con.use_max_z = True
    con.max_x = 1
    con.use_transform_limit = True
    con.owner_space = 'LOCAL'

    for i in range(32):
        arm.data.layers[i] = arm.data.layers[i] or layers[i]
    

def add_constraints(action):
    for bone in bpy.context.selected_pose_bones:
        con = bone.constraints.new(type='ACTION')
        con.name = 'action_slider_' + action.name
        con.show_expanded = False
        con.target = bpy.context.object
        con.subtarget = 'action_handle_' + action.name
        con.target_space = 'LOCAL'
        con.max = 1
        con.action = action
        con.frame_start = action.frame_range[0]
        con.frame_end = action.frame_range[1]


class ActionSlider_State(bpy.types.PropertyGroup):
    action_name: bpy.props.StringProperty(name='动作名称')

    slider_layers: bpy.props.BoolVectorProperty(
        name='控制器层',
        size=32, 
        subtype='LAYER_MEMBER',
        default=[True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, 
                False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False,]
    )

    slider_group: bpy.props.StringProperty(name='控制器组')

    def name_valid(self):
        return self.action_name != '' and bpy.data.actions.get(self.action_name) == None

class ActionSlider_PT_Panel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'ActionSlider'
    bl_label = 'Action Slider Create Tool'

    def draw(self, context):
        layout = self.layout
        state = context.scene.kumopult_as

        if context.selected_pose_bones == None or len(context.selected_pose_bones) == 0:
            layout.label(text='请选择若干姿态骨骼...')
            return
        elif context.active_pose_bone.name.startswith('action_slider_'):
            layout.label(text='选中了「' + context.active_pose_bone.name[14:] + '」动作滑块...')
            layout.operator(ActionSlider_OT_Remove.bl_idname, text=ActionSlider_OT_Remove.bl_label)
            return
        else:
            layout.label(text='选中了' + str(len(context.selected_pose_bones)) + '根骨骼:')
            box = layout.box()
            column = box.column()
            for pb in context.selected_pose_bones:
                column.label(text=pb.name, icon='BONE_DATA', translate=False)

        column = layout.column()
        column.prop(state, 'slider_layers', text='')
        column.prop_search(state, 'slider_group', context.object.pose, 'bone_groups', text='')

        column = layout.column()
        column.alert = not state.name_valid()
        column.prop(state, 'action_name', text='', icon='OUTLINER_DATA_GP_LAYER')
        layout.operator(ActionSlider_OT_Create.bl_idname, text=ActionSlider_OT_Create.bl_label)

class ActionSlider_OT_Create(bpy.types.Operator):
    bl_idname = 'kumopult_as.create'
    bl_label = '创建滑块'
    bl_description = '记录动作并创建对应滑块'

    @classmethod
    def poll(cls, context):
        state = context.scene.kumopult_as
        return state.name_valid()

    def execute(self, context):
        state = context.scene.kumopult_as

        action = record_pose()
        action.name = state.action_name
        create_controller(state.action_name, state.slider_layers, state.slider_group)
        add_constraints(action)
        state.action_name = ''

        return {'FINISHED'}

class ActionSlider_OT_Remove(bpy.types.Operator):
    bl_idname = 'kumopult_as.remove'
    bl_label = '删除'
    bl_description = '删除选中的滑块及其对应动作'

    def execute(self, context):
        state = context.scene.kumopult_as
        slider_name = context.active_pose_bone.name
        action_name = slider_name[14:]
        handle_name = 'action_handle_' + action_name

        # 移除约束
        for pb in context.object.pose.bones:
            for con in pb.constraints:
                if con.name == slider_name:
                    pb.constraints.remove(con)
        # 移除控制器
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        context.object.data.edit_bones.remove(context.object.data.edit_bones.get(handle_name))
        context.object.data.edit_bones.remove(context.object.data.edit_bones.get(slider_name))
        bpy.ops.object.mode_set(mode='POSE', toggle=False)
        # 移除动作
        bpy.data.actions.remove(bpy.data.actions.get(action_name))
        
        return {'FINISHED'}

classes = (
    ActionSlider_State,
    ActionSlider_PT_Panel,
    ActionSlider_OT_Create,
    ActionSlider_OT_Remove,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.kumopult_as = bpy.props.PointerProperty(type=ActionSlider_State)
    print('hello kumopult!')

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.kumopult_as
    print('goodbye kumopult!')