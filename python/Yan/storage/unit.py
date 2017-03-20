from caused import *
from collections import OrderedDict as odict

class Unit(object):
    class FormatError(CausedException):pass

    UNIT = odict([('BYTE',pow(1024,0)), ('KB', pow(1024,1)),
                  ('MB', pow(1024,2)),  ('GB', pow(1024,3)),
                  ('TB', pow(1024,4)),  ('PB', pow(1024,5)),
                  ('KiB', pow(1024,1)), ('MiB', pow(1024,2)),
                  ('GiB', pow(1024,3)), ('TiB', pow(1024,4)),
                  ('PiB', pow(1024,5)), ('B', pow(1024,0)),
                  ('K', pow(1024,1)),   ('M', pow(1024,2)),
                  ('G', pow(1024,3)),   ('T', pow(1024,4)),
                  ('P', pow(1024,5)),   ('SECTOR', 512),
                  ('b', pow(1024,0)),   ('k', pow(1024,1)),
                  ('m', pow(1024,2)),   ('g', pow(1024,3)),
                  ('t', pow(1024,4)),   ('p', pow(1024,5)),
                  ('S', 512), ('Page', 4096)])

    def __init__(self, *vargs):
        try:
            if len(vargs) == 1:
                if isinstance(vargs[0], Unit):
                    self.val = vargs[0].val
                    self.unit = vargs[0].unit.upper()
                else:
                    m = re.search('([0-9.]+)([a-zA-Z]+)', str(vargs[0]))
                    val = float(m.group(1))
                    self.val  = int(val) if val.is_integer() else val
                    self.unit = m.group(2).upper()
            elif len(vargs) == 2:
                val = float(vargs[0])
                self.val = int(val) if val.is_integer() else val
                self.unit = vargs[1].upper()
        except Exception as e:
            raise self.FormatError(cause=e)

        self.byte = float(self.val) * self.UNIT[self.unit]

    def __sub__(self, u):
        return Byte(self.Byte-u.Byte)

    def __add__(self, u):
        return Byte(self.Byte+u.Byte)

    def __mul__(self, n):
        return Byte(self.Byte*n)

    def __rmul__(self, n):
        return self * n

    def __div__(self, n):
        if isinstance(n, Unit):
            v = float(self.Byte) / n.Byte
            return int(v) if v.is_integer() else v
        else:
            return Byte(self.Byte/n)

    def __getattr__(self, name):
        if name.upper() in self.UNIT:
            return self._val(name.upper())
        elif name[:2] == 'to' and name[2:].upper() in self.UNIT:
            return self._to(name[2:].upper())
        else:
            raise AttributeError

    def _val(self, unit):
        val = self.byte / self.UNIT[unit]
        return Unit(val, unit).val

    def _to(self, unit):
        def __to():
            val = self.byte / self.UNIT[unit]
            return Unit(val, unit)
        return __to

    def fit(self):
        for u in self.UNIT:
            val = self.byte / self.UNIT[u]
            if val < 1024: return getattr(self, 'to%s'%u)()

    def floor(self, cap):
        u = unit(cap)
        v = int(u.Byte)
        v1 = int(self.Byte)
        b = Unit(v1/v*v, 'Byte')
        return Unit(getattr(b, self.unit), self.unit)

    def ceil(self, cap):
        u = unit(cap)
        v = int(u.Byte)
        v1 = int(self.Byte)
        b = Unit((v1+v-1)/v*v, 'Byte')
        return Unit(getattr(b, self.unit), self.unit)

    def int(self):
        v = int(self.val)
        return Unit(v, self.unit)

    def __str__(self):
        if isinstance(self.val, int): return '%d%s' % (self.val, self.unit)
        return '%.2f%s' % (self.val, self.unit)

    def __cmp__(self, other):
        return self.Byte - other.Byte

def unit(u):
    return u if isinstance(u, Unit) else Unit(u)

def KB(val):
    if isinstance(val, (str, int, long, float)):
        return Unit(val, 'KB')
    elif isinstance(val, Unit):
        return val.toKB()
    else:
        raise Unit.FormatError()

def MB(val):
    if isinstance(val, (str, int, long, float)):
        return Unit(val, 'MB')
    elif isinstance(val, Unit):
        return val.toMB()
    else:
        raise Unit.FormatError()

def GB(val):
    if isinstance(val, (str, int, long, float)):
        return Unit(val, 'GB')
    elif isinstance(val, Unit):
        return val.toGB()
    else:
        raise Unit.FormatError()

def TB(val):
    if isinstance(val, (str, int, long, float)):
        return Unit(val, 'TB')
    elif isinstance(val, Unit):
        return val.toTB()
    else:
        raise Unit.FormatError()

def Byte(val):
    if isinstance(val, (str, int, long, float)):
        return Unit(val, 'Byte')
    elif isinstance(val, Unit):
        return val.toByte()
    else:
        raise Unit.FormatError()

def Sector(val):
    if isinstance(val, (str, int, long, float)):
        return Unit(val, 'Sector')
    elif isinstance(val, Unit):
        return val.toSector()
    else:
        raise Unit.FormatError()

def Page(val):
    if isinstance(val, (str, int, long, float)):
        return Unit(val, 'Page')
    elif isinstance(val, Unit):
        return val.toPage()
    else:
        raise Unit.FormatError()
