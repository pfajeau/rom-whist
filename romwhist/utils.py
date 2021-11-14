import copy

def copy_dict(dict1):
    dict2 = dict()
    for key in dict1.keys():
        dict2[key] = copy.copy(dict1[key])

    return dict2
