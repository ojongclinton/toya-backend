from payments.payment import PaymentProcess
from payments.payments.smobilepay.error_message import ERROR_CODES, SUCCESS_MESSAGE
from .s3_api_auth import S3ApiAuth
from dotenv import load_dotenv 
import os 
import json
import logging

logger = logging.getLogger(__name__)


load_dotenv()
BASE_API_URL = os.getenv('BASE_API_URL')
S3P_KEY = os.getenv('S3P_KEY')
S3P_SECRET = os.getenv('S3P_SECRET')

class S3CashOutManager: 
    def __init__(self):
        pass 

    def check_phone_number_validite(self, phone_number): 
        pass 

    def get_all_available_service(self):    
        API_URL= BASE_API_URL+'cashout'
        api_auth = S3ApiAuth(api_url=API_URL, public_token=S3P_KEY, secret_key=S3P_SECRET)

        response = api_auth.make_request(method="GET")
        return response.status_code ,  response.text

    def get_service_information(self, merchant): 

        API_URL = BASE_API_URL + 'cashout'
        
        api_auth = S3ApiAuth(api_url=API_URL, public_token=S3P_KEY, secret_key=S3P_SECRET)

        response = api_auth.make_request(method="GET")

        
        if response.status_code == 200:
            services = json.loads(response.text)
            
            for service in services:
                if merchant == 'mtn_money' and service['merchant'] == 'CMMTNMOMOCC':
                    return service['serviceid'], service['payItemId']
                elif merchant == 'orange_money' and service['merchant'] == 'CMORANGEOMCC':
                    return service['serviceid'], service['payItemId']
            
            return None, None
        else:
            return None , None
        

    
    def initiateTransaction(self , payItemId, amount): 
        API_URL = BASE_API_URL + 'quotestd'
        
        api_auth = S3ApiAuth(api_url=API_URL, public_token=S3P_KEY, secret_key=S3P_SECRET)

        payload = {
            "amount": amount, 
            "payItemId": payItemId,
        }

        response = api_auth.make_request(method="POST", payload=payload)

        # Handle error responses (dict with 'error' key)
        if isinstance(response, dict) and 'error' in response:
            logger.error(f"Quote request failed: {response.get('error')}")
            return None, None
        
        # Handle successful HTTP response
        try:
            if response.status_code == 200:
                response_data = json.loads(response.text) 
                quoteId = response_data.get('quoteId')
                return quoteId, response_data
            else:
                logger.error(f"Quote request non-200 status: {response.status_code}")
                return None, None
        except AttributeError as e:
            logger.error(f"Unexpected response type in initiateTransaction: {type(response)}")
            return None, None
    

    
    def processTransactionWithCollectStd(self ,quoteId , serviceNumber, transactionId): 
        API_URL = BASE_API_URL + 'collectstd'
        
        api_auth = S3ApiAuth(api_url=API_URL, public_token=S3P_KEY, secret_key=S3P_SECRET)
        serviceNumber = serviceNumber.replace('+','')
        payload = {
            "quoteId": quoteId,
            "customerPhonenumber": "237653754334",
            "customerEmailaddress": "devert@test.com",
            "customerName": "Devert",
            "customerAddress": "Mambanda Bonaberi",
            "serviceNumber": serviceNumber,
            "trid": transactionId
        }

        response = api_auth.make_request(method="POST", payload=payload)
        
        # Handle error responses (dict with 'error' key)
        if isinstance(response, dict) and 'error' in response:
            logger.error(f"API request failed: {response.get('error')}")
            if 'response_body' in response:
                logger.error(f"API error response body: {response.get('response_body')}")
            return None, None
        
        # Handle successful HTTP response
        try:
            logger.info(f"collectstd request payload: {payload}")
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            
            if response.status_code == 200:
                response_data = json.loads(response.text)
                # collectstd returns PTN, not quoteId
                ptn = response_data.get('ptn')
                logger.info(f"Payment collection initiated successfully. PTN: {ptn}")
                return ptn, response_data
            else:
                logger.error(f"Non-200 status code: {response.status_code}")
                return None, None
        except AttributeError as e:
            logger.error(f"Unexpected response type: {type(response)}, value: {response}")
            return None, None
        




    def checkTransactionStatus(self, transactionId):
        API_URL = BASE_API_URL + f'verifytx'
        params = {'trid': transactionId}
        api_auth = S3ApiAuth(api_url=API_URL, public_token=S3P_KEY, secret_key=S3P_SECRET)

        logger.info(f"Checking transaction status for {transactionId}")
        logger.info(f"API URL: {API_URL}")
        logger.info(f"Request params: {params}")

        response = api_auth.make_request(method="GET", additional_params=params)
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response body: {response.text}")

        try:
            response_data = json.loads(response.text)
            logger.info(f"Received response: {response_data}")
        except json.JSONDecodeError:
            logger.error("Failed to decode the response JSON.")
            return {
                'status': 'FAILED',
                'message': {
                    "fr": {
                        'message_fr': "Impossible de traiter la réponse",
                        'solution_fr': "Contactez le support pour plus de détails"
                    },
                    "en": {
                        'message_en': "Unable to process response",
                        'solution_en': "Contact support for details"
                    }
                }
            }

        if response_data:
            # Handle both array and single object responses
            # When using 'trid', API returns single object
            # When using 'ptn', API returns array
            if isinstance(response_data, list):
                if len(response_data) == 0:
                    logger.error(f"Empty response array for transaction {transactionId}")
                    return {
                        'status': 'FAILED',
                        'message': {
                            "fr": {
                                'message_fr': "Aucune donnée de transaction trouvée",
                                'solution_fr': "Contactez le support"
                            },
                            "en": {
                                'message_en': "No transaction data found",
                                'solution_en': "Contact support"
                            }
                        }
                    }
                transaction_info = response_data[0]
            else:
                # Single object response (when using trid)
                transaction_info = response_data
            
            status = transaction_info.get('status', 'UNKNOWN')

            logger.info(f"Transaction status: {status}")

            payment_process = PaymentProcess()

            if status == 'SUCCESS':
                payment_process.launch_process('SUCCESS', transactionId)
                logger.info(f"Payment successful for transaction {transactionId}")
                return {
                    'status': status,
                    'message': {
                        "fr": {
                            'message_fr': SUCCESS_MESSAGE["fr"],
                            'solution_fr': SUCCESS_MESSAGE["fr"]
                        },
                        "en": {
                            'message_en': SUCCESS_MESSAGE["en"],
                            'solution_en': SUCCESS_MESSAGE["en"]
                        }
                    }
                }

            if status == 'PENDING':
                payment_process.launch_process('PENDING', transactionId)
                logger.info(f"Payment is pending for transaction {transactionId}")
                return {
                    'status': status,
                    'message': {
                        "fr": {
                            'message_fr': "Transaction en cours de traitement", 
                            'solution_fr': "Votre transaction est en traitement, merci de patienter."
                        },
                        "en": {
                            'message_en': "Transaction in process",
                            'solution_en': "Your transaction is being processed, please wait."
                        }
                    }
                }

            error_code = transaction_info.get('errorCode')
            if error_code:
                logger.error(f"Error code {error_code} for transaction {transactionId}")
                error_message = ERROR_CODES.get(error_code, ERROR_CODES["default"])
                
                solution_fr = error_message.get("solution", {}).get("fr", "")
                solution_en = error_message.get("solution", {}).get("en", "")
                
                # Lancer le processus de paiement
                payment_process.launch_process(status, transactionId)
                
                return {
                    'status': status,
                    'message': {
                        "fr": {
                            'message_fr': error_message["fr"],
                            'solution_fr': solution_fr
                        },
                        "en": {
                            'message_en': error_message["en"],
                            'solution_en': solution_en
                        }
                    }
                }

            else:
                logger.error(f"Transaction failed with no specific error code for {transactionId}")
                payment_process.launch_process('FAILED', transactionId)
                return {
                    'status': 'FAILED',
                    'message': {
                        "fr": {
                            'message_fr': "Transaction failed, but no specific error code returned",
                            'solution_fr': "Contactez le support pour plus de détails"
                        },
                        "en": {
                            'message_en': "Transaction failed, but no specific error code returned",
                            'solution_en': "Contact support for details"
                        }
                    }
                }

        else:
            logger.error(f"No transaction data found for {transactionId}")
            payment_process.launch_process('FAILED', transactionId)
            return {
                'status': 'FAILED',
                'message': {
                    "fr": {
                        'message_fr': "No transaction data found",
                        'solution_fr': "Contactez le support pour plus de détails"
                    },
                    "en": {
                        'message_en': "No transaction data found",
                        'solution_en': "Contact support for details"
                    }
                }
            }
