import time
#import visa

def num_to_hex(x):
    if int(x) == float(x):
        x = int(x)
    if x == 0 or float(x) == 0:
        return "00000000"
    res = []
    if x > 0:
        res.append(str(0))
    else:
        res.append(str(8))
    x = abs(x)
    e = 0
    m = x
    while m >= 2:
        m = m / 2
        e += 1

    res.append(hex(e + 1)[2:])
    #print("e:{}".format(e))

    m = m * 128
    m_int = int(m)
    m_digit = m - m_int
    m_digit = int(m_digit * 65536)
    #print("m int:")
    #print(m_int)

    m_int = hex(m_int)[2:]
    m_int = "0" * (2 - len(m_int)) + m_int
    m_digit = hex(m_digit)[2:]
    m_digit = "0" * (4 - len(m_digit)) + m_digit

    res.append(m_int)
    res.append(m_digit)
    res = "".join(res).upper()
    if not len(res) == 8:
        print(res)
        print(x)
        print(type(x))
        print("error!!")
        return "00000000"
    return res


def hex_to_num(s):
    sign = s[0]
    if sign == '0':
        sign = 1
    elif sign == '8':
        sign = -1
    else:
        return 0

    e = int(s[1], 16) - 1
    m_int = s[2:4].lstrip('0')
    if len(m_int) == 0:
        m_int = '0'
    m_int = int(m_int, 16)
    m_float = s[4:].lstrip('0')
    if len(m_float) == 0:
        m_float = '0'
    m_float = int(m_float, 16)
    m = (m_int + (m_float / 65536)) / 128
    res = sign * m * 2 ** e
    return res


def read_field(gauss):
    f = gauss.query("RDGFIELD?")
    f = round(float(f[:-2])*10)/10
    return f

def vsm_read_field(vsm):
    f = vsm.query("READ?")[18:26].lower()
    if not(len(f) == 8):
        raise
    f = hex_to_num(f)
    return f

def check_stable(vsm, time_per_point=0.5):
    current = [0, 0 ,0]
    target = [2, 2, 2]
    while True:
        next_point = int(vsm.query("CONST?")[0])
        current.pop(0)
        current.append(next_point)
        if current == target:
            return
        time.sleep(time_per_point)

def vsm_set_field(vsm, field, rate=1000):
    vsm.write("CONTO " + num_to_hex(field))

def set_field(vsm, gauss, field, rate=1000):
    vsm.write("RANGE 0 ") # high field range
    vsm.write("CMODE 2 ") # field ramp mode
    time.sleep(0.1)
    vsm.write("CONTR " + num_to_hex(rate))
    vsm.write("CONTO " + num_to_hex(field))
    check_stable(vsm)
    current = read_field(gauss)
    diff = field - current
    new_f = field + diff
    vsm.write("CONTO " + num_to_hex(new_f))
    check_stable(vsm)

if __name__ == "__main__":
    for i in range(-100,100):
        print(hex_to_num(num_to_hex(i)))
    #print(num_to_hex(4))
