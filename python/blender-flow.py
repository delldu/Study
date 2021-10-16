import bpy

# Add cube
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
bpy.context.object.scale = [5, 5, 5]
bpy.ops.object.modifier_add(type = 'FLUID')
bpy.context.object.modifiers['Fluid'].fluid_type = 'DOMAIN'
bpy.context.object.modifiers['Fluid'].domain_settings.domain_type = 'LIQUID'
bpy.context.object.modifiers['Fluid'].domain_settings.use_mesh = 1
bpy.context.object.modifiers['Fluid'].domain_settings.cache_type = 'ALL'
bpy.context.object.modifiers['Fluid'].domain_settings.cache_frame_end = 60

# Add ball
bpy.ops.mesh.primitive_ico_sphere_add(location=(0, 0, 0))
bpy.ops.object.modifier_add(type='FLUID')
bpy.context.object.modifiers['Fluid'].fluid_type = 'FLOW'
bpy.context.object.modifiers['Fluid'].flow_settings.flow_type = 'LIQUID'
bpy.context.object.modifiers['Fluid'].flow_settings.flow_behavior = 'INFLOW'
bpy.context.object.modifiers['Fluid'].flow_settings.use_initial_velocity = 1
bpy.context.object.modifiers['Fluid'].flow_settings.velocity_coord = [0, 0, -2]


