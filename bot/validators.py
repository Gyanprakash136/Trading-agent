def validate_order_type_and_price(order_type: str, price: float):
    if order_type.upper() == "LIMIT" and price is None:
        raise ValueError("Price is required for LIMIT orders.")
    if order_type.upper() not in ["MARKET", "LIMIT"]:
        raise ValueError("Invalid order type. Must be MARKET or LIMIT.")

def validate_side(side: str):
    if side.upper() not in ["BUY", "SELL"]:
        raise ValueError("Invalid side. Must be BUY or SELL.")

def validate_quantity(quantity: float):
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")
