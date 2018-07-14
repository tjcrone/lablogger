#!/usr/bin/env python
# This program logs data from various IRS lab instruments. See the README file for usage
# notes, or use lablogger -h to display the help information.

# imports
import sys, os, serial, time, argparse, signal, datetime
from socket import gethostname 

# get hostname
hostname=gethostname()

# default device ports
if hostname=='europa':
  tm_port = '/dev/tty.usbserial-A100M04W'

# define required globals as empty
tm = []
mm = []

# ctrl-c handler function
running=True
def signal_handler(signal, frame):
  running=False
  clean_quit()
signal.signal(signal.SIGINT, signal_handler)

# clean up and quit function
def clean_quit():
  if not args.quiet:
    sys.stderr.write("\b\b  \nCleaning up ... ")
  if f: f.close()
  if tm: tm.ser.close()
  if not args.quiet:
    sys.stderr.write("done.\n")
  raise SystemExit

# default output file function
def default_output():
  output = time.strftime('%Y_%m_%d_%H%M%S.log', time.gmtime())
  return output

# version function
version = '0.1.0dev'
def get_version():
  return ('%%(prog)s version %s' % version)

# parse arguments
parser = argparse.ArgumentParser(description='Data logger for IRS lab instruments')
parser.add_argument('-v', '--version', action='version', version=get_version())
parser.add_argument("-d", dest="device", nargs='+', metavar=('name', 'port'),
  default=[], action='append', help="device [and port] to log (options: tm, mm)")
parser.add_argument("-i", dest="interval", metavar="seconds", type=int, default=5,
  help="interval between log entries (default: 5)")
parser.add_argument("-n", dest="total_samples", metavar="samples", type=int, default=[],
  help="number of samples to log (default: inf)")
parser.add_argument("-t", dest="total_seconds", metavar="seconds", type=int, default=[],
  help="total time to log (default: inf)")
parser.add_argument("-o", dest="output", metavar="filename", type=str,
  default=default_output(), help="output file name (default: based on start time)")
parser.add_argument("-q", dest="quiet", action='store_true',
  default=False, help="suppress screen output")
args = parser.parse_args()

# default devices
if not args.device:
  args.device = [['tm']]

# default ports
for dev in args.device:
  if len(dev) == 1:
    if dev[0] == 'tm':
      dev.append(tm_port)
    else:
      parser.error("argument -d: the first device argument must be 'tm'")

# error check device arguments
for dev in args.device:
  if len(dev)>2:
    parser.error("argument -d: device option takes a maximum of two arguments")
  if not os.path.exists(dev[1]):
    parser.error("argument -d: device path '%s' does not exist" % dev[1])

# error check output file
if os.path.isdir(args.output):
  parser.error("argument -o: output file argument '%s' is a directory" % args.output)
if os.path.exists(args.output):
  parser.error("argument -o: output file '%s' already exists" % args.output)
try:
  f = open(args.output, 'a')
  f.close()
  os.remove(args.output)
except:
  raise

# simple device object for namespace convenience
class Device(object):
  pass

# uncomment the following line for testing without any connected devices
#args.device = []

# create requested devices
for dev in args.device:
  if dev[0] == 'tm':
    # create  amprobe object
    tm = Device()
    tm.name = 'Amprobe TMD-56'
    tm.ser = serial.Serial(baudrate=19200, parity=serial.PARITY_EVEN,
      stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1.0)
    tm.ser.port = dev[1]
  elif dev[0] == 'mm':
    # create  multimeter serial object
    mm = Device()
    mm.name = 'multimeter'
    mm.ser = serial.Serial(baudrate=38400, parity=serial.PARITY_NONE,
      stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1.25)
    mm.ser.port = dev[1]

# connector routine
def connect(device):
  if not args.quiet:
    sys.stderr.write("Connecting to %s ... " % device.name)
  num_tries = 10
  n = 0
  while True:
    try:
      device.ser.open()
    except:
      if sys.exc_info()[1].errno == 16: # loop for num_tries on resource busy error
        n = n+1
        if n == num_tries:
          if not args.quiet:
            sys.stderr.write("failed.\nError opening %s port '%s' after %i tries: Resource busy.\n" %
              (device.name, device.ser.port, num_tries))
          raise SystemExit
        else:
          time.sleep(1)
          continue
      else:
        raise # raise the SerialException on any other error
    if not args.quiet:
      sys.stderr.write("done.\n")
    break

# connect to defined devices
if tm:
  connect(tm)
if mm:
  connect(mm)


# function to check if device value is a valid float
def check_float(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

# initialize some counters
total_seconds = 0 # total number of seconds elapsed
total_samples = 0 # total number of samples logged
interval_seconds = 0 # number of seconds elapsed per interval

# open output file
f = open(args.output, 'w')

# write logging started message to stderr
if not args.quiet:
  sys.stderr.write("Logging data to %s every %i s.\n" % (args.output, args.interval))
  sys.stderr.write("Press Ctrl-C to quit logging.\n\n")
 
# header string function
def header():
  device_string=''
  for dev in args.device:
    device_string = device_string + dev[0] + ', '
  device_string = device_string[:-2]
  header_string = [("lablogger version: %s\n" % version),
    ("devices logged: " + device_string + "\n"),
    ("logging interval: %i s\n" % args.interval)]
  return "".join(header_string)

# write header
if not args.quiet:
  sys.stdout.write(header())
  sys.stdout.flush()
f.write(header())
f.flush()

# change mm mode
#if mm:
#  mm.ser.write('FUNC VOLTage:DC\n')
  #mm.ser.write('FUNC CURRent:DC\n')

# loop to log data
while running:
  # quit if requested number of samples have been collected
  if args.total_samples:
    if total_samples == args.total_samples:
      clean_quit()

  # quit if requested logging time has elapsed 
  if args.total_seconds:
    if total_seconds == args.total_seconds:
      clean_quit()

  # sleep for one second
  time.sleep(1 - time.time() % 1)

  # increment counters
  total_seconds = total_seconds+1
  interval_seconds = interval_seconds+1

  # log sample according to the logging inverval
  if interval_seconds == args.interval or total_seconds == 1:
    total_samples = total_samples+1
    interval_seconds = 0

    # get sample time
    sample_time = datetime.datetime.now().strftime('%Y,%m,%d,%H,%M,%S.%f')

    # get tm value
    if tm:
      tm.ser.flushInput()
      tm.ser.flushOutput()
      command = bytes("#0A0000NA2\r\n", "ascii")
      tm.ser.write(command)
      time.sleep(0.05)
      tm_data = tm.ser.read(16)
      if len(tm_data) == 16 and int(tm_data[0])==62 and int(tm_data[1])==15:
        tm_s1 = (int(tm_data[5])*256. + int(tm_data[6]))/10
        tm_s2 = (int(tm_data[10])*256. + int(tm_data[11]))/10

    # get mm value
    if mm:
      #mm.ser.write('FUNC VOLT:DC\n')
      #time.sleep(0.9)
      #mm.ser.write('FUNC CURR:DC\n')
      mm.ser.write('FUNC VOLT:DC\n')
      mm.ser.flushInput()
      mm.ser.flushOutput()
      #time.sleep(0.9)
      mm.ser.write('*TRG\n')
      time.sleep(0.2)
      mm.ser.flushOutput()
      mm.ser.write('FETCH?\n')
      time.sleep(0.2)
      mm.ser.flushInput()
      mm.ser.flushOutput()
      time.sleep(0.9)
      mm_data = mm.ser.read(mm.ser.in_waiting).strip()
      print(mm_data.split('\n'))
      mm.ser.write('FUNC CURR:DC\n')
      # format mm value
      if len(mm_data)>0:
        if mm_data == 'FETCH?':
          mm_cur = "NaN"
        else:
          try:
            mm_cur = mm_data.split('\n')[1]
          except:
            mm_cur = 'NaN'
      else:
        mm_cur = 'NaN'
    else:
      mm_cur = 'NaN'

    #print(mm_cur)

    # write results to screen
    #if not args.quiet:
      #sys.stdout.write('%s,%s,%s\n' % (sample_time, tm_s1, tm_s2))
      #sys.stdout.flush()

    # write results to file
    #f.write('%s,%s,%s\n' % (sample_time, tm_s1, tm_s2))
    #f.flush()
