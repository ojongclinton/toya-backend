import os
import hmac
import hashlib
import base64
from urllib import parse
import secrets
import time
import requests
import uuid
import json

class HMACSignature:
    def __init__(self, method, url, params):
        self.method = method
        self.url = url
        self.params = params

    def generate(self, secret):
        signature_raw = hmac.new(secret.encode(), self.get_base_string().encode(), hashlib.sha1).digest()
        return base64.b64encode(signature_raw).decode()

    def get_base_string(self):
        glue = '&'
        sorted_params = sorted(self.params.items())
        parameter_string = "&".join(f"{key}={str(value)}" for key, value in sorted_params)
        return f"{self.method.upper()}{glue}{parse.quote(self.url, safe='-')}{glue}{parse.quote(parameter_string, safe='-')}"

class S3ApiAuth:
    def __init__(self, api_url, public_token, secret_key):
        self.api_url = api_url
        self.public_token = public_token
        self.secret_key = secret_key
        self.debug = os.getenv('SMOBIL_PAY_API_DEBUG', 'False') == 'True'

    def timestamp(self):
        timestamp = str(int(time.time()))
        return timestamp

    def create_authorization_header(self, method, additional_params=None):
        nonce = self.timestamp()
        timestamp = self.timestamp()
        parameters = {
            's3pAuth_nonce': nonce,
            's3pAuth_signature_method': "HMAC-SHA1",
            's3pAuth_timestamp': timestamp,
            's3pAuth_token': self.public_token,
            **(additional_params if additional_params else {})
        }
        signature_helper = HMACSignature(method, self.api_url, parameters)
        signature = signature_helper.generate(self.secret_key)
        auth_header = (
            f's3pAuth, s3pAuth_nonce="{nonce}", s3pAuth_signature="{signature}", '
            f's3pAuth_signature_method="HMAC-SHA1", s3pAuth_timestamp="{timestamp}", '
            f's3pAuth_token="{self.public_token}"'
        )
        return auth_header
        

    def make_request(self, method, additional_params=None, payload=None, version="3.0.0", timeout=45):
        headers = {
            'Authorization': self.create_authorization_header(method, payload if method.upper() == "POST" else additional_params),
            'x-api-version': version,
            'Content-Type': 'application/json'  
        }

        try:
            if method.upper() == "POST":
                response = requests.request(method, self.api_url, headers=headers, data=json.dumps(payload), timeout=timeout)
            elif method.upper() == "GET":
                response = requests.request(method, self.api_url, headers=headers, params=additional_params, timeout=timeout)
            else:
                return {'error': 'Unsupported HTTP method'}

            # Check status and capture error body before raising
            if response.status_code >= 400:
                error_body = response.text
                return {
                    'error': f'{response.status_code} Client Error: {response.reason} for url: {response.url}',
                    'status_code': response.status_code,
                    'response_body': error_body
                }
            
            return response
            
        except requests.Timeout:
            return {'error': 'Request timeout - payment may still be processing'}
        except Exception as err:
            return {'error': str(err)}





