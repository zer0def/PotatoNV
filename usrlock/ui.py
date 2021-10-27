def error(*data, critical=False):
    print("ERROR: {}".format(" ".join(data)))
    if critical:
        exit(1)


def success(*data):
    print("SUCCESS: {}".format(" ".join(data)))


def tip(*data):
    print("TIP: {}".format(" ".join(data)))


def info(*data):
    print("INFO: {}".format(" ".join(data)))


def debug(*data):
    return
    print("DEBUG: {}".format(" ".join(data)))


def progress(title=None, value=0, max_value=100):
    perc = int(100.0 * value / max_value)
    print('%s%d%%' % (' ' * (3 - len(str(perc))), perc), end='')
    if title:
        print(' %s' % title, end='')
    print(end='\r')
    if perc == 100:
        done()


def done():
    print("DONE")
