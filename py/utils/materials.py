import bpy


def create_magic_material(
    color: tuple[float, float, float],
    name: str,
    emission_value: float = 0.0,
):
    mat = bpy.data.materials.new(name=name + "TrackMaterial")
    mat.use_nodes = True

    # Get the node tree and clear default nodes
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Keep output node and remove others for a clean slate
    output_node = nodes.get("Material Output")
    if not output_node:
        output_node = nodes.new(type="ShaderNodeOutputMaterial")

    # Create principled BSDF node
    bsdf = nodes.get("Principled BSDF")
    if not bsdf:
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")

    # Link BSDF to output
    links.new(bsdf.outputs[0], output_node.inputs[0])

    # Set base color and emission
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Emission Color"].default_value = (*color, 1)
    bsdf.inputs["Emission Strength"].default_value = emission_value

    # Create Magic texture
    magic_tex = nodes.new(type="ShaderNodeTexMagic")

    # Configure magic texture
    magic_tex.turbulence_depth = 2  # Number of iterations (1-10)
    magic_tex.inputs["Scale"].default_value = 5.0  # Scale of the pattern
    magic_tex.inputs["Distortion"].default_value = 2.0  # Amount of distortion

    # Color correction for magic texture
    hue_sat = nodes.new(type="ShaderNodeHueSaturation")
    hue_sat.inputs["Saturation"].default_value = 0.8
    hue_sat.inputs["Value"].default_value = 0.7

    # Calculate brightness from original color for hue shift
    brightness = (color[0] + color[1] + color[2]) / 3
    hue_shift = 0.5 if brightness > 0.5 else 0.0
    hue_sat.inputs["Hue"].default_value = hue_shift

    # Mix with base color
    mix_rgb = nodes.new(type="ShaderNodeMixRGB")
    mix_rgb.blend_type = "MULTIPLY"
    mix_rgb.inputs[0].default_value = 0.7  # Blending factor
    mix_rgb.inputs[1].default_value = (*color, 1.0)  # Base color

    # Connect nodes
    links.new(magic_tex.outputs["Color"], hue_sat.inputs["Color"])
    links.new(hue_sat.outputs["Color"], mix_rgb.inputs[2])
    links.new(mix_rgb.outputs[0], bsdf.inputs["Base Color"])

    # Add texture coordinates for proper mapping
    tex_coord = nodes.new(type="ShaderNodeTexCoord")
    mapping = nodes.new(type="ShaderNodeMapping")

    # Connect texture coordinates
    links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], magic_tex.inputs["Vector"])

    # Add roughness variation
    rough_mix = nodes.new(type="ShaderNodeMixRGB")
    rough_mix.blend_type = "MULTIPLY"
    rough_mix.inputs[0].default_value = 0.5
    rough_mix.inputs[1].default_value = (0.7, 0.7, 0.7, 1.0)  # Base roughness

    # Get brightness from magic texture for roughness
    bright = nodes.new(type="ShaderNodeRGBToBW")
    links.new(magic_tex.outputs["Color"], bright.inputs["Color"])
    links.new(bright.outputs[0], rough_mix.inputs[2])
    links.new(rough_mix.outputs[0], bsdf.inputs["Roughness"])

    return mat
