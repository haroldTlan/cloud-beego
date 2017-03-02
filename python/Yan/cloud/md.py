import md5
from util import uuid, execute
import re
import unit

class MetadataChecksum(Exception):
    pass

class MetadataAttrNotFound(Exception):
    pass

class Metadata(object):
    MAGIC_VAL = 'bf2f21a8-80ca-4934-bdd4-950c79c6b5e7'
    MAGIC = 'magic'
    VERSION = 'version'
    LENGTH = 'length'
    CHECKSUM = 'checksum'
    HEADER_LENGTH = 128
    ver_map = {}
    def _get_metadata_attr(self, ms, attr):
        m = re.search('%s: (.+)' % attr, ms)
        if not m: raise MetadataAttrNotFound()
        return m.group(), m.group(1)

    def _read_header(self, dev):
        header = dev.read(self.HEADER_LENGTH).rstrip('\0\n')
        line1, magic = self._get_metadata_attr(header, self.MAGIC)
        line2, ver = self._get_metadata_attr(header, self.VERSION)
        line3, len = self._get_metadata_attr(header, self.LENGTH)
        if magic <> self.MAGIC_VAL: raise MetadataAttrNotFound()
        self._check_metadata(header)
        return ver, len

    def _read(self, disk, off):
        with open(disk, 'r') as dev:
            dev.seek(512*off)
            ver, len = self._read_header(dev)
            mc = dev.read(int(len))

        return ver, mc

    def _calc_checksum(self, ms):
        return md5.new(ms).hexdigest()

    def _append_checksum(self, mc):
        ms = self._format(*mc)
        chksum = self._calc_checksum(ms)
        mc.append((self.CHECKSUM, chksum))

    def _check_metadata(self, ms):
        idx = ms.find(self.CHECKSUM)
        if idx == -1: raise MetadataChecksum()
        chksum = self._calc_checksum(ms[:idx-1])
        line, _chksum = self._get_metadata_attr(ms, self.CHECKSUM)
        if chksum <> _chksum: raise MetadataChecksum()

    def _format(self, *vargs):
        mc = []
        for k, v in vargs:
            mc.append('%s: %s' % (k, v))
        return '\n'.join(mc)

    def _pack_header(self, ver, ms):
        attrs = [(self.MAGIC, self.MAGIC_VAL), (self.VERSION, ver), (self.LENGTH, len(ms))]
        self._append_checksum(attrs)
        header = self._format(*attrs)
        header += '\0' * (self.HEADER_LENGTH-len(header)-1) + '\n'
        return header + ms

    @classmethod
    def parse(cls, disk, off=1):
        md = Metadata()
        ver, mc = md._read(disk, off)

        mdcls = eval(Metadata.ver_map[ver])
        md = mdcls()
        md.parse(mc)
        return md

    @classmethod
    def update(cls, disk, off=1, **kv):
        md = cls.parse(disk, off)
        for k, v in kv.items():
            if k in md.MD_ATTRS:
                setattr(md, k, v)
        md.save(disk, off)
        return md

class DiskMetadata_1(Metadata):
    VERSION_VAL = 'disk1.0'
    Metadata.ver_map[VERSION_VAL] = 'DiskMetadata_1'
    MD_ATTRS = ['host-uuid', 'disk-uuid']

    def __init__(self):
        self.host_uuid = uuid.host_uuid()
        self.disk_uuid = ''

    def _attr(self, name):
        return '%s' % name.replace('-', '_')

    def parse(self, mc):
        self._check_metadata(mc)
        for mattr in self.MD_ATTRS:
            try:
                line, val = self._get_metadata_attr(mc, mattr)
            except Exception as e:
                if not hasattr(self, self._attr(mattr)):
                    raise e
            else:
                setattr(self, self._attr(mattr), val)

    def save(self, disk, off=1):
        with open(disk, 'w') as dev:
            dev.seek(512*off) 
            dev.write(str(self))
            dev.flush()

    def __str__(self):
        mc = []
        for mattr in self.MD_ATTRS:
            val = getattr(self, self._attr(mattr), None)
            if val is None: raise MetadataAttrNotFound()
            if val:
                mc.append((mattr, val))

        self._append_checksum(mc)
        ms = self._format(*mc)
        return self._pack_header(self.VERSION_VAL, ms)

class DiskMetadata_1_1(DiskMetadata_1):
    VERSION_VAL = 'disk1.1'
    Metadata.ver_map[VERSION_VAL] = 'DiskMetadata_1_1'
    MD_ATTRS = ['host_uuid', 'disk_uuid', 'partition_size', 'partition_max_nr', 'rqr_reserved_ratio', 'raid_uuid']

    def __init__(self):
        super(DiskMetadata_1_1, self).__init__()
        self.raid_uuid = ''

    def _attr(self, name):
        return name

    def parse(self, mc):
        super(DiskMetadata_1_1, self).parse(mc)
        self.partition_size = unit.unit(self.partition_size)
        self.partition_max_nr = int(self.partition_max_nr)
        self.rqr_reserved_ratio = float(self.rqr_reserved_ratio)

from ctypes import *

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
    MAGIC = 0xa92b4efc
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
    def raid_uuid(self):
        return uuid.normalize(''.join(hex(b)[2:] for b in self.set_uuid))

    @property
    def name(self):
        m = re.search('speedio:(\w+)', self.set_name)
        return m.group(1) if m else '%s-%s' % (self.set_name, self.raid_uuid[:8])

    @property
    def valid(self):
        return self.magic == self.MAGIC

    def read_from(self, path, off_sector=8):
        super(mdp_superblock_1, self).read_from(path, off_sector)

    def __str__(self):
        fields = []
        for f, t in mdp_superblock_1._fields_:
            v = getattr(self, f)
            if isinstance(v, Array):
                v = ','.join([hex(e) for e in v])
            elif isinstance(v, int):
                v = hex(v)
            elif isinstance(v, long):
                v = hex(v).replace('L', '')
            fields.append('%18s: %12s' % (f, v))
        return '\n'.join(fields)

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

    def __str__(self):
        fields = []
        for f, t in mdp_superblock_bitmap._fields_:
            v = getattr(self, f)
            if isinstance(v, Array):
                v = ','.join([hex(e) for e in v])
            elif isinstance(v, int):
                v = hex(v)
            elif isinstance(v, long):
                v = hex(v).replace('L', '')
            fields.append('%18s: %12s' % (f, v))
        return '\n'.join(fields)

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

