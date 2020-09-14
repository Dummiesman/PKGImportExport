def get_raw_object_name(meshname):
    return meshname.upper().replace("_VL", "").replace("_L", "").replace("_M", "").replace("_H", "")

def is_matrix_object(obj):
    obj_name = get_raw_object_name(obj.name)
    return (obj_name == "AXLE0" or obj_name == "AXLE1" or obj_name == "SHOCK0" or obj_name == "SHOCK1" or obj_name == "SHOCK2" or obj_name == "SHOCK3" 
            or obj_name == "ARM0" or obj_name == "ARM1" or obj_name == "ARM2" or obj_name == "ARM3" or obj_name == "SHAFT2" or obj_name == "SHAFT3" or obj_name == "ENGINE")