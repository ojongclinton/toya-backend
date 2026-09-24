# clients/tasks.py
from celery import shared_task
import logging
import re

from core.sms.service import SMSClient

logger = logging.getLogger(__name__)


@shared_task
def notifiy_new_user_with_sms_tasks(phone_number, message):
    """
    Send an SMS via Celery using SMSClient.

    - Preserves/normalizes E.164 format expected by the provider (e.g. "+2376XXXXXXXX").
    - Validates phone number and credentials before sending.
    - Logs provider responses and errors for observability in worker logs.
    """
    try:
        original_number = str(phone_number).strip()

        # TODO: Update this logic to handle more phone number formats
        #  Normalize to +2376XXXXXXXX if common variants are provided
        # Acceptable patterns we convert:
        #  - "2376XXXXXXXX" -> "+2376XXXXXXXX"
        #  - "6XXXXXXXX" (9 digits starting with 6) -> "+2376XXXXXXXX"
        #  - "+2376XXXXXXXX" -> keep as is
        normalized = original_number
        if re.fullmatch(r"2376\d{8}", normalized):
            normalized = "+" + normalized
        elif re.fullmatch(r"6\d{8}", normalized):
            normalized = "+237" + normalized
        elif re.fullmatch(r"\+2376\d{8}", normalized):
            # Already in correct format
            pass

        # Validate final format
        pattern = r"^\+2376\d{8}$"
        if not re.match(pattern, normalized):
            logger.error("[SMS Task] Invalid phone number format after normalization: %s (original: %s)", normalized, original_number)
            return {"status": "error", "reason": "invalid_phone_format", "phone": original_number}

        sms_client = SMSClient()

        # Ensure credentials are present in the worker environment
        if not all([sms_client.user, sms_client.password, sms_client.sender_id]):
            logger.error("[SMS Task] Missing SMS credentials in worker environment. user=%s sender_id=%s", bool(sms_client.user), bool(sms_client.sender_id))
            return {"status": "error", "reason": "missing_credentials"}

        response = sms_client.send_sms(message=message, mobile_number=normalized)

        if response is None:
            logger.error("[SMS Task] Provider returned no response (None) for %s", normalized)
            return {"status": "error", "reason": "provider_error"}

        logger.info("[SMS Task] SMS sent to %s. Provider response: %s", normalized, response)
        return {"status": "ok", "phone": normalized, "provider_response": response}

    except Exception as e:
        logger.exception("[SMS Task] Unexpected error while sending SMS: %s", str(e))
        return {"status": "error", "reason": "exception", "detail": str(e)}
