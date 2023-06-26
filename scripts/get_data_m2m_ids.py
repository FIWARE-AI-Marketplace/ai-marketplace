#! /usr/local/bin/python3

#
# Fecthes data from Context Broker protected by Marketplace IDS Connector via IDS data space.
# 

import sys
import os
import re
import json
import requests # pip3 install requests
from requests.exceptions import HTTPError

PROVIDER_URL = "https://hella-kong-kong-kim-main.apps.fiware.fiware.dev/kim/ids-input/ngsi-ld/v1"
PROVIDER_TOKEN_URL = "https://keyrock-0-kim-main.apps.fiware.fiware.dev/oauth2/token"


def main():
    
    # Check length of args
    # Should be exactly 1 (namespace)
    args = sys.argv[1:]
    if len(args) < 1:
        print("ERROR: Provide at least the namespace as argument")
        print("Usage: python get_data_m2m_i4Trust.py <NAMESPACE>")
        print("   NAMESPACE: The namespace where components have been deployed, e.g., kim-poc-02")
        sys.exit(2)

    # Get namespace
    namespace = args[0]
    print("Target namespace: " + namespace)
    target_url = PROVIDER_URL.replace("kim-main", namespace)
    token_url = PROVIDER_TOKEN_URL.replace("kim-main", namespace)
    
    print("Service Provider Target URL: " + target_url)

    # Get operation if specified, POST not allowed in IDS use case
    operation = "GET"
    print("Operation: " + operation)

    username = "operator-local@cardealer.com"
    print("Username: " + username)

    password = "operator"    
    print("Password: " + password)
    
    # Retrieve access token from Marketplace
    headers = {
                "Authorization": "Basic NzEwNDk4OTktYjkxOS00ZDBmLTkzMDMtZTVkMmZkMWJiYjkxOmY3ZTExMjM0LWI4NGYtNDc0OC04NmU1LTEyMzQ1Njc4OThoOA==",
                "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            }
    auth_params = {
                "grant_type": "password",
                "username": username,
                "password": password
    }
    print(" ")
    print("==========================")
    print("Getting access token from " + token_url)
    response = requests.post(token_url, headers=headers, data=auth_params)
    print("-----------------------------")
    try:
        response.raise_for_status()
    except HTTPError as e:
        print("Response:")
        print(e)
        print(response.json())
        sys.exit(4)
    auth_data = response.json()
    if not auth_data['access_token']:
        print("Response:")
        print("ERROR: No access token in response")
        sys.exit(4)
    access_token = auth_data['access_token']
    print("Received access_token: " + access_token)
    
    # Get data from Context Broker
    target_url = target_url + "/entities/urn:ngsi-ld:Analytics:ID999Total"
    print(" ")
    print("==========================")
    print("Sending request: GET " + target_url)
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Forward-To': 'http://www.test.de'
    }
    response = requests.get(target_url, headers=headers) #, verify=False)
    print("-----------------------------")
    print("Response:")
    try:
        response.raise_for_status()
    except HTTPError as e:
        print(e)
    if response.status_code == 200: 
        response_data = response.json()
        print(json.dumps(response_data, indent=4, sort_keys=True))    

if __name__ == "__main__":
    main()

