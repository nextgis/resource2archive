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
from tqdm import tqdm
import tempfile

#python getfullresource.py --url elina-usmanova --login administrator --password pass --parent_id 760 --zip c:/work/zip1

parser = argparse.ArgumentParser()
parser.add_argument('--url',type=str,required=True)
parser.add_argument('--login',type=str,default='administrator')
parser.add_argument('--password',type=str)
parser.add_argument('--parent_id',type=str,required=True)
parser.add_argument('--zip',type=str,required=True)

args = parser.parse_args()

path = tempfile.gettempdir()

def generate_zip(url, login, password, parent_id, zip): 
    elems = []
    if args.login and args.password:
        AUTH = HTTPBasicAuth(login, password)
    else:
        AUTH = HTTPBasicAuth('guest','guest')

    print ('Downloading structure...')
    with zipfile.ZipFile(zip + '.zip', 'w') as z:
        r = requests.get("http://%s.nextgis.com/api/resource/%s/geojson" %(url, parent_id), auth = AUTH)
        q = requests.get("http://%s.nextgis.com/api/resource/%s" %(url, parent_id), auth = AUTH)
        d = requests.get("http://%s.nextgis.com/api/resource/%s/feature/" %(url, parent_id), auth = AUTH)
        f = q.json()
        data = json.loads(r.text)
        dt = json.loads(d.text)
        l = []
        at = []
        attachments = []
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
        
        attach_count = 0
        for elem in data:
            if elem['extensions']['attachment'] != None:
                attach_count+=1
        
        pbar = tqdm(total=attach_count)
        for elem in data:
            if elem['extensions']['attachment'] != None:
                elems.append(elem['id'])
                id = str(elem['id'])
                os.mkdir(os.path.join(path,id))
                #Download attachements
                for attach in elem['extensions']['attachment']:
                    fid = attach['id']
                    p = requests.get("http://%s.nextgis.com/api/resource/%s/feature/%s/attachment/%s/image" % (url, parent_id, elem['id'], fid), auth = AUTH)
                    with open(os.path.join(path,id,attach['name']), "wb") as out:
                        out.write(p.content)
                        out.close()
                directories = os.listdir(os.path.join(path,id))
                for d in directories:
                    #print(d)
                    z.write(os.path.join(path,id,d),os.path.join(id,d))
                pbar.update(1)
        z.close() 
        pbar.close()
    #Clean up folders
    for el in elems:
        shutil.rmtree(os.path.join(path,str(el)), ignore_errors = True)
        
if __name__ == '__main__':
    generate_zip(args.url, args.login, args.password, args.parent_id, args.zip)

