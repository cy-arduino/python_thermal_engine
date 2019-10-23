import unittest
from unittest import TestCase
from thermal_engine import ThermalEngine, Rule, Sensor, Device
from pollinghub import Pollee
import time
import threading
import logging


class TestThermalEngine(TestCase):
    def setUp(self):
        if not hasattr(self, 'log'):
            self.log = logging.getLogger(self.__class__.__name__)

    def tearDown(self):
        pass

    def _test_rule(self):
        pass

    def _test_sensor(self):
        poll_interval = 10

        s1 = S1('s1')
        s1.set_polling(poll_interval)
        p1 = s1.get_pollee()
        self.assertTrue(isinstance(p1, Pollee))
        self.assertEqual(p1.period, poll_interval)

    def _test_device(self):
        pass

    def test_thermal_engine(self):
        # basic tests
        self._test_rule()
        self._test_sensor()
        self._test_device()

        # R1:
        #   sensor: S1, S2
        #   device: D1, D2, D3
        # R2:
        #   sensor: S1
        #   device: D2, D4

        s1 = S1('s1')
        s2 = S1('s2')
        r1 = R1('r1')
        r2 = R1('r2')
        d1 = D1('d1')
        d2 = D1('d2')
        d3 = D1('d3')
        d4 = D1('d4')

        # config
        r1.add_sensor_list(['s1', 's2'])
        r1.add_device_list(['d1', 'd2', 'd3'])
        r2.add_sensor_list(['s1'])
        r2.add_device_list(['d2', 'd4'])

        # thermal engine
        te = ThermalEngine()
        te.reg_sensor(s1)
        te.reg_sensor(s2)
        te.reg_rule(r1)
        te.reg_rule(r2)
        te.reg_device(d1)
        te.reg_device(d2)
        te.reg_device(d3)
        te.reg_device(d4)

        te.start()

        s1_temp = 50
        s1.set_temp(s1_temp)
        s1.update()
        time.sleep(1)
        self.assertEqual(s1_temp, d1.get_value())
        self.assertEqual(s1_temp, d2.get_value())
        self.assertEqual(s1_temp, d3.get_value())

        s2_temp = 60
        s2.set_temp(s2_temp)
        s2.update()
        time.sleep(1)
        self.assertEqual(s2_temp, d1.get_value())
        self.assertEqual(s2_temp, d2.get_value())
        self.assertEqual(s2_temp, d3.get_value())
        self.assertEqual(s1_temp, d4.get_value())

        te.stop()


class S1(Sensor):
    def __init__(self, *args, **kwargs):
        super(S1, self).__init__(*args, **kwargs)
        self.temp = None

    def set_temp(self, temp):
        self.temp = temp

    def get_value(self):
        return {'temp': self.temp}


class R1(Rule):
    # forward max temp to all devices
    def gen_action(self):
        max_temp = None
        for sensor_name, sensor_value in self.get_sensor_value().iteritems():
            if sensor_value['temp'] > max_temp:
                max_temp = sensor_value['temp']

        ret = {}
        for dev_name in self.get_device_list():
            ret[dev_name] = {'temp': max_temp}

        return ret


class D1(Device):
    def __init__(self, *args, **kwargs):
        super(D1, self).__init__(*args, **kwargs)
        self._value = None

    def apply_action(self):
        self.log.debug("actions: %s", self._actions)

        for rule_name, action in self.get_actions().iteritems():
            if self._value is None or action['temp'] > self._value:
                self._value = action['temp']

        self.log.debug("update temp=%s", self._value)

    def get_value(self):
        return self._value


if __name__ == '__main__':
    LOG_FMT = "%(asctime)s [%(levelname)s] " \
              "%(filename)s:%(lineno)s %(name)s %(funcName)s() : %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=LOG_FMT)
    unittest.main()
