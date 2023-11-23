# resource2archive
Download nextgis.com resource with all attachments as one ZIP file

    python getfullresource.py --url demo --login guest --password guest --layer_id 4248 --zip c:/temp/output.zip
    
or to get output.zip where script is ran (permissions are ok):

    python getfullresource.py --url demo --layer_id 4248

Works under Python 3.x

Params:

    * url - subdomain name of your Web GIS url. If your Web GIS is example.nextgis.com use 'example' here.
    * layer_id - resource ID of a vector layer that needs to be downloaded
    
    
For reverse operation, see attach2resource repo https://github.com/nextgis/attach2resource
