from enum import IntEnum
import struct
import bpy

class TEXType(IntEnum):
    P8 = 1
    P8A8 = 2
    A1R5G5B5 = 6
    PA8 = 14
    P4 = 15
    PA4 = 16
    RGB888 = 17
    RGB8888 = 18
    
class TEXFile:
    def to_blender_image(self, name= 'tex_image'):
        im = bpy.data.images.new(name=name, width=self.width, height=self.height, alpha=self.is_alpha_format())
        pixels = list(im.pixels)
        
        for y in range(self.height):
            for x in range(self.width):
                flipped_y = self.height - y - 1
                b_pixel_index = 4 * ((flipped_y * self.width) + x)
                pixel_color = self.get_pixel(x, y)
                
                pixels[b_pixel_index] = pixel_color[0]
                pixels[b_pixel_index+1] = pixel_color[1]
                pixels[b_pixel_index+2] = pixel_color[2]
                pixels[b_pixel_index+3] = pixel_color[3]
    
        im.pixels = pixels[:]
        im.update()
        return im
        
    def __read_palette(self, file, color_count):
        for x in range(color_count):
            col_data = file.read(4)

            # add to palette, reordering BGRA to RGBA
            self.palette.append((col_data[2] / 255, col_data[1] / 255, col_data[0] / 255, col_data[3] / 255)) 
    
    def __make_palette_opaque(self):
        for i in range(len(self.palette)):
            pal_color = list(self.palette[i])
            pal_color[3] = 1.0
            self.palette[i] = tuple(pal_color)
    
    def is_paletted_format(self):
        return self.format != TEXType.RGB888 and self.format != TEXType.RGB8888 and self.format != TEXType.A1R5G5B5
        
    def is_alpha_format(self):
        return self.format != TEXType.P8 and self.format != TEXType.P4 and self.format != TEXType.RGB888
    
    def is_valid(self):
        return self.width != 0 and self.height != 0
        
    def get_stride(self):
        strides = (0, 
                   1, 
                   2, 
                   None, 
                   None, 
                   None, 
                   2, 
                   None, 
                   None, 
                   None, 
                   None, 
                   None, 
                   None, 
                   None,
                   1, 
                   -2, 
                   -2,
                   3,
                   4
                  )
                              
        
        fmt_int = int(self.format)
        if fmt_int >= 0 and fmt_int <= 18:
            return strides[fmt_int]

        # this should never happen
        raise Exception("A wild texture format has appeared")
            
    def calculate_mip_size(self, mipIndex):
        if mipIndex < 0:
            raise Exception("mipIndex must not be < 0")

        mip = 0;
        width = self.width
        height = self.height
        while mip != mipIndex:
            width //= 2
            height //= 2
            mip += 1

        return (width, height)

    def calculate_mip_array_size(self, mipIndex):
        size = self.calculate_mip_size(mipIndex)
        stride = self.get_stride()
        retval = (size[0] * size[1]) // -stride if stride < 0 else (size[0] * size[1]) * stride
        return retval;
    
    def __get_pixel_pa4_p4(self, x, y, stride, mip_data, mip_size, data_index):
        nibbles = mip_data[data_index]
        nibble1 = nibbles & 0x0F
        nibble2 = (nibbles & 0xF0) >> 4
        nibbleIdx = (x / -stride) + (y * (mip_size[0]  / -stride))
        return self.palette[nibble2] if nibbleIdx > 0 else self.palette[nibble1]
        
    def __get_pixel_pa8_p8(self, x, y, stride, mip_data, mip_size, data_index):
        pal_index = mip_data[data_index]
        return self.palette[pal_index]
        
    def __get_pixel_p8a8(self, x, y, stride, mip_data, mip_size, data_index):
        pal_index = mip_data[data_index]
        alpha = mip_data[data_index + 1]
        color = self.palette[pal_index]
        return (color[0], color[1], color[2], alpha / 255)
       
    def __get_pixel_rgb888(self, x, y, stride, mip_data, mip_size, data_index):
        return (mip_data[data_index] / 255, mip_data[data_index + 1] / 255, mip_data[data_index + 2] / 255, 1.0)
        
    def __get_pixel_rgb8888(self, x, y, stride, mip_data, mip_size, data_index):
        return (mip_data[data_index] / 255, mip_data[data_index + 1] / 255, mip_data[data_index + 2] / 255, mip_data[data_index + 3] / 255)
        
    def __get_pixel_a1r5g5b5(self, x, y, stride, mip_data, mip_size, data_index):
        color_short = struct.unpack('<H', (mip_data[data_index], mip_data[data_index + 1]))[0]
        maskA = 32768 
        maskR = 0x7C00
        maskG = 0x3E0
        maskB = 0x1F

        alpha = ((maskA & color_short) >> 8)
        red = ((maskR & color_short) >> 7)
        green = ((maskG & color_short) >> 2)
        blue = ((maskB & color_short) << 3)
        alpha = 255 if alpha > 0 else 0

        red = red | 0xF if (red & 0x8) == 0x8 else red
        green = green | 0xF if (red & 0x8) == 0x8 else green
        blue = blue | 0xF if (red & 0x8) == 0x8 else blue

        return (red / 255, green / 255, blue / 255, alpha / 255)
        
    def get_pixel(self, x, y, mip_level = 0):
        mip_data = self.mipmaps[mip_level]
        mip_size = self.calculate_mip_size(mip_level)
        stride = self.get_stride()
        
        data_index =  (x * stride) + (y * (mip_size[0] * stride)) if stride > 0 else (x // -stride) + (y * (mip_size[0] // -stride))

        get_pixel_functions = (None, 
                               self.__get_pixel_pa8_p8, 
                               self.__get_pixel_p8a8, 
                               None, 
                               None, 
                               None, 
                               self.__get_pixel_a1r5g5b5, 
                               None, 
                               None, 
                               None, 
                               None, 
                               None, 
                               None, 
                               None,
                               self.__get_pixel_pa8_p8, 
                               self.__get_pixel_pa4_p4, 
                               self.__get_pixel_pa4_p4,
                               self.__get_pixel_rgb888,
                               self.__get_pixel_rgb8888
                              )

            
        fmt_int = int(self.format)
        if fmt_int >= 0 and fmt_int <= 18:
            return get_pixel_functions[fmt_int](x, y, stride, mip_data, mip_size, data_index)
        else:
            return (0, 0, 0, 0)


    def read(self, filepath):
        file = open(filepath, 'rb')
        
        width, height, format = struct.unpack('<HHH', file.read(6))
        self.width = width
        self.height = height
        self.format = TEXType(format)
        
        mipcount, garbage, flags = struct.unpack('<HHL', file.read(8))
        
        # read palette if paletted format
        if self.format == TEXType.P4 or self.format == TEXType.PA4:
            self.__read_palette(file, 16)
        elif self.format == TEXType.P8A8 or self.format == TEXType.PA8 or self.format == TEXType.P8:
            self.__read_palette(file, 256)
            
        # make opaque palette if format doesn't support alpha
        if self.format == TEXType.P8 or self.format == TEXType.P4:
            self.__make_palette_opaque()
         
        # read mips
        for i in range(mipcount):
            mip_data_size = self.calculate_mip_array_size(i)
            if mip_data_size == 0:
                break
            data = file.read(mip_data_size)
            self.mipmaps.append(data)
    
    def __init__(self, filepath=None):
        self.palette = []
        self.width = 0
        self.height = 0
        self.format = TEXType.RGB8888
        self.mipmaps = []
        
        if filepath is not None:
            self.read(filepath)

