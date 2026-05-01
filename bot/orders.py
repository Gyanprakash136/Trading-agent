from typing import Optional
from .client import BinanceTestnetClient, BinanceClientError
from .logging_config import logger

def execute_trade(symbol: str, side: str, order_type: str, quantity: float, price: Optional[float] = None) -> dict:
    """
    Validates input and executes trade via client.
    """
    try:
        client = BinanceTestnetClient()
        response = client.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price
        )
        logger.info(f"Order successful. ID: {response.get('orderId')}, Status: {response.get('status')}")
        return response
    except BinanceClientError as e:
        error_msg = str(e)
        if "4164" in error_msg:
            friendly_msg = "Order size too small! Binance Futures requires a minimum 'Notional Value' of 50 USDT. Try increasing your quantity (e.g., 0.01 instead of 0.001)."
            logger.error(friendly_msg)
            raise BinanceClientError(friendly_msg)
        logger.error(f"Failed to execute trade: {e}")
        raise e
