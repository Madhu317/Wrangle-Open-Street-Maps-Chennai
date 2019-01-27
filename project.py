#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json
from collections import defaultdict

"""
The output should be a list of dictionaries in for following format:
{
"id": "2406124091",
"type: "node",
"visible":"true",
"created": {
          "version":"2",
          "changeset":"17206049",
          "timestamp":"2013-08-03T16:43:42Z",
          "user":"linuxUser16",
          "uid":"1219059"
        },
"pos": [41.9757030, -87.6921867],
"address": {
          "housenumber": "5157",
          "postcode": "60625",
          "street": "North Lincoln Ave"
        },
"amenity": "restaurant",
"cuisine": "mexican",
"name": "La Cabana De Don Luis",
"phone": "1 (773)-271-5176"
}
    <tag k="addr:housenumber" v="5158"/>
    <tag k="addr:street" v="North Lincoln Avenue"/>
    <tag k="addr:street:name" v="Lincoln"/>
    <tag k="addr:street:prefix" v="North"/>
    <tag k="addr:street:type" v="Avenue"/>
    <tag k="amenity" v="pharmacy"/>
"tags" should be formatted into:
{...
"address": {
    "housenumber": 5158,
    "street": "North Lincoln Avenue"
}
"amenity": "pharmacy",
...
}
    <nd ref="305896090"/>
    <nd ref="1719825889"/>
"way" should appear as:
{...
"node_refs": ["305896090", "1719825889"]
...
}
"""
# REGEX for cleaning 

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)



# Update street names 

def update_street(street_name):
    street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
    expected = ["Street", "Avenue", "Nagar", "Road", "Salai"]
    mapping  = { "St": "Street",
                    "St.": "Street",
                    "street":"Street",
                    "strret":"Street",
                    "ROAD":"Road",
                    "Rd":"Road",
                    "rd":"Road",
                    "road": "Road",
                    "nagar": "Nagar",
                    "NAGAR":"Nagar",
                    "Ave":"Avenue",
                    "Ave.":"Avenue",
                    "av": "Avenue",
                    "ave": "Avenue",
                    "avenue" : "Avenue",
                    }

    Street_type=re.search(street_type_re,street_name)
    
    if Street_type:
        r=Street_type.group()
        if r  in mapping.keys():
            update_street_name=re.sub(street_type_re,mapping[Street_type.group()],street_name)
            
        else:
            update_street_name=street_name
        return update_street_name

# Update postal codes

def update_postal(postcode):
    if postcode.isdigit():
        return postcode
    elif re.findall("\.",postcode):
        return postcode.replace(" ","").replace(".","")
    else:   
        return postcode.replace(" ","")

# Shape function to get the required dictionaries 

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

def shape_element(element):

    ref=[]
    address={}
    node = {}
    temp=[0,0]
    
# process only node and way tags, add elements in CREATED araay into created, add lat and long into pos 

    if element.tag=="node" or element.tag == "way" :

        data=element.attrib
        node["created"]={i:data[i] for i in CREATED}

        for key,value in data.items():

                if key=="lat":
                    lat=float(data[key])
                    temp[0]=lat

                elif key=="lon":
                    lon=float(data[key])
                    temp[1]=lon

                elif key not in CREATED:
                    node[key]=data[key]
                    
        node["type"]=element.tag
        node["pos"]=temp
        
# update the street and postal codes in the data before creating JSON files 

        for elem in element:

            if elem.tag=="tag" or elem.tag=="nd" :
                datattrib=elem.attrib

                for key, value in datattrib.items():
                    if key=='k':
                        
                        if re.search(problemchars,value):
                            continue

                        if re.search(lower_colon,value):

                            if value=='addr:street':

                                address["street"]=update_street(elem.attrib['v'])

                            else:
                                try:

                                    m=re.search("(?<=addr:)\w+",value)
                                    k=m.group(0)
                                    address[k]=datattrib['v']

                                except :
                                    pass

                        if re.search(lower,value):

                            node[value]=datattrib['v']
                        node["address"]=address

                    elif key=="ref":
                         ref.append(value)
        

        if ref:
            node["node_refs"]=ref

        try:
            if node["address"]=={}:
                del node["address"]

        except:

            pass

        return node

    else:

        return None

#Create JSON file 

def process_map(file_in, pretty=False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w",encoding="utf8") as fo:
        for event, element in ET.iterparse(file_in):
            el = shape_element(element)
            
            if el:
                data.append(el)
                #print (data)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data
    


def test():
    # call the process_map procedure with pretty=False. The pretty=True option adds
    # additional spaces to the output, making it significantly larger.
    data = process_map('chennai_sample.osm', False)
    # pprint.pprint(data)


if __name__ == "__main__":
    test()