import os
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from .logging_config import logger

class BinanceClientError(Exception):
    pass

class BinanceTestnetClient:
    BASE_URL = "https://testnet.binancefuture.com"

    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
        
        if not self.api_key or not self.api_secret:
            logger.error("API key and secret must be provided or set in environment variables.")
            raise BinanceClientError("API credentials missing. Please set BINANCE_API_KEY and BINANCE_API_SECRET.")
            
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        })
        logger.info("BinanceTestnetClient initialized.")

    def _generate_signature(self, query_string: str) -> str:
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def _dispatch_request(self, method: str, endpoint: str, params: dict = None):
        if params is None:
            params = {}
            
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = self._generate_signature(query_string)
        
        url = f"{self.BASE_URL}{endpoint}?{query_string}&signature={signature}"
        logger.debug(f"Dispatching {method} request to {endpoint}")
        
        try:
            response = self.session.request(method, url)
            response.raise_for_status()
            logger.debug(f"Received response: {response.status_code}")
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_data = response.json()
                msg = f"API Error {error_data.get('code')}: {error_data.get('msg')}"
                logger.error(f"HTTPError: {msg}")
                raise BinanceClientError(msg)
            except ValueError:
                logger.error(f"HTTPError: {str(e)}")
                raise BinanceClientError(f"HTTP Error: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {str(e)}")
            raise BinanceClientError(f"Network error: {str(e)}")

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = None, time_in_force: str = "GTC"):
        """
        Places an order on the Binance Futures Testnet.
        """
        endpoint = "/fapi/v1/order"
        params = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": order_type.upper(),
            "quantity": quantity,
        }
        
        if order_type.upper() == "LIMIT":
            if price is None:
                raise BinanceClientError("Price must be specified for LIMIT orders.")
            params["price"] = price
            params["timeInForce"] = time_in_force
            
        logger.info(f"Placing {order_type} {side} order for {quantity} {symbol} at {price if price else 'MARKET'}")
        
        return self._dispatch_request("POST", endpoint, params)
