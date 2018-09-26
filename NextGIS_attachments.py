#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import zipfile
import os
import tempfile
import json
import shutil
import argparse
from requests.auth import HTTPBasicAuth

#python NextGIS_attachments.py --url elina-usmanova --login administrator --password 123456 --parent_id 760 --path_name_zip D:/NextGIS/Attachments/zip1

parser = argparse.ArgumentParser()
parser.add_argument('--url',type=str,required=True)
parser.add_argument('--login',type=str,required=True,default='administrator')
parser.add_argument('--password',type=str,required=True)
parser.add_argument('--parent_id',type=str,required=True)
parser.add_argument('--path_name_zip',type=str,required=True)

args = parser.parse_args()

#path = tempfile.gettempdir()
#path = path.replace('\\','/')
path = "D:/"

def generate_zip(url, login, password, parent_id, path_name_zip): 
    elems = []
    AUTH = HTTPBasicAuth(login, password)
    #Открываем zip на запись
    with zipfile.ZipFile(path_name_zip + '.zip', 'w') as z:
        r = requests.get("http://%s.nextgis.com/api/resource/%s/geojson" %(url, parent_id), auth = AUTH)
        q = requests.get("http://%s.nextgis.com/api/resource/%s" %(url, parent_id), auth = AUTH)
        d = requests.get("http://%s.nextgis.com/api/resource/%s/feature/" %(url, parent_id), auth = AUTH)
        f = q.json()
        data = json.loads(r.text)
        dt = json.loads(d.text)
        l = []
        at = []
        attachments = []
        #print (dt)
        for elem in dt:
            if elem["extensions"]["attachment"] != None:
                for el in elem["extensions"]["attachment"]:
                    at.append(el["name"])
                attachments.append(at)
                at = []
            else:
                attachments.append(l)
        for el in range(len(data["features"])):
            data["features"][el]["properties"]["attachments"] = attachments[el]
        d = json.dumps(data)
        with open("D:/%s.geojson" %(f['resource']['display_name']), 'w') as gj:
            gj.write(d)
            gj.close()
        z.write(r"D:/%s.geojson" %(f['resource']['display_name']))
        os.remove("D:/%s.geojson" %(f['resource']['display_name']))
        r = requests.get('http://%s.nextgis.com/api/resource/%s/feature/' %(url, parent_id), auth = AUTH)
        data = json.loads(r.text)    
        for elem in data:
            elems.append(elem['id'])
            if elem['extensions']['attachment'] != None:
                os.mkdir(path + str(elem['id']))
                #Загрузка вложений
                for attach in elem['extensions']['attachment']:
                    fid = attach['id']
                    p = requests.get("http://%s.nextgis.com/api/resource/%s/feature/%s/attachment/%s/image" % (url, parent_id, elem['id'], fid), auth = AUTH)
                    with open(path + str(elem['id']) + '/' + attach['name'], "wb") as out:
                        out.write(p.content)
                        out.close()
                directories = os.listdir(path + str(elem['id']))
                for d in directories:
                    #print(d)
                    z.write(path + str(elem['id']) + '/%s' % (d))  
            else:
                continue
        z.close() 
    #Удаление созданных папок
    for el in elems:
        shutil.rmtree(path + str(el), ignore_errors = True)
        
if __name__ == '__main__':
    generate_zip(args.url, args.login, args.password, args.parent_id, args.path_name_zip)

