"""custom_classes.py

NOTE: Number of YOLO COCO output classes differs from SSD COCO models.
"""
import configparser

def get_names(config_path):
    CUSTOM_CLASSES_LIST = []

    config = configparser.ConfigParser()
    config.read(config_path)
    names_path = config['Model']['names']

    with open(names_path) as f:
        for line in f.readlines():
            if line != '':
                CUSTOM_CLASSES_LIST.append(line.rstrip('\n'))
    
    return CUSTOM_CLASSES_LIST

def get_cls_dict(config_path):
    """Get the class ID to name translation dictionary."""
    return {i: n for i, n in enumerate(get_names(config_path))}

if __name__ == '__main__':
    result = get_cls_dict('appsettings.ini')
    print(result)