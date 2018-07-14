from serial import Serial
from time import sleep


def device():
    return Device()


class Device():

    self.serial = Serial(baudrate=19200, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS, timeout=1.0)
    #self.serial = Serial()


    def connect:
        n = 0
        while True:
            try:
                self.serial.open()
                self.connected = True
            except:
                if sys.exc_info()[1].errno == 16: # loop for num_tries on resource busy error
                    n = n+1
                    if n == num_tries:
                        raise
                    else:
                        sleep(1)
                        continue
                else:
                    raise # raise the SerialException on any other error
