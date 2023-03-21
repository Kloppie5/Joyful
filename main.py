import ctypes
from ctypes.wintypes import BOOL, DWORD, HANDLE, ULONG, WCHAR, WORD
from ctypes import c_ubyte as UBYTE
from ctypes import c_longlong as ULONGLONG
import socket

joyconL = 0xE0F6B52E4E22
joyconR = 0xE0F6B52E0E07

bthprops = ctypes.windll["bthprops.cpl"]
kernel32 = ctypes.windll["Kernel32.dll"]

class SYSTEMTIME(ctypes.Structure):
    _fields_ = [
        ('wYear', WORD),
        ('wMonth', WORD),
        ('wDayOfWeek', WORD),
        ('wDay', WORD),
        ('wHour', WORD),
        ('wMinute', WORD),
        ('wSecond', WORD),
        ('wMilliseconds', WORD),
    ]
    
    def __str__ ( self ) :
        month_map = {
            0: "NULL",
            1: "January",
            2: "February",
            3: "March",
            4: "April",
            5: "May",
            6: "June",
            7: "July",
            8: "August",
            9: "September",
            10: "October",
            11: "November",
            12: "December"
        }
        day_of_week_map = {
            0: "Sunday",
            1: "Monday",
            2: "Tuesday",
            3: "Wednesday",
            4: "Thursday",
            5: "Friday",
            6: "Saturday"
        }
        return f"{day_of_week_map[self.wDayOfWeek]}, {month_map[self.wMonth]} {self.wDay}, {self.wYear} | {self.wHour}:{self.wMinute}:{self.wSecond}.{self.wMilliseconds}"

class BLUETOOTH_ADDRESS(ctypes.Union):
    _fields_ = [
        ('ullLong', ULONGLONG),
        ('rgBytes', 6 * UBYTE),
    ]
    
    def __str__ ( self ) :
        return self.__repr__()
    
    def __repr__ ( self ) :
        addr_str = ""
        for i in range(5, -1, -1):
            if i != 5 :
                addr_str += ":"
            addr_str += f"{self.rgBytes[i]:02X}"
        return addr_str
    
    def __eq__ ( self, other ) :
        return self.ullLong == other.ullLong

class BLUETOOTH_DEVICE_INFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', DWORD),
        ('Address', BLUETOOTH_ADDRESS),
        ('ulClassofDevice', ULONG),
        ('fConnected', BOOL),
        ('fRemembered', BOOL),
        ('fAuthenticated', BOOL),
        ('stLastSeen', SYSTEMTIME),
        ('stLastUsed', SYSTEMTIME),
        ('szName', 248 * WCHAR),
    ]

    def __init__ ( self, Address = None ) :
        super().__init__()
        self.cbSize = ctypes.sizeof(self)
        if Address is not None:
            self.Address = Address
    
    def __str__ ( self ) :
        class_str = hex(self.ulClassofDevice)
        if class_str[-1] == "L":
            class_str = class_str[:-1]
            while len(class_str) < 10:
                class_str = "0x0" + class_str[2:]
        return f"Size: {self.cbSize}\nAddress: {str(self.Address)}\nClass Of Device: {class_str}\nConnected: {self.fConnected != 0}\nRemembered: {self.fRemembered != 0}\nAuthenticated: {self.fAuthenticated != 0}\nLast Seen: {str(self.stLastSeen)}\nLast Used: {str(self.stLastUsed)}\nName: {str(self.szName)}"

class BLUETOOTH_DEVICE_SEARCH_PARAMS(ctypes.Structure):
    _fields_ = [
        ('cbSize', DWORD),
        ('fReturnAuthenticated', BOOL),
        ('fReturnRemembered', BOOL),
        ('fReturnUnknown', BOOL),
        ('fReturnConnected', BOOL),
        ('fIssueInquiry', BOOL),
        ('cTimeoutMultiplier', UBYTE),
        ('hRadio', HANDLE),
    ]

    def __init__ ( self, fReturnAuthenticated = True, fReturnRemembered = True, fReturnUnknown = True, fReturnConnected = True, fIssueInquiry = True, cTimeoutMultiplier = 1, hRadio = None ) :
        super().__init__()
        self.cbSize = ctypes.sizeof(self)
        self.fReturnAuthenticated = fReturnAuthenticated
        self.fReturnRemembered = fReturnRemembered
        self.fReturnUnknown = fReturnUnknown
        self.fReturnConnected = fReturnConnected
        self.fIssueInquiry = fIssueInquiry
        self.cTimeoutMultiplier = cTimeoutMultiplier
        self.hRadio = hRadio

def getBluetoothDevices ( ) :
    print("Getting bluetooth devices...")
    search_params = BLUETOOTH_DEVICE_SEARCH_PARAMS()
    device_info = BLUETOOTH_DEVICE_INFO()

    device_find_handle = bthprops.BluetoothFindFirstDevice(ctypes.byref(search_params), ctypes.byref(device_info))
    if device_find_handle == 0:
        error_code = kernel32.GetLastError()
        raise Exception(f"BluetoothFindFirstDevice failed with error code {error_code}")
        
    print("Found device:")
    print(device_info)
    print()


getBluetoothDevices()

"""
BluetoothFindNextDevice = ctypes.windll["bthprops.cpl"].BluetoothFindNextDevice
BluetoothFindNextDevice.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulonglong)]
BluetoothFindNextDevice.restype = ctypes.c_int

class GUID(ctypes.Structure):
    _fields_ = [("Data1", ctypes.c_ulong),
                ("Data2", ctypes.c_ushort),
                ("Data3", ctypes.c_ushort),
                ("Data4", ctypes.c_byte * 8)]

handle = ctypes.c_void_p()

bt_guid = GUID(0x00001101, 0x0000, 0x1000, (0x80, 0x00, 0x00, 0x80, 0x5f, 0x9b, 0x34, 0xfb))
result = ctypes.windll["bthprops.cpl"].BluetoothFindFirstDevice(ctypes.byref(bt_guid), ctypes.byref(handle))
if result != 0:
    print("Error: {}".format(result))
    exit()
print("Handle: {}".format(handle.value))
print("Result: {}".format(result))
exit()

while True:
    device_info = ctypes.c_ulonglong()
    result = BluetoothFindNextDevice(handle, ctypes.byref(device_info))
    if result == 0:
        # Process the device_info
        device_address = "{:012X}".format(device_info.value >> 16)
        print(f"Device address: {device_address}")
        pass
    elif result == 0x16f:  # ERROR_NO_MORE_ITEMS
        # End of search
        break
    else:
        print("Error: {}".format(result))
        exit()

ctypes.windll["bthprops.cpl"].BluetoothFindDeviceClose(handle)
"""
