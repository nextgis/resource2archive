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
from datetime import datetime
import six,string

valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)

#python getfullresource.py --url demo --login test --password testtest --layer_id 4248 --zip output.zip


#TODO make sanitize an argument?

parser = argparse.ArgumentParser()
parser.add_argument('--url',type=str,required=True)
parser.add_argument('--login',type=str,default='administrator')
parser.add_argument('--password',type=str)
parser.add_argument('--layer_id',type=str,required=True)
parser.add_argument('--zip',type=str)

args = parser.parse_args()

def sanitize(attach_name):
    name = ''.join(c for c in attach_name if c in valid_chars)

    return name

def generate_zip(path, url, login, password, layer_id, output_zip): 
    elems = []
    if args.login and args.password:
        AUTH = HTTPBasicAuth(login, password)
    else:
        AUTH = ''
    resource_url = 'https://%s.nextgis.com/api/resource/%s' %(url, layer_id)
    resource = requests.get(resource_url, auth = AUTH).json()
    
    if 'exception' not in resource.keys():
        if resource['resource']['cls'] == 'vector_layer' or resource['resource']['cls'] == 'postgis_layer':
            print ('Downloading structure...')
            data = requests.get(resource_url + '/geojson', auth = AUTH).json()
            
            features = requests.get(resource_url + '/feature/', auth = AUTH).json()

            try:
                keys = features.keys()
            except:
                keys = features[0].keys()

            if 'exception' not in keys:
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
                    items = []
                    for item in attachments[el]:
                        item = sanitize(item)
                        items.append(item)

                    data["features"][el]["properties"]["attachments"] = items
                
                geojson_filename = '%s.geojson' %(resource['resource']['display_name'])
                geojson_filenamefull = os.path.join(path,geojson_filename)
                with open(geojson_filenamefull, 'w') as gj:
                    gj.write(json.dumps(data))
                
                with zipfile.ZipFile(output_zip, 'w', allowZip64 = True) as z:
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
                            
                            #Download attachments
                            for attach in elem['extensions']['attachment']:
                                fid = attach['id']
                                #https://demo.nextgis.com/api/resource/4248/feature/1/attachment/42/download
                                link = 'https://%s.nextgis.com/api/resource/%s/feature/%s/attachment/%s/download' % (url, layer_id, elem['id'], fid)
                                p = requests.get(link, auth = AUTH)
                                attach_name = six.ensure_str(attach['name'])
                                attach_name = sanitize(attach_name)
                                with open(os.path.join(path,id,attach_name), 'wb') as out:
                                    out.write(p.content)
                            directories = os.listdir(os.path.join(path,id))
                            for d in directories:
                                #print(d)
                                z.write(os.path.join(path,id,d),os.path.join(id,d))
                            pbar.update(1)
                    z.close() 
                    pbar.close()
            else:
                print('HTTP error %s. Invalid request or problems with the server.' % features['status_code'])
            #Clean up folders
            for el in elems:
                shutil.rmtree(os.path.join(path,str(el)), ignore_errors = True)
        else:
            print('Resource %s is not a vector layer' % layer_id)
    else:
        print('Resource %s does not exist' % layer_id)
        
if __name__ == '__main__':
    if not args.zip:
        output_zip = 'output.zip'
    else:
        output_zip = args.zip
    
    dt = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_name = args.url + '_' + dt + '_' + next(tempfile._get_candidate_names())
    path = os.path.join(tempfile.gettempdir(),temp_name)
    os.mkdir(path)

    generate_zip(path, args.url, args.login, args.password, args.layer_id, output_zip)
    shutil.rmtree(path)

