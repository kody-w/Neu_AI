from skills.basic_skill import BasicSkill
from langchain.tools import StructuredTool
import requests

class ExchangeRateSkill(BasicSkill):
    def __init__(self):
        self.name = "ExchangeRate"
        self.metadata = {
            "name": self.name,
            "description": "Get the current exchange rate of a base currency and target currency",
            "parameters": {
                "type": "object",
                "properties": {
                    "base_currency": {
                        "type": "string",
                        "description": "The base currency for exchange rate calculations, i.e. USD, EUR, RUB",
                    },
                    "target_currency": {
                        "type": "string", 
                        "description": "The target currency for exchange rate calculations, i.e. USD, EUR, RUB"
                    },
                    "date": {
                        "type": "string", 
                        "description": "A specific day to reference, in YYYY-MM-DD format. Defaults to 'latest' if not provided."
                    },
                },
                "required": ["base_currency", "target_currency"],
            }
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, base_currency: str, target_currency: str, date: str = "latest") -> str:
        """
        Get the exchange rate between two currencies.

        Args:
            base_currency (str): The base currency for exchange rate calculations.
            target_currency (str): The target currency for exchange rate calculations.
            date (str, optional): A specific day to reference, in YYYY-MM-DD format. Defaults to "latest".

        Returns:
            str: The exchange rate or an error message.
        """
        try:
            url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date}/v1/currencies/{base_currency.lower()}.json"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                rate = data.get(base_currency.lower(), {}).get(target_currency.lower())
                if rate is not None:
                    return f"The exchange rate from {base_currency.upper()} to {target_currency.upper()} is {rate}"
                else:
                    return f"Could not find exchange rate for {base_currency.upper()} to {target_currency.upper()}"
            else:
                return f"Failed to fetch exchange rate: HTTP {response.status_code}"
        except Exception as e:
            return f"An error occurred while fetching the exchange rate: {str(e)}"