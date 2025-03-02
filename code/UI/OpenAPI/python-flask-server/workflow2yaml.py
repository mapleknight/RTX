#!/usr/bin/python3
import sys
def eprint(*args, **kwargs): print(*args, file=sys.stderr, **kwargs)

import os
import sys
import re
import json
import requests
import json
import yaml



############################################ Main ############################################################
def main():

    #### Parse command line options
    import argparse
    argparser = argparse.ArgumentParser(description='Fetch and convert the latest workflow operations definitions and convert to YAML')
    argparser.add_argument('--verbose', action='count', help='If set, print more information about ongoing processing' )
    params = argparser.parse_args()

    response_content = requests.get('https://raw.githubusercontent.com/NCATSTranslator/OperationsAndWorkflows/main/schema/operation.json', headers={'accept': 'application/json'})
    status_code = response_content.status_code

    if status_code != 200:
        eprint("Cannot fetch operation.json")
        return

    #### Unpack the response content into a dict
    try:
        response_dict = response_content.json()
    except:
        eprint("Cannot decode request response")
        return

    response_dict['components'] = {}
    response_dict['components']['schemas'] = response_dict['$defs']
    del response_dict['$defs']
    
    # replace $def with components/schemas for all of this list items in anyOf
    response_dict['anyOf'] = [{'$ref': x['$ref'].replace('$defs','components/schemas')} for x in response_dict['anyOf']]
    print(yaml.dump(response_dict))

    return


if __name__ == "__main__": main()
