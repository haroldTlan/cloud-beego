from ctypes import *
from util import uuid

class cdata(object):
    def unpack(self, bytes):
        fit = min(len(bytes), self.sizeof())
        memmove(addressof(self), bytes, fit)

    def sizeof(self):
        return sizeof(self)

    def read_from(self, path, off_sector):
        with open(path, 'r') as dev:
            dev.seek(off_sector*512)
            bytes = dev.read(self.sizeof())
            self.unpack(bytes)

    def __str__(self):
        fields = []
        for f, t in self.__class__._fields_:
            v = getattr(self, f)
            if isinstance(v, Array):
                v = ','.join([hex(e) for e in v])
            elif isinstance(v, int):
                v = hex(v)
            elif isinstance(v, long):
                v = hex(v).replace('L', '')
            fields.append('%18s: %12s' % (f, v))
        return '\n'.join(fields)

class rqr_table_entry(Structure):
    _fields_ = [("bad", c_ulong),
                ("replacement", c_ulong)]

class rqr_table(Structure, cdata):
    _fields_ = [("sign", c_uint),
                ("crc", c_uint),
                ("sn", c_uint),
                ("use", c_uint),
                ("entries", rqr_table_entry*31)]

    def __str__(self):
        valid = ['%s->%s' % (self.entries[i].bad, self.entries[i].replacement)\
                for i in range(0, min(self.use, 31))]
        chunk = [', '.join(valid[i:i+8]) for i in range(0, len(valid), 8)]
        entries = 'entries:\n\t%s' % '\n\t'.join(chunk)
        fields = ['sign:   %#-16x' % self.sign,
                  'crc:    %#-16x' % self.crc,
                  'sn:     %-16s' % self.sn,
                  'use:    %-16s' % self.use]
        if valid:
            fields.append(entries)
        return '\n'.join(fields)

class mdp_superblock_1(Structure, cdata):
    MAGIC = ''
    _fields_ = [("magic", c_uint),
                ("major_version", c_uint),
                ("feature_map", c_uint),
                ("pad0", c_int),
                ("set_uuid", c_ubyte*16),
                ("set_name", c_char*32),
                ("ctime", c_ulong),
                ("level", c_int),
                ("layout", c_uint),
                ("size", c_ulong),
                ("chunksize", c_uint),
                ("raid_disks", c_uint),
                ("bitmap_offset", c_int),
                ("new_level", c_int),
                ("reshape_position", c_ulong),
                ("delta_disks", c_int),
                ("new_layout", c_uint),
                ("new_chunk", c_uint),
                ("new_offset", c_int),
                ("data_offset", c_ulong),
                ("data_size", c_ulong),
                ("super_offset", c_ulong),
                ("recovery_offset", c_ulong),
                ("dev_number", c_uint),
                ("cnt_corrected_read", c_uint),
                ("device_uuid", c_ubyte*16),
                ("devflags", c_ubyte),
                ("bblog_shift", c_ubyte),
                ("bblog_size", c_ushort),
                ("bblog_offset", c_uint),
                ("utime", c_ulong),
                ("events", c_ulong),
                ("resync_offset", c_ulong),
                ("sb_csum", c_uint),
                ("max_dev", c_uint),
                ("pad3", c_ubyte*32),
                ("dev_roles", c_ushort*27)]

    @property
    def valid(self):
        return self.magic == self.MAGIC

    @property
    def raid_uuid(self):
        return uuid.normalize(''.join([hex(b)[2:] for b in self.set_uuid]))

class mdp_superblock_bitmap(Structure, cdata):
    _fields_ = [("magic", c_uint),
                ("version", c_uint),
                ("uuid", c_ubyte*16),
                ("events", c_ulong),
                ("events_cleared", c_ulong),
                ("sync_size", c_ulong),
                ("state", c_int),
                ("chunksize", c_uint),
                ("daemon_sleep", c_uint),
                ("write_behind", c_int),
                ("pad", c_ubyte*192),
                ("bitmap", c_ubyte*64)]


class monfs_superblock(Structure, cdata):
    MAGIC = 0x6d667300
    _fields_ = [("magic", c_uint),
                ("_uuid", c_ubyte*16),
                ("name", c_char*32),
                ("_edev_uuid", c_ubyte*16),
                ("export_meta_off", c_ulong),
                ("export_meta_size", c_ulong),
                ("ebitmap_off", c_ulong),
                ("ebitmap_size", c_ulong),
                ("ebitmap_nr", c_uint),
                ("ebitmap_bits", c_ulong),
                ("extent_off", c_ulong),
                ("extent_size", c_ulong),
                ("extent_nr", c_uint),
                ("_mdev_uuid", c_ubyte*16),
                ("m_ebitmap_off", c_ulong),
                ("m_ebitmap_size", c_ulong),
                ("m_ebitmap_nr", c_uint),
                ("m_ebitmap_bits", c_ulong),
                ("m_ibitmap_off", c_ulong),
                ("m_ibitmap_size", c_ulong),
                ("m_ibitmap_nr", c_uint),
                ("m_ibitmap_bits", c_ulong),
                ("m_imap_off", c_ulong),
                ("m_imap_size", c_ulong),
                ("m_imap_nr", c_uint),
                ("ctime", c_ulong)]

    @property
    def valid(self):
        return self.magic == self.MAGIC

    @property
    def uuid(self):
        return uuid.normalize(''.join([hex(b)[2:] for b in self._uuid]))

    @property
    def edev_uuid(self):
        return uuid.normalize(''.join([hex(b)[2:] for b in self._edev_uuid]))

    @property
    def mdev_uuid(self):
        return uuid.normalize(''.join([hex(b)[2:] for b in self._mdev_uuid]))

def print_rqr(path, off, count):
    for i in range(0, count):
        rqr = rqr_table()
        rqr.read_from(path, off+i)
        print rqr

def print_md_sb(path, off):
    sb = mdp_superblock_1()
    sb.read_from(path, off)
    print sb

def print_md_bm(path, off):
    bm = mdp_superblock_bitmap()
    bm.read_from(path, off)
    print bm

def print_monfs_sb(path, off):
    msb = monfs_superblock()
    msb.read_from(path, off)
    print msb
