# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Copyright (C) Dummiesman, 2016
#
# ##### END LICENSE BLOCK #####

import bpy, struct

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
    return struct.unpack('f', file.read(4))[0]


def read_float3(file):
    return struct.unpack('fff', file.read(12))


def read_cfloat3(file):
    btc = struct.unpack('BBB', file.read(3))
    return (btc[0]-128)/128, (btc[1]-128)/128, (btc[2]-128)/128


def read_cfloat2(file):
    stc = struct.unpack('HH', file.read(4))
    return (stc[0]/128) - 128, (stc[1]/128) - 128


def read_float2(file):
    return struct.unpack('ff', file.read(8))


def read_color4f(file):
    return struct.unpack('ffff', file.read(16))


def read_color4d(file):
    c4d = struct.unpack('BBBB', file.read(4))
    return [c4d[0]/255, c4d[1]/255, c4d[2]/255, c4d[3]/255]
    
#########
# WRITE #
#########
def write_angel_string(file, strng):
    str_len = len(strng)
    if str_len > 0:
        file.write(struct.pack('B', str_len+1))
        file.write(bytes(strng, 'UTF-8'))
        file.write(bytes('\x00', 'UTF-8'))
    else:
        file.write(struct.pack('B', 0))

def write_float2(file, data):
    file.write(struct.pack('FF', data[0], data[1]))
    
def write_float3(file, data):
    file.write(struct.pack('FFF', data[0], data[1], data[2]))
    
def write_color4d(file, color, alpha=1):
    file.write(struct.pack('BBBB', int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), int(alpha * 255)))
    
def write_color4f(file, color, alpha=1):
    file.write(struct.pack('FFFF', color[0], color[1], color[2], alpha))


def write_file_header(file, name, length=0):
    file.write(bytes('FILE', 'utf-8'))
    write_angel_string(file, name)
    file.write(struct.pack('L', length))