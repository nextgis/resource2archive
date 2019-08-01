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

#python getfullresource.py --url demo --login test --password testtest --layer_id 4248 --zip output.zip

parser = argparse.ArgumentParser()
parser.add_argument('--url',type=str,required=True)
parser.add_argument('--login',type=str,default='administrator')
parser.add_argument('--password',type=str)
parser.add_argument('--layer_id',type=str,required=True)
parser.add_argument('--zip',type=str)

args = parser.parse_args()

path = tempfile.gettempdir()

def generate_zip(url, login, password, layer_id, output_zip): 
    elems = []
    if args.login and args.password:
        AUTH = HTTPBasicAuth(login, password)
    else:
        AUTH = HTTPBasicAuth('guest','guest')

    print ('Downloading structure...')
    data = requests.get("http://%s.nextgis.com/api/resource/%s/geojson" %(url, layer_id), auth = AUTH).json()
    resource = requests.get("http://%s.nextgis.com/api/resource/%s" %(url, layer_id), auth = AUTH).json()
    features = requests.get("http://%s.nextgis.com/api/resource/%s/feature/" %(url, layer_id), auth = AUTH).json()
        
    at = []
    attachments = []
    for elem in features:
        if elem["extensions"]["attachment"] != None:
            for el in elem["extensions"]["attachment"]:
                at.append(el["name"])
            attachments.append(at)
            at = []
        else:
            attachments.append([])
    for el in range(len(data["features"])):
        data["features"][el]["properties"]["attachments"] = attachments[el]
    
    geojson_filename = '%s.geojson' %(resource['resource']['display_name'])
    geojson_filenamefull = os.path.join(path,geojson_filename)
    with open(geojson_filenamefull, 'w') as gj:
        gj.write(json.dumps(data))
    
    with zipfile.ZipFile(output_zip, 'w') as z:
        z.write(geojson_filenamefull,geojson_filename)
        os.remove(geojson_filenamefull)
        
        attach_count = 0
        for elem in features:
            if elem['extensions']['attachment'] != None:
                attach_count+=1
        
        pbar = tqdm(total=attach_count)
        for elem in features:
            if elem['extensions']['attachment'] != None:
                elems.append(elem['id'])
                id = str(elem['id'])
                os.mkdir(os.path.join(path,id))
                
                #Download attachements
                for attach in elem['extensions']['attachment']:
                    fid = attach['id']
                    #http://iproekt.nextgis.com/api/resource/638/feature/1/attachment/180/download
                    p = requests.get("http://%s.nextgis.com/api/resource/%s/feature/%s/attachment/%s/download" % (url, layer_id, elem['id'], fid), auth = AUTH)
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
    if not args.zip:
        output_zip = 'output.zip'
    else:
        output_zip = args.zip
    generate_zip(args.url, args.login, args.password, args.layer_id, output_zip)

