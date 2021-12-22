from typing import Dict
# Put custom methods for unpacking json files into this file.

def remove_html_tags(xml):
    # find location of each < and >
    start = xml.find('<')
    end = xml.find('>')
    while start != -1 and end != -1:
        xml = xml[:start] + ' ' + xml[end+1:]
        start = xml.find('<')
        end = xml.find('>')

def json_unpack(contents:Dict):
    text = ''
    for entry in contents['data']:
        text += entry.get('title') + ' '
        xml = entry.get('songxml')
        xml = remove_html_tags(xml)
    return text
