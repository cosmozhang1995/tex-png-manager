import sys, os
import uuid
import ConfigParser
import MySQLdb
import json

root_path = os.path.split(os.path.realpath(__file__))[0] + '/'
conf = ConfigParser.ConfigParser()
config_path = os.path.realpath(root_path + "./config.conf")
conf.read(config_path)

mysql_host = conf.get('database', 'host')
mysql_port = conf.get('database', 'port')
mysql_user = conf.get('database', 'user')
mysql_passwd = conf.get('database', 'passwd')
mysql_db = conf.get('database', 'db')

manager_items = [item[0] for item in conf.items('manager')]

tmp_dir = conf.get('manager', 'tmp_dir') if 'tmp_dir' in manager_items else "./tex2im"
if tmp_dir[0] == ".": tmp_dir = os.path.realpath(root_path + '/' + tmp_dir)
if not os.path.exists(tmp_dir) or not os.path.isdir(tmp_dir): os.makedirs(tmp_dir)
tmp_texc_dir = os.path.join(tmp_dir, 'texc') # temp subdir to save latex content
if not os.path.exists(tmp_dir) or not os.path.isdir(tmp_dir): os.makedirs(tmp_dir)

image_dir = conf.get('manager', 'image_dir') if 'image_dir' in manager_items else "./static/tex_images"
if image_dir[0] == ".": image_dir = os.path.realpath(root_path + '/' + image_dir)
if not os.path.exists(image_dir) or not os.path.isdir(image_dir): os.makedirs(image_dir)

tex2im_path = conf.get('manager', 'tex2im_path') if 'tex2im_path' in manager_items else "./tmp"
if tex2im_path[0] == ".": tex2im_path = os.path.realpath(root_path + '/' + tex2im_path)

image_format = 'png'

def generateTexImage(texContent, toFileName, options = None):
    if options is None: options = {}
    temp_file_name = str(uuid.uuid1())
    temp_file_path = tmp_dir + '/' + temp_file_name + '.tex'
    f = open(temp_file_path, 'w')
    f.write(texContent)
    f.close()
    opt_str = ""
    if 'transparent' in options and options['transparent']: opt_str += " -z"
    elif 'dpi' in options:
        if options['dpi'] == 100: opt_str += " -r 100*100"
        elif options['dpi'] == 150: opt_str += " -r 150*150"
        elif options['dpi'] == 200: opt_str += " -r 200*150"
        elif options['dpi'] == 300: opt_str += " -r 300*300"
    elif 'header' in options: opt_str += " -x " + options['header']
    print "{0} {1} -o {2} {3}".format(tex2im_path, opt_str, toFileName, temp_file_path)
    result = os.system("{0} {1} -x ~/Desktop/header.tex -o {2} {3}".format(tex2im_path, opt_str, toFileName, temp_file_path)) >> 8
    os.remove(temp_file_path)
    return result

class Util:
    def __init__(self, image_dir = image_dir):
        if image_dir[0] == ".": image_dir = os.path.realpath(root_path + '/' + image_dir)
        if not os.path.exists(image_dir) or not os.path.isdir(image_dir): os.makedirs(image_dir)
        self.image_dir = image_dir

    def getConnection(self):
        conn = MySQLdb.connect(
            host = mysql_host,
            port = mysql_port,
            user = mysql_user,
            passwd = mysql_passwd,
            db = mysql_db)
        cur = conn.cursor()
        return (conn, cur)

    def closeConnection(self, conn_cur, commit = True):
        conn = conn_cur[0]
        cur = conn_cur[1]
        cur.close()
        if commit: conn.commit()
        conn.close()

    def addTex(self, texContent, options = None):
        (conn, cur) = self.getConnection()
        _uuid = str(uuid.uuid1())
        image_path = os.path.realpath(self.image_dir, str(_uuid) + '.' + image_format)
        if not (cur.execute('INSERT INTO `tex` (`uuid`, `content`) VALUES ("{0}", "{1}")'.format(str(_uuid), texContent.replace('"', '\\"'))) \
                    and cur.execute('SELECT `id` FROM `tex` WHERE `uuid` = "{0}"'.format(str(_uuid)))):
            self.closeConnection(conn, cur)
            return None
        texItem = Tex(cur.fetchone()[0], _uuid, texContent)
        if not texItem.saveImage == 0:
            self.closeConnection(conn, cur)
            return None
        return texItem


class Tex:
    def __init__(self, _id, _uuid, content, imagePath):
        self.id = int(_id)
        self._uuid = uuid.UUID(_uuid)
        self.content = content
        if imagePath[0] == '.': self.imagePath = os.path.realpath(os.path.join(root_path, imagePath))
        else: self.imagePath = os.path.realpath(imagePath)

    def generateImage(self):
        return generateTexImage(self.content, self.imagePath)

    def toJson(self):
        return {
            "id": self.id
            "_uuid": str(self._uuid)
            "content": self.content
            "imagePath": self.imagePath
        }

    def toJsonStr(self, indent = None):
        return json.dumps(self.toJson(), indent = indent)


