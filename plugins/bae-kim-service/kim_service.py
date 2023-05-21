# -*- coding: utf-8 -*-

# Copyright (c) 2021 Future Internet Consulting and Development Solutions S.L.

# This file is part of BAE NGSI Dataset plugin.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os
import re
import requests
import random
from requests.exceptions import HTTPError

from django.conf import settings

from wstore.asset_manager.resource_plugins.plugin import Plugin
from wstore.asset_manager.resource_plugins.plugin_error import PluginError

ADMIN_MP_KR_EMAIL = os.getenv('ADMIN_MP_KR_EMAIL', 'admin@test.com')
ADMIN_MP_KR_PW = os.getenv('ADMIN_MP_KR_PW', 'admin')

KEYROCK_BASE_URL = os.getenv('KEYROCK_BASE_URL', 'http://keyrock:8080')
KEYROCK_APP_ID = os.getenv('KEYROCK_APP_ID', '71049899-b919-4d0f-9303-e5d2fd1bbb91')

UNITS = [{
    'name': 'Api call',
    'description': 'The final price is calculated based on the number of calls made to the API'
}]

class KIMService(Plugin):
            
    def on_product_acquisition(self, asset, contract, order):
                
        # Login Keyrock
        auth_body = {
            "name": ADMIN_MP_KR_EMAIL, 
            "password": ADMIN_MP_KR_PW       
        }

        auth_url = KEYROCK_BASE_URL + '/v1/auth/tokens'

        response1 = requests.post(auth_url, json=auth_body)
        response1.raise_for_status()

        auth_token = response1.headers['x-subject-token']        

        
        
        # Create Keyrock role
        create_role_path = '/v1/applications/{}/roles'.format(KEYROCK_APP_ID)
        create_role_url = KEYROCK_BASE_URL + create_role_path

        rnd_number = random.randint(10000, 99999)
        access_role = 'baeRole{}'.format(rnd_number)

        create_role_body = {
            "role": {
                "name": access_role
            }
        }

        response2 = requests.post(create_role_url, headers={'X-Auth-Token': auth_token}, json=create_role_body)
        response2.raise_for_status()

        new_role = response2.json()
        new_role_id = new_role['role']['id']        
                    
        
        # Create Keyrock Permission
        create_permission_path = '/v1/applications/{}/permissions'.format(KEYROCK_APP_ID)
        create_permission_url = KEYROCK_BASE_URL + create_permission_path
        access_permission = 'baePermission{}'.format(access_role)

        action = asset.meta_info['method']
        resource = asset.meta_info['permissionresource']
                        
        create_permission_body = {
          "permission": {
            "name": access_permission,
            "description": "Permission for BAE customers in role {}".format(access_role),
            "action": action,
            "resource": resource,
            "is_regex": False
          }
        }
                        
                
        response3 = requests.post(create_permission_url, headers={'X-Auth-Token': auth_token}, json=create_permission_body)

        response3.raise_for_status()

        
        new_permission = response3.json()
        permission_id = new_permission['permission']['id']
            
            
        
        # Permission to role        
        assign_permission_to_role_url = KEYROCK_BASE_URL + '/v1/applications/{}/roles/{}/permissions/{}'.format(KEYROCK_APP_ID, new_role_id, permission_id)

        resp = requests.put(assign_permission_to_role_url, headers={'X-Auth-Token': auth_token, 'Content-Type': 'application/json'})

        resp.raise_for_status()
        

        
        # User to role
        user_id = 'cardealer-operator-local'

        assign_user_to_role_url = KEYROCK_BASE_URL + '/v1/applications/{}/users/{}/roles/{}'.format(KEYROCK_APP_ID, user_id, new_role_id)
                        
        resp = requests.put(assign_user_to_role_url, headers={'X-Auth-Token': auth_token, 'Content-Type': 'application/json'})

        resp.raise_for_status()

        #### TEST
        response_body = {
            "Ergebnis" : "Role finally attached to User, Success",
            "token" : auth_token,
            "roleID" : new_role_id,
            "path" : create_permission_path,
            "permission" : new_permission,
            "permission_id" : permission_id,
            "assign_permission_to_role_url" : assign_permission_to_role_url,
            "assign_user_to_role_url" : assign_user_to_role_url,
            "KEYROCK_APP_ID" : KEYROCK_APP_ID,
            "user_id" : user_id
        }

        response = requests.post('http://envjjxkl6429c.x.pipedream.net', headers={'X-Auth-Token': auth_token}, json=response_body) 
        
        
        
        # order_data = order.json()
        
        # responseRB9_body = {
        #     "order" : order_data
        # }

        # responseRB9 = requests.post('http://envjjxkl6429c.x.pipedream.net', headers={'X-Auth-Token': auth_token}, json=responseRB9_body) 
                    
    
    def get_usage_specs(self):
        return UNITS

    def get_pending_accounting(self, asset, contract, order):
        return [], None


if __name__ == "__main__":
    plugin = KIMService()
    plugin.on_product_acquisition(None, None, None)
