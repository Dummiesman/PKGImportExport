# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Created by Dummiesman, 2016-2020
#
# ##### END LICENSE BLOCK #####

import io_scene_pkg.binary_helper as bin
import struct

class Shader:
    def print(self):
        # lazyily written debug function
        print("=== SHADER: " + str(self.name) + " ===")
        print("Diffuse Color is [" + str(self.diffuse_color[0]) + ","+ str(self.diffuse_color[1]) + ","+ str(self.diffuse_color[2]) + ","+ str(self.diffuse_color[3]) + "]")
        print("Ambient Color is [" + str(self.ambient_color[0]) + ","+ str(self.ambient_color[1]) + ","+ str(self.ambient_color[2]) + ","+ str(self.ambient_color[3]) + "]")
        print("Specular Color is [" + str(self.specular_color[0]) + ","+ str(self.specular_color[1]) + ","+ str(self.specular_color[2]) + ","+ str(self.specular_color[3]) + "]")
        print("Emissive Color is [" + str(self.emissive_color[0]) + ","+ str(self.emissive_color[1]) + ","+ str(self.emissive_color[2]) + ","+ str(self.emissive_color[3]) + "]")
        print("Shininess is " + str(self.shininess))
    
    def write(self, file, type):
        bin.write_angel_string(file, self.name)
    
        if type == "byte":
            bin.write_color4d(file, self.diffuse_color, self.diffuse_color[3])
            bin.write_color4d(file, self.ambient_color, self.ambient_color[3])
            bin.write_color4d(file, self.emissive_color)
        elif type == "float":
            bin.write_color4f(file, self.diffuse_color, self.diffuse_color[3])
            bin.write_color4f(file, self.ambient_color, self.ambient_color[3])
            bin.write_color4f(file, self.specular_color)
            bin.write_color4f(file, self.emissive_color)
            
        file.write(struct.pack('f', self.shininess))
        
    def read(self, file, type):
        texture_name = bin.read_angel_string(file)
        if texture_name == '':
            # matte material
            texture_name = None
            
        self.name = texture_name

        if type == "float":
            self.diffuse_color = bin.read_color4f(file)
            self.ambient_color = bin.read_color4f(file)
            self.specular_color = bin.read_color4f(file)
            self.emissive_color = bin.read_color4f(file)
        elif type == "byte":
            self.diffuse_color = bin.read_color4d(file)
            self.ambient_color = bin.read_color4d(file)
            self.emissive_color = bin.read_color4d(file)
        else:
            raise Exception("Cannot read shader type " + str(type))
            
        self.shininess = bin.read_float(file)
    
    def __init__(self, file=None, type=None):
        self.name = None
        self.diffuse_color = [1,1,1,1]
        self.emissive_color = [0,0,0,0]
        self.specular_color = [0,0,0,0]
        self.ambient_color = [1,1,1,1]
        self.shininess = 0.0
        
        if file is not None and type is not None:
            self.read(file, type)

    @staticmethod
    def __iter_check_equal(i1, i2):
        l1 = len(i1)
        l2 = len(i2)
        if l1 != l2:
            return False
        for idx in range(l1):
            if i1[idx] != i2[idx]:
                return False
        return True
        
    def __eq__(self, obj):
        if not isinstance(obj,Shader):
            return False
         
        return (Shader.__iter_check_equal(obj.diffuse_color, self.diffuse_color) and
               Shader.__iter_check_equal(obj.ambient_color, self.ambient_color) and
               Shader.__iter_check_equal(obj.specular_color, self.specular_color) and
               Shader.__iter_check_equal(obj.emissive_color, self.emissive_color) and
               obj.shininess == self.shininess and obj.name == self.name)
        
    def __ne__(self, obj):
        return not self == obj
   

class ShaderSet:
    def read(self, file):
        shadertype_raw, shaders_per_paintjob = struct.unpack('2L', file.read(8))
        
        self.type = "float"
        self.num_variants = shadertype_raw
        # determine real shader type
        
        if shadertype_raw > 128:
            # byte shader. also we need to do some math
            self.num_variants -= 128
            self.type = "byte"    
            
        for shader_set_num in range(self.num_variants):
            variant = []
            for shader_num in range(shaders_per_paintjob):
                shader = Shader(file, self.type)
                variant.append(shader)
            self.variants.append(variant)
        
    def __init__(self, file=None):
        self.name = None
        self.type = "float"
        self.num_variants = 0
        self.variants = []        
        
        if file is not None:
            self.read(file)
