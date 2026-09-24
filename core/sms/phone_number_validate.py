import re

class PhoneNumberUtils:

    @staticmethod
    def phone_number_validate(phone_number):
        """
        Valide un numéro Ivoirien (Moov/Orange/MTN) au format +22507xxxxxxxx ou 22507xxxxxxxx
        """
        pattern = r"^\+?225(0|1|5|7)\d{8}$"
        return re.match(pattern, phone_number) is not None

    @staticmethod
    def clean_phone_number(phone_number):
        """
        Nettoie le numéro en supprimant le "+" si présent
        """
        return phone_number.replace("+", "")

    @classmethod
    def validate_and_clean(cls, phone_number):
        cleaned = cls.clean_phone_number(phone_number)
        print("✅ Numéro valide :", cleaned)
        return True, cleaned 