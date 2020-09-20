# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Created by Dummiesman, 2016-2020
#
# ##### END LICENSE BLOCK #####

import bpy, struct, mathutils
from bpy_extras.io_utils import axis_conversion
import math
import io_scene_pkg.common_helpers as helper

########
# READ #
########
def read_angel_string(file):
    str_len = struct.unpack('B', file.read(1))[0]
    if str_len == 0:
        return ''
    else:
        return_string = file.read(str_len - 1).decode("utf-8")
        file.seek(1, 1)
        return return_string

def read_float(file):
    return struct.unpack('<f', file.read(4))[0]


def read_float3(file):
    return struct.unpack('<fff', file.read(12))


def read_cfloat3(file):
    btc_data = file.read(3)    
    btc = (btc_data[0] - 128, btc_data[1] - 128, btc_data[2] - 128)
    return float(btc[0]) / 127, float(btc[1]) / 127, float(btc[2])  / 127


def read_cfloat2(file):
    stc = struct.unpack('<HH', file.read(4))
    return (stc[0]/128) - 128, (stc[1]/128) - 128


def read_float2(file):
    return struct.unpack('<ff', file.read(8))


def read_color4f(file):
    return struct.unpack('<ffff', file.read(16))


def read_color4d(file):
    c4d = struct.unpack('BBBB', file.read(4))
    return [c4d[0]/255, c4d[1]/255, c4d[2]/255, c4d[3]/255]


def read_matrix3x4(file):
    row1r = list(struct.unpack('<fff', file.read(12)))
    row2r = list(struct.unpack('<fff', file.read(12)))
    row3r = list(struct.unpack('<fff', file.read(12)))
    translation = struct.unpack('<fff', file.read(12))
    
    # transpose the matrix
    col1 = [row1r[0], row2r[0], row3r[0], translation[0]]
    col2 = [row1r[1], row2r[1], row3r[1], translation[1]]
    col3 = [row1r[2], row2r[2], row3r[2], translation[2]]
    
    # create matrix, and convert its coordinate space
    mtx = mathutils.Matrix((col1, col2, col3)).to_4x4()
    
    mtx_convert = axis_conversion(from_forward='-Z', 
        from_up='Y',
        to_forward='-Y',
        to_up='Z').to_4x4()
    
    mtx = mtx_convert @ mtx
    
    mat_rot = mathutils.Matrix.Rotation(math.radians(90), 4, 'X') @ mathutils.Matrix.Rotation(math.radians(180), 4, 'Y')
    mtx @= mat_rot 
    
    return mtx.to_4x4()

#########
# WRITE #
#########
def write_matrix3x4(file, matrix):  
    # passed by ref, don't mess that up
    matrix = matrix.copy() 
    
    # convert coordinate space   
    mat_rot = mathutils.Matrix.Rotation(math.radians(-180.0), 4, 'Y') @ mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'X')
    matrix @= mat_rot
    
    mtx_convert = axis_conversion(from_forward='-Y', 
        from_up='Z',
        to_forward='-Z',
        to_up='Y').to_4x4()
    matrix = mtx_convert @ matrix
    
    #write 3x3
    file.write(struct.pack('<fff', matrix[0][0], matrix[1][0], matrix[2][0]))
    file.write(struct.pack('<fff', matrix[0][1], matrix[1][1], matrix[2][1]))
    file.write(struct.pack('<fff', matrix[0][2], matrix[1][2], matrix[2][2]))
    file.write(struct.pack('<fff', matrix[0][3], matrix[1][3], matrix[2][3]))
    

def write_angel_string(file, strng):
    if strng is not None and len(strng) > 0:
        file.write(struct.pack('B', len(strng)+1))
        file.write(bytes(strng, 'UTF-8'))
        file.write(bytes('\x00', 'UTF-8'))
    else:
        file.write(struct.pack('B', 0))


def write_float2(file, data):
    file.write(struct.pack('<ff', data[0], data[1]))

    
def write_float3(file, data):
    file.write(struct.pack('<fff', data[0], data[1], data[2]))

    
def write_color4d(file, color, alpha=1):
    r = min(255, int(color[0] * 255))
    g = min(255, int(color[1] * 255))
    b = min(255, int(color[2] * 255))
    a = min(255, int(alpha * 255))
    file.write(struct.pack('BBBB', r, g, b, a))


def write_color4f(file, color, alpha=1):
    file.write(struct.pack('<ffff', color[0], color[1], color[2], alpha))


def write_file_header(file, name, length=0):
    file.write(bytes('FILE', 'utf-8'))
    write_angel_string(file, name)
    file.write(struct.pack('L', length))