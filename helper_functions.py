def isleapyear(yr):
    """Detects if a year is a leap year and returns T or F accordingly"""
    if yr % 4 == 0 and yr % 100 != 0:
        return True
    elif yr % 400 == 0:
        return True
    elif yr % 100 == 0:
        return False
    else:
        return False


def dt2freq(dt):
    """Converts a time step in hours to a DER-VET readable code"""
    if dt == .25:
        return '15min'
    elif dt == 1:
        return 'H'
    elif dt == .5:
        return '30min'
    else:
        print('Invalid dt input in Load screen. Assuming 15 minute intervals')
        return '15min'


def textonly(tovalidate):
    """Returns T or F depending on whether the input is a single character in A-Z or a-z or an empty string"""
    return tovalidate.isalpha() | (tovalidate == '') | (tovalidate == ' ')


def numonly(tovalidate):
    """Returns T or F depending on whether the input is a single character in 0-9, ., or and empty string"""
    return tovalidate.isdecimal() | (tovalidate == '.') | (tovalidate == '')

def numonlynoblank(tovalidate):
    """Returns T or F depending on whether the input is a single character in 0-9, or ."""
    return tovalidate.isdecimal() | (tovalidate == '.')