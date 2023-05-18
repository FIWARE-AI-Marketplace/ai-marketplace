#! /usr/local/bin/python3

#
# Fecthes data from Context Broker protected by PEP/PDP via i4Trust data space.
# 

import sys
import os
import re
import jwt  # pip3 install pyjwt
import json
import requests # pip3 install requests
from requests.exceptions import HTTPError
import uuid
import time

ENTITY_TYPE = "CarStatusMonitoring"

KEY_FILE = "../certs/autosupplier.key.pem"
CERT_FILE = "../certs/autosupplier.ca-chain.cert.pem"
EORI = "EU.EORI.DEAUTOSUPPLIER"
PROVIDER_URL = "https://hella-kong-kong-kim-main.apps.fiware.fiware.dev/diagnosis-i4trust/ngsi-ld/v1"
PROVIDER_TOKEN_URL = "https://hella-keyrock-0-kim-main.apps.fiware.fiware.dev/oauth2/token"
PROVIDER_EORI = "EU.EORI.DEHELLA"

CARDEALER_KEY_FILE = "../certs/cardealer.key.pem"
CARDEALER_CERT_FILE = "../certs/cardealer.ca-chain.cert.pem"
CARDEALER_EORI = "EU.EORI.DECARDEALER"

def build_token(params):
    def getCAChain(cert):

        sp = cert.split('-----BEGIN CERTIFICATE-----\n')
        sp = sp[1:]

        ca_chain = []
        for ca in sp:
            ca_sp = ca.split('\n-----END CERTIFICATE-----')
            ca_chain.append(ca_sp[0])

        return ca_chain

    iat = int(str(time.time()).split('.')[0])
    exp = iat + 30

    token = {
        "jti": str(uuid.uuid4()),
        "iss": params['client_id'],
        "sub": params['client_id'],
        "aud": [
            params['provider_id'],
            params['token_endpoint']
        ],
        "iat": iat,
        "nbf": iat,
        "exp": exp
    }

    with open(params['key'], 'r') as key:
        private_key = key.read()
        
    with open(params['cert'], 'r') as cert:
        ca_chain = getCAChain(cert.read())

    return jwt.encode(token, private_key, algorithm="RS256", headers={
        'x5c': ca_chain
    })

def main():
    global EORI, KEY_FILE, CERT_FILE, PROVIDER_EORI, ENTITY_TYPE
    
    # Check length of args
    # Should be at least 1 (namespace)
    args = sys.argv[1:]
    if len(args) < 1:
        print("ERROR: Provide at least the namespace as argument")
        print("Usage: python get_data_m2m_i4Trust.py <NAMESPACE> <PARTY> <OPERATION>")
        print("   NAMESPACE: The namespace where components have been deployed, e.g., kim-poc")
        print("   PARTY: The consuming party of the data space, e.g., autosupplier or cardealer (optional, default: autosupplier)")
        print("   OPERATION: Type of operation, GET or POST (optional, default: GET)")
        sys.exit(2)

    # Get namespace
    namespace = args[0]
    print("Target namespace: " + namespace)
    target_url = PROVIDER_URL.replace("kim-main", namespace)
    token_url = PROVIDER_TOKEN_URL.replace("kim-main", namespace)
    
    print("Service Provider Target URL: " + target_url)

    # Get party if specified
    if len(args) > 1:
        party = args[1]
        if party == "cardealer":
            KEY_FILE = CARDEALER_KEY_FILE
            CERT_FILE = CARDEALER_CERT_FILE
            EORI = CARDEALER_EORI
            print("Consuming party set to: " + party)
        elif party == "autosupplier":
            # Do nothing, everything set
            print("Consuming party set to: " + party)
        else:
            print("Unknown consuming party: " + party)
            sys.exit(3)

    # Get operation if specified
    operation = "GET"
    if len(args) > 2:
        operation = args[2].upper()
    if operation not in ["GET", "POST"]:
        print("Unknown operation specified: " + operation)
        
            
    print("EORI of consuming party: " + EORI)
    print("Using key/cert files:")
    print("  KEY: " + KEY_FILE)
    print("  CERT: " + CERT_FILE)
    print("Operation: " + operation)
    
    # Generate iSHARE JWT of consumer
    token = build_token({
        'client_id': EORI,
        'provider_id': PROVIDER_EORI,
        'key': KEY_FILE,
        'cert': CERT_FILE,
        'token_endpoint': token_url
    })

    # Retrieve access token from provider
    #grant_type = 'client_credentials'
    grant_type = 'urn:ietf:params:oauth:grant-type:jwt-bearer'
    auth_params = {
        'grant_type': grant_type,
        'scope': 'iSHARE',
        'client_id': EORI,
        'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
        'client_assertion': token
    }
    print(" ")
    print("==========================")
    print("Getting access token from " + token_url)
    response = requests.post(token_url, data=auth_params)
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
    print("Received access_token (decoded):")
    access_token_decoded = jwt.decode(access_token, options={"verify_signature": False})
    print(json.dumps(access_token_decoded, indent=4, sort_keys=True))
    
    # Get data from Context Broker
    if operation == "GET":
        target_url = target_url + "/entities"
        print(" ")
        print("==========================")
        print("Getting entities of type " + ENTITY_TYPE)
        print("Sending request: GET " + target_url)
        params = {
            'type': ENTITY_TYPE,
            'options': 'keyValues'
        }
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Accept': 'application/json'
        }
        print("Parameters:")
        print(json.dumps(params, indent=4, sort_keys=True))
        response = requests.get(target_url, params=params, headers=headers) #, verify=False)
        print("-----------------------------")
        print("Response:")
        try:
            response.raise_for_status()
        except HTTPError as e:
            print(e)
            print(response.json())
            sys.exit(4)
        response_data = response.json()
        print(json.dumps(response_data, indent=4, sort_keys=True))
    elif operation == "POST":
        target_url = target_url + "/entities"
        print(" ")
        print("==========================")
        print("Create entity of type " + ENTITY_TYPE)
        print("Sending request: POST " + target_url)
        body = {
            "id": "urn:ngsi-ld:CarStatusMonitoring:ID003",
            "param1": "val1",
            "param2": "val2",
            "type": "CarStatusMonitoring"
        }
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Accept': 'application/json'
        }
        print("Body:")
        print(json.dumps(body, indent=4, sort_keys=True))
        response = requests.post(target_url, json=body, headers=headers) #, verify=False)
        print("-----------------------------")
        print("Response:")
        try:
            response.raise_for_status()
        except HTTPError as e:
            print(e)
            print(response.json())
            sys.exit(4)
        response_data = response.json()
        print(json.dumps(response_data, indent=4, sort_keys=True))
    

if __name__ == "__main__":
    main()
