SEPARATOR = ';'


def get_camera_name_major(c):
    return c.split(SEPARATOR)[0].replace('/', '-')


def get_camera_name_minor(c):
    return ''


def get_camera_full_name(c):
    camera_name_minor = get_camera_name_minor(c)
    name_major = get_camera_name_major(c)
    name = name_major + ('_' + camera_name_minor if len(camera_name_minor) else '')
    return name

def get_camera_stream(c):
    return c.split(SEPARATOR)[1]

