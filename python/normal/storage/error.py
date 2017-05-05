from caused import caused, CausedException
import log

def status(status, exc=None, detail=None):
    status = {'status': status}
    if exc:
        if hasattr(exc, 'errcode'):
            status['errcode'] = exc.errcode
        status['description'] = exc.message
    if detail is not None: status['detail'] = detail
    return status

def success(detail=None):
    return status('success', detail=detail)

def error(exc=None, detail=None):
    return status('error', exc, detail)

def exc2status(func):
    def _exc2status(*vargs, **kv):
        try:
            o = func(*vargs, **kv)
        except ExternalError as e:
            log.error(caused(e).detail)
            return error(e)
        except Exception as e:
            log.error(caused(e).detail)
            return internal_error
        else:
            return success(o)
    return _exc2status

class ExternalError(CausedException):
    def __init__(self, message, **kv):
        super(ExternalError, self).__init__(message, **kv)
        for k, v in kv.items():
            setattr(self, k, v)

class InternalError(CausedException):
    errcode=10001
    def __init__(self, message='internal error.', **kv):
        super(InternalError, self).__init__(message, **kv)
        for k, v in kv.items():
            setattr(self, k, v)

class InvalidParam(ExternalError):
    errcode=10002
    def __init__(self, attr, val):
        message = 'invalid param %s=%s.' % (attr, val)
        super(InvalidParam, self).__init__(message, attr=attr, val=val)

class InvalidCommand(ExternalError):
    errcode=10003
    def __init__(self, command):
        message = 'invalid command %s' % command
        super(InvalidCommand, self).__init__(message, command=command)

class ExistError(ExternalError):
    errcode=10004
    def __init__(self, name):
        message = '%s has existed.' % name
        super(ExistError, self).__init__(message, name=name)

class NotExistError(ExternalError):
    errcode=10005
    def __init__(self, name):
        message = '%s has not existed.' % name
        super(NotExistError, self).__init__(message, name=name)

class NameTooLong(ExternalError):
    errcode=10006
    def __init__(self, name, length):
        message = '%s exceed %s characters limit.' % (name, length)
        super(NameTooLong, self).__init__(message, name=name, length=length)

class ShellError(InternalError):
    errcode=10007
    def __init__(self, cmd, err, output):
        o = '\t\n'.join(output.split('\n')).rstrip('\n')
        message = 'failed to execute shell cmd.\n'\
                  'command: '\
                  '%s\n'\
                  'output: '\
                  '%s\n'\
                  'errcode: %s' % (cmd, o, err)
        super(ShellError, self).__init__(message, cmd=cmd, err=err, output=output)

class OutputMismatched(InternalError):
    errcode=10008
    def __init__(self, output, matched):
        message = 'output: %s mismatches %s.' % (output, matched)
        super(OutputMismatched, self).__init__(message, output=output, matched=matched)

class LoginError(ExternalError):
    errcode=10009
    def __init__(self, name):
        message = 'user %s login failed.' % name
        super(LoginError, self).__init__(message, name=name)

class Unauthorized(ExternalError):
    errcode=10010
    def __init__(self):
        message = 'request is unauthorized.'
        super(Unauthorized, self).__init__(message)

class Timeout(ExternalError):
    errcode=10011
    def __init__(self):
        message = 'timeout.'
        super(Timeout, self).__init__(message)

class UnkownOperation(ExternalError):
    errcode=10012
    def __init__(self):
        message = 'unkown operation.'
        super(UnkownOperation, self).__init__(message)

class Disk(object):
    class NeedNotFormat(ExternalError):
        errcode = 70001
        def __init__(self, disk):
            message = 'disk %s need not format.' % disk
            super(Disk.NeedNotFormat, self).__init__(message, disk=disk)

    class NotFoundAnyDisk(InternalError):
        errcode = 70002
        def __init__(self):
            message = 'not found any disk.'
            super(Disk.NotFoundAnyDisk, self).__init__(message)

    class Role(ExternalError):
        errcode = 70003
        def __init__(self, disk, role, newrole):
            message = 'disk %s role is %s, can\'t set to %s.' % (disk, role, newrole)
            super(Disk.Role, self).__init__(message)

class Raid(object):
    class NeedMoreDisk(ExternalError):
        errcode = 20001
        def __init__(self, nr, level):
            message = '%s disks are not enough to create level %s raid.' % (nr, level)
            super(Raid.NeedMoreDisk, self).__init__(message, nr=nr, level=level)

    class DiskRepeated(ExternalError):
        errcode = 20002
        def __init__(self, disk):
            message = 'disk %s is repeated.' % disk
            super(Raid.DiskRepeated, self).__init__(message, disk=disk)

    class DiskUsed(ExternalError):
        errcode = 20003
        def __init__(self, disk):
            message = 'disk %s has used.' % disk
            super(Raid.DiskUsed, self).__init__(message, disk=disk)

    class DiskUnnormal(ExternalError):
        errcode = 20004
        def __init__(self, disk):
            message = 'disk %s is unnormal.' % disk
            super(Raid.DiskUnnormal, self).__init__(message, disk=disk)

    class InUse(ExternalError):
        errcode = 20005
        def __init__(self, raid):
            message = 'raid %s in use.' % raid
            super(Raid.InUse, self).__init__(message, raid=raid)

    class DiskBeyondLimit(ExternalError):
        errcode = 20011
        def __init__(self, limit):
            message = 'disk number beyonds %s limit.' % limit
            super(Raid.DiskBeyondLimit, self).__init__(message, limit=limit)

    class Level1DiskNum(ExternalError):
        errcode = 20012
        def __init__(self):
            message = 'level 1 raid only support 2 disks.'
            super(Raid.Level1DiskNum, self).__init__(message)

    class NotSupportSpareDisk(ExternalError):
        errcode = 20013
        def __init__(self, level):
            message = 'level %s raid does not support spare disk.' % level
            super(Raid.NotSupportSpareDisk, self).__init__(message, level=level)

    class AtLeastOneDiskOnDSU11(ExternalError):
        errcode = 20014
        def __init__(self):
            message = 'need at least one disk on dsu 1.1 to create raid'
            super(Raid.AtLeastOneDiskOnDSU11, self).__init__(message)

    class NotSameCapacityDisk(ExternalError):
        errcode = 20015
        def __init__(self):
            message = 'not same capacity disk'
            super(Raid.NotSameCapacityDisk, self).__init__(message)

    class NotEnoughCacheMem(ExternalError):
        errcode = 20016
        def __init__(self):
            message = 'not enough cache memory'
            super(Raid.NotEnoughCacheMem, self).__init__(message)

class Volume(object):
    class Mapped(ExternalError):
        errcode = 30001
        def __init__(self, volume):
            message = 'volume %s is mapped to initiators.' % volume
            super(Volume.Mapped, self).__init__(message, volume=volume)

    class CapacityLessThanPE(ExternalError):
        errcode = 30002
        def __init__(self, cap, pe):
            message = 'capacity %s is less than minimun size %s.' % (cap, pe.fit())
            super(Volume.CapacityLessThanPE, self).__init__(message, cap=cap, pe=pe)

    class NotEnoughFreeCapacity(ExternalError):
        errcode = 30003
        def __init__(self, free_cap, alloc_cap):
            message = 'free capacity is %s, not enough to allocate %s.' % (free_cap.fit(), alloc_cap.fit())
            super(Volume.NotEnoughFreeCapacity, self).__init__(message, free_cap=free_cap, alloc_cap=alloc_cap)

    class HasFS(ExternalError):
        errcode = 30004
        def __init__(self, volume):
            message = '%s has monfs.' % volume
            super(Volume.HasFS, self).__init__(message, volume=volume)


class Initiator(object):
    class Mapping(ExternalError):
        errcode = 40001
        def __init__(self, initr):
            message = 'initiator %s mapped volumes.' % initr
            super(Initiator.Mapping, self).__init__(message, initr=initr)

    class ActiveSession(ExternalError):
        errcode = 40002
        def __init__(self, initr):
            message = 'initiator %s is actvie.' % initr
            super(Initiator.ActiveSession, self).__init__(message, initr=initr)

class VIMap(object):
    class Mapping(ExternalError):
        errcode = 50001
        def __init__(self, initr, volume):
            message = 'initiator %s has mapped volume %s.' % (initr, volume)
            super(VIMap.Mapping, self).__init__(message, initr=initr, volume=volume)

    class NotMapping(ExternalError):
        errcode = 50002
        def __init__(self, initr, volume):
            message = 'initiator %s has not mapped volume %s.' % (initr, volume)
            super(VIMap.NotMapping, self).__init__(message, initr=initr, volume=volume)

    class VolumeUsed(ExternalError):
        errcode = 50003
        def __init__(self, volume):
            message = 'volume %s has used.' % volume
            super(VIMap.VolumeUsed, self).__init__(message, volume=volume)

class Network(object):
    class IPAdressError(ExternalError):
        errcode = 60001
        def __init__(self, address):
            message = 'address %s error.' % address
            super(Network.IPAdressError, self).__init__(message, address=address)

    class InitiatorOnIFace(ExternalError):
        errcode = 60002
        def __init__(self, iface):
            message = 'iface %s is using by initiators.' % iface
            super(Network.InitiatorOnIFace, self).__init__(message, iface=iface)

    class SameSubnet(ExternalError):
        errcode = 60003
        def __init__(self, network):
            message = 'other ifaces are using the subnet %s.' % network
            super(Network.SameSubnet, self).__init__(message, network=network)

    class GatewayUnreachable(ExternalError):
        errcode = 60004
        def __init__(self, address):
            message = 'no ifaces can reach gateway %s.' % address
            super(Network.GatewayUnreachable, self).__init__(message, address=address)

    class IFaceNotAvailable(ExternalError):
        errcode = 60005
        def __init__(self, iface):
            message = 'iface %s is not available.' % iface
            super(Network.IFaceNotAvailable, self).__init__(message, iface=iface)

class User(object):
    class NewPasswordInvalid(ExternalError):
        errcode = 70001
        def __init__(self):
            message = 'new password is invalid.'
            super(User.NewPasswordInvalid, self).__init__(message)

    class OldPasswordWrong(ExternalError):
        errcode = 70002
        def __init__(self):
            message = 'old password is wrong.'
            super(User.OldPasswordWrong, self).__init__(message)

class DB(object):
    class ConnectionUnmatch(InternalError):
        errcode = 80001
        def __init__(self):
            message = 'connection open and close number are not match.'
            super(DB.ConnectionUnmatch, self).__init__(message)

    class TransactionUnmatch(InternalError):
        errcode = 80002
        def __init__(self, raid, disks):
            message = 'transaction begin and commit/rollback number are not match.'
            super(DB.TransactionUnmatch, self).__init__(message)

class FS(object):
    class OnlySupportOne(ExternalError):
        errcode = 90001
        def __init__(self):
            message = 'only support one monfs filesystem'
            super(FS.OnlySupportOne, self).__init__(message)

    class VolumeUnnormal(ExternalError):
        errcode = 90002
        def __init__(self, volume):
            message = 'volume %s is unnormal.' % volume
            super(FS.VolumeUnnormal, self).__init__(message, volume=volume)

    class VolumeUsed(ExternalError):
        errcode = 90003
        def __init__(self, volume):
            message = 'volume %s has used.' % volume
            super(FS.VolumeUsed, self).__init__(message, volume=volume)

    class MountedDirUsed(ExternalError):
        errcode = 90004
        def __init__(self, mdir):
            message = 'monfs is used, can not be umounted.'
            super(FS.MountedDirUsed, self).__init__(message, mdir=mdir)

    class RaidStripeNotEnough(ExternalError):
        errcode = 90005
        def __init__(self, raid, stripe):
            message = 'raid %s\'s stripe %s is less than 512KB.' % (raid, stripe)
            super(FS.RaidStripeNotEnough, self).__init__(message, raid=raid, stripe=stripe)

    class NoMountPoint(ExternalError):
        errcode = 90006
        def __init__(self):
            message = 'no mountpoint'
            super(FS.NoMountPoint, self).__init__(message)

internal_error = error(InternalError())

