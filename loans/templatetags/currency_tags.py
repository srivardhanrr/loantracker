from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def currency(value):
    """Format currency as whole numbers without decimals"""
    try:
        if value is None:
            return "₹0"
        
        # Convert to Decimal and round to whole number
        amount = Decimal(str(value)).quantize(Decimal('1'))
        
        # Format with Indian number system (commas)
        formatted = "{:,}".format(int(amount))
        return f"₹{formatted}"
    except (ValueError, TypeError, Decimal.InvalidOperation):
        return "₹0"

@register.filter
def whole_number(value):
    """Convert any number to whole number without decimals"""
    try:
        if value is None:
            return "0"
        
        # Convert to Decimal and round to whole number
        number = Decimal(str(value)).quantize(Decimal('1'))
        return "{:,}".format(int(number))
    except (ValueError, TypeError, Decimal.InvalidOperation):
        return "0"
