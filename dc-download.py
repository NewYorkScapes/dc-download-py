#!/usr/bin/env python

import argparse
import os
import requests
import json
import time

def parse_argument():
    parser = argparse.ArgumentParser(prog='python dc-download.py', usage='%(prog)s [-h] [-t <api-token>] [-o <path>] [-f <filename>] [-s <size>] [-u <uuid-of-item>]',
                        description='A Python version of the NYPL dc-download Image Downloader (see https://github.com/nypl-spacetime/dc-download'
                        )
    parser.add_argument('-t', '--token', action='store', required=True, help='Digital Collections API access token, see http://api.repo.nypl.org/')
    parser.add_argument('-s', '--size', action='store', default='b', choices=['b','f','t','r','w','q','v','g','T'], help="""
    
    size/type of images to be downloaded - see below (default is 'b', thumbnail).
    
        b - .jpeg center cropped thumbnail (100x100 pixels)
        f - .jpeg (140 pixels tall with variable width)
        t - .gif (150 pixels on the long side). Not currently an option.
        r - .jpeg (300 pixels on the long side)
        w - .jpeg (760 pixels on the long side)
        q - .jpeg (1600 pixels on the long side)
        v - .jpeg (2560 pixels on the long side)
        g - .jpeg original dimensions
        T - tiff/sull size. Not currently an option.
    
    Examples:
    'piu' will yield "<pageNum>.<imageId>.<uuid>.jpg"
    'u' will yield "<uuid>.jpeg"
    """)
    parser.add_argument('-f', '--filename', action='store', default='piu', help='fields to be used as filename for downloaded files - see below (default is "piu")')
    parser.add_argument('-o', '--output', action='store', default='', help='output directory (default is current directory)')
    parser.add_argument('-u', '--uuid', action='store', required=True, help='uuid of the item whose captures will be downloaded')

    return parser.parse_args()


def make_filename(size_letters, derivative, sort_num, capture_num, capture_uuid):
    file_components = [None, None, None]
    if 'p' in size_letters:
        file_components[0] = sort_num
    if 'i' in size_letters:
        file_components[1] = capture_num
    if 'u' in size_letters:
        file_components[2] = capture_uuid
    filename = '.'.join([i for i in [sort_num, capture_num, capture_uuid] if i is not None])
    ext = '.jpeg' if derivative != 'T' else '.tif'
    return filename + ext

class CaptureUrls:

    def __init__(self, item_uuid, auth_token):
        self.list_image_urls = []
        auth = 'Token token=' + auth_token
        tries = 0
        page = 1
        while tries < 4:
            try:
                captures_r = requests.get('http://api.repo.nypl.org/api/v1/items/' + item_uuid + '?page=' + str(page) + '&per_page=200', headers={'Authorization': auth})
                if captures_r.status_code == 200:
                    captures_json = json.loads(captures_r.text)
                    self.list_image_urls += [(i['imageID'], i['uuid'], i['sortString'].split('|')[-1][7:]) for i in
                                            captures_json['nyplAPI']['response']['capture']]

                    # Check to see if pagination needed to continue grabbing results

                    if int(captures_json['nyplAPI']['response']['numResults']) > 200:
                        page+=1

                    else:
                        tries = 4

                    # Check to see if we've reached the final page, meaning number of results less than page size; if so we are done

                    if (page - 1) * 200 > int(captures_json['nyplAPI']['response']['numResults']):
                        tries = 4
                else:
                    print("Initial API response failure...")
                    if tries == 4:
                        print("Failure to receive needed API request (latest http code of {})".format(captures_r.status_code))
                    else:
                        time.sleep(4)
                        tries+=1
            except:
                print("Initial API response failure...")
                time.sleep(4)
                tries+=1

class CapturePull:

    def __init__(self, capture_num, capture_uuid, sort_num, derivative, output_directory, auth_token):
        auth = 'Token token=' + auth_token
        tries = 0
        while tries < 4:
            try:
                captures_stream = requests.get(
                   'http://images.nypl.org/index.php?id=' + capture_num + '&t=' + derivative,
                   headers={'Authorization': auth})
                if captures_stream.status_code == 200:
                    print("Downloading image ", capture_num)
                    filename = make_filename(args.filename, derivative, sort_num, capture_num, capture_uuid)
                    with open(os.path.join(output_directory, filename), 'wb') as f:
                       f.write(captures_stream.content)
                    f.close()
                    tries = 4
                else:
                    print("API response failure in retrieving image capture. Trying again.")
                    if tries == 4:
                        print("Failure to receive needed API request (latest http code of {})".format(captures_r.status_code))
                    else:
                        time.sleep(4)
                        tries+=1
            except:
                print("API response failure in retrieving image capture. Trying again.")
                time.sleep(4)
                tries+=1



if __name__ == "__main__":
    args = parse_argument()
    capture_list = CaptureUrls(args.uuid, args.token)
    capture_puller = [CapturePull(capture_rec[0], capture_rec[1], capture_rec[2], args.size, args.output,
                     args.token) for capture_rec in capture_list.list_image_urls]
    print("Process complete.")