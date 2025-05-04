bl_info = {
    "name": "Multi-View Rendering",
    "author": "nadavc220",
    "blender": (4, 2, 1),
#    "location": "View3D > Add Mesh",
    "description": "Renders a chosen mesh from views over 360 degrees",
    "category": "Render",
}


import bpy
import os
import math

#################################### Black Box Code #############################################

def get_mesh_objects(scene, context):
    """Returns a list of mesh objects in the current scene"""
    return [(obj.name, obj.name, "") for obj in bpy.data.objects if obj.type == 'MESH']

def update_selected_mesh(self, context):
    """Update function to highlight the selected mesh"""
    selected_mesh_name = context.scene.selected_mesh
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Get the mesh object by name
    selected_mesh = bpy.data.objects.get(selected_mesh_name)
    if selected_mesh:
        # Set the mesh as active and select it
        context.view_layer.objects.active = selected_mesh
        selected_mesh.select_set(True)  # Highlights in orange

def rotate_camera_position(camera, frames):
    pos_angle = (1 / frames) * 360
    x = camera.location.x * math.cos(math.radians(pos_angle)) - camera.location.y * math.sin(math.radians(pos_angle))
    y = camera.location.x * math.sin(math.radians(pos_angle)) + camera.location.y * math.cos(math.radians(pos_angle))
    camera.location.x = x
    camera.location.y = y

def calculate_tilt_to_target(camera, target):
    # calculate camera_tilt
    b = math.sqrt((camera.location.x - target.location.x)**2 + (camera.location.y - target.location.y)**2)
    v = math.sqrt((camera.location.y - target.location.y)**2 + (camera.location.z - target.location.z)**2)
    alpha = math.acos(b/v)
    return alpha

def rotate_camera_to_target(camera, frames):
    pos_angle = (1 / frames) * 360
    camera.rotation_euler[2] += math.radians(pos_angle)


def render360(object_name, num_frames, camera_radius, image_h, image_w, output_path=None):
    if output_path is None:
        output_path = f"/home/nadav/Documents/renders/{object_name}/"  # Set the path where the images will be saved
    rotation_axis = 'X'  # Axis to rotate around (X, Y, or Z)

    # Get the object by names
    target = bpy.data.objects[object_name] 

    # Set up the camera
    camera = bpy.data.objects['Camera']
    camera.location = (0, -camera_radius, 5)  # Adjust camera position as needed

    # calculate camera_tilt
    alpha_tilt = calculate_tilt_to_target(camera, target)

    camera.rotation_euler = (math.radians(90) - alpha_tilt, 0, 0)  # Pointing the camera toward the object

    # Ensure the camera points at the object
    bpy.ops.object.select_all(action='DESELECT')
    target.select_set(True)
    bpy.context.view_layer.objects.active = target

    # Set the start and end frames for the loop
    start_frame = bpy.context.scene.frame_start  # usually the first frame (e.g., 1)
    end_frame = bpy.context.scene.frame_end  # usually the last frame

    # Set the current frame to the start frame to begin the animation
    bpy.context.scene.frame_set(start_frame)

    # Set render settings
    scene = bpy.context.scene
    scene.render.image_settings.file_format = 'PNG'  # Output format
    scene.render.resolution_x = image_h  # Set resolution
    scene.render.resolution_y = image_w
    #scene.render.film_transparent = True  # Enable transparency if needed


    # Rotate and render
    for i in range(num_frames):
        bpy.context.scene.frame_set(bpy.context.scene.frame_current + 1)
    #    rotation_angle = (i / frames) * 360
    #    camera.rotation_euler.rotate_axis(rotation_axis, math.radians(rotation_angle))
    ##    camera.rotation_euler.rotate_axis((rotation_axis, math.radians(angle))
    #    
    #    # Update scene and render
    #    scene.render.filepath = f"{output_path}frame_{i:03d}.png"
    #    bpy.ops.render.render(write_still=True)

    #    # Reset rotation for the next frame
    #    camera.rotation_euler.rotate_axis(rotation_axis, -math.radians(rotation_angle))
        file = os.path.join(output_path, str(i))
        bpy.context.scene.render.filepath = file
        bpy.ops.render.render( write_still=True ) 
        
        # Move Camera to next position
        rotate_camera_position(camera, num_frames)
        rotate_camera_to_target(camera, num_frames)
        
        if bpy.context.scene.frame_current > end_frame:
            # Reset to the start frame if the end is reached
            bpy.context.scene.frame_set(start_frame)

    # Reset the object's rotation to the original state
    #target.rotation_euler = (0, 0, 0)

#################################### Main Addon Code #############################################

class Render360Operator(bpy.types.Operator):
    """Operator to render the scene from 360 degrees"""
    bl_idname = "render.render_360_operator"
    bl_label = "Render 360 Degrees"

    def execute(self, context):
        object_name = context.scene.selected_mesh
        camera_radius = context.scene.camera_radius
        num_frames = context.scene.num_frames
        render_depth_maps = context.scene.render_depth_maps
        image_h = context.scene.res_y
        image_w = context.scene.res_x
        render360(object_name, num_frames, camera_radius, image_h, image_w, output_path=None)
        return {'FINISHED'}

class Render360Panel(bpy.types.Panel):
    """ Displayy panel in 3D view"""
#    bl_label = "3D Multi-View Rendering"
#    bl_space_type = "VIEW_3D"
#    bl_region_type = "UI"
#    bl_options = {'HEADER_LAYOUT_EXPAND'}
    
    bl_label = "360 Degree Render"
    bl_idname = "RENDER_PT_360"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Add a dropdown for selecting a mesh object
        layout.prop(scene, "selected_mesh", text="Select Mesh")
        
        # Add a numeric input field for the number of requested frames
        layout.prop(scene, "num_frames", text="Number of Rendered Frames")
        
        # Add a numeric input field for the camera radius
        layout.prop(scene, "camera_radius", text="Camera Radius")
        
        # Add a numeric input field for the number of requested frames
        layout.prop(scene, "res_x", text="Resolution X")
        
        # Add a numeric input field for the number of requested frames
        layout.prop(scene, "res_y", text="Resolution Y")
        
        # Add a checkbox for rendering depth maps
        layout.prop(scene, "render_depth_maps", text="Render Depth Maps")
        
        # Add a checkbox for rendering depth maps
        layout.prop(scene, "animation_on", text="Animation")
        
        # Add a button to start rendering
        layout.operator("render.render_360_operator", text="Render 360 Degrees")

classes = (
        Render360Panel,
        Render360Operator,
        )
    

def register():

        
    # Add an enum property for selecting a mesh object
    bpy.types.Scene.selected_mesh = bpy.props.EnumProperty(
        name="Select Mesh",
        description="Select a mesh object from the scene",
        items=get_mesh_objects,
        update=update_selected_mesh  # Set the update function
    )
        
    # Add a property to the Scene for camera radius
    bpy.types.Scene.num_frames = bpy.props.IntProperty(
        name="Number of Rendered Frames",
        description="Number of frames to be rendered around the main object",
        default=4,
        min=1,
        max=1080,
    )
    
    # Add a property to the Scene for camera radius
    bpy.types.Scene.camera_radius = bpy.props.FloatProperty(
        name="Camera Radius",
        description="Radius of the circle the camera moves on",
        default=10.0,
        min=0.1,
        max=100.0,
    )
    
    # Add a property to the Scene for camera radius
    bpy.types.Scene.res_x = bpy.props.IntProperty(
        name="Resolution X",
        description="Resolution of output x axis",
        default=1024,
        min=10,
        max=2048,
    )
    
    # Add a property to the Scene for camera radius
    bpy.types.Scene.res_y = bpy.props.IntProperty(
        name="Resolution Y",
        description="Resolution of output y axis",
        default=1024,
        min=10,
        max=2048,
    )
    
    # Add a boolean property to decide whether to render depth maps
    bpy.types.Scene.render_depth_maps = bpy.props.BoolProperty(
        name="Render Depth Maps",
        description="Toggle rendering of depth maps",
        default=False,
    )
    
    # Add a boolean property to decide whether to render depth maps
    bpy.types.Scene.animation_on = bpy.props.BoolProperty(
        name="Animation ON",
        description="Toggle rendering with/without animation",
        default=False,
    )
    
    bpy.utils.register_class(Render360Panel)
    bpy.utils.register_class(Render360Operator)
    
    
def unregister():
    # Remove properties from the Scene
    del bpy.types.Scene.camera_radius
    del bpy.types.Scene.render_depth_maps
    del bpy.types.Scene.selected_mesh
    del bpy.types.Scene.output_directory
    bpy.utils.unregister_class(Render360Panel)
    bpy.utils.unregister_class(Render360Operator)

if __name__ == "__main__":
    register()