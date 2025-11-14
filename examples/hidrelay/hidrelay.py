import argparse
import os
import sys
import time

from tempfile import NamedTemporaryFile

from labgrid import Target, Environment
from labgrid.resource import HIDRelay
from labgrid.driver import HIDRelayDriver
from labgrid.driver import DigitalOutputPowerDriver

parser = argparse.ArgumentParser()
parser.add_argument('--use-code', help="build the target with code", action='store_true')
parser.add_argument('--use-yaml', help="build the target from yaml code", action='store_true')
parser.add_argument('--first-index', help="index of the first relay", type=int)
parser.add_argument('--second-index', help="index of the second relay", type=int)
parser.add_argument('serial_no',  help="serial number of USB relay adapter")
args = parser.parse_args()

hidrelay_yaml=f"""
targets:
  example:
    resources:
      - HIDRelay:
          name: first-relay
          index: {args.first_index}
          match:
            ID_SERIAL_SHORT: {args.serial_no}
      - HIDRelay:
          name: second-relay
          index: {args.second_index}
          match:
            ID_SERIAL_SHORT: {args.serial_no}
    drivers:
      - HIDRelayDriver:
          name: first-driver
          bindings:
            relay: first-relay
      - HIDRelayDriver:
          name: second-driver
          bindings:
            relay: second-relay
      - DigitalOutputPowerDriver:
          name: first-power
          delay: 2.05
          bindings:
            output: first-driver
      - DigitalOutputPowerDriver:
          name: second-power
          delay: 2.50
          bindings:
            output: second-driver
"""

if not args.use_code and not args.use_yaml:
    print("Use at least one of --use-code --use-yaml options.")
    sys.exit(os.EX_USAGE)

if args.use_code:
    t = Target('example')
    HIDRelay(t, name='first-relay', match={"ID_SERIAL_SHORT": args.serial_no}, index=args.first_index)
    HIDRelay(t, name='second-relay', match={"ID_SERIAL_SHORT": args.serial_no}, index=args.second_index)

    t.set_binding_map({"relay": "first-relay"})
    HIDRelayDriver(t, name='first-driver')

    t.set_binding_map({"relay": "second-relay"})
    HIDRelayDriver(t, name='second-driver')

    t.set_binding_map({"output": "first-driver"})
    DigitalOutputPowerDriver(t, name="first-power", delay=2.50)
    firstp = t.get_driver(DigitalOutputPowerDriver, name="first-power")

    t.set_binding_map({"output": "second-driver"})
    DigitalOutputPowerDriver(t, name="second-power", delay=2.50)
    secondp = t.get_driver(DigitalOutputPowerDriver, name="second-power")

    t.get_driver(HIDRelayDriver, name="first-driver").set(True)
    t.get_driver(HIDRelayDriver, name="second-driver").set(True)
    time.sleep(1)

    secondp.cycle()
    firstp.cycle()
    t.cleanup()

if args.use_yaml:
    with NamedTemporaryFile(delete=False) as fp:
        fp.write(hidrelay_yaml.encode('utf-8'))
        fp.close()
        e = Environment(fp.name)
        os.unlink(fp.name)
    print(hidrelay_yaml)
    t = e.get_target('example')

    firstp = t.get_driver(DigitalOutputPowerDriver, name="first-power")
    secondp = t.get_driver(DigitalOutputPowerDriver, name="second-power")

    t.get_driver(HIDRelayDriver, name="first-driver").set(True)
    t.get_driver(HIDRelayDriver, name="second-driver").set(True)
    time.sleep(1)

    secondp.cycle()
    firstp.cycle()
    t.cleanup()
