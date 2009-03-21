import re
re.compile

def textsplit(text):
    # FIXME: several brackets missing, etc.
    # but at least this respects unicode and is better than string.split
    l = re.findall(r'[^-() ,.?!:;=\'"<>\n/\\]+', text)
    l = [s for s in l if len(s) < 40]
    return l

def age2str(age):
    age = age / (60*60*24)
    if age < 14:
        return '%d days' % age
    elif age < 2*30:
        return '%d weeks' % (age/7)
    else:
        age /= 30
        if age < 24:
            return '%d months' % age
        else:
            return '%d years' % (age/12)
