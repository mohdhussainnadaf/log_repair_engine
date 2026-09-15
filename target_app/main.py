def calculate_discount(price: float, discount: float) -> float:
    # BUG: Division by zero when price is 0
    return price - (discount / price)
