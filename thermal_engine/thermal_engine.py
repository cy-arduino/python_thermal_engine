import abc
import logging
from pollinghub import Pollee, PollingHub


# TODO: use specific Exception?
# TODO: compatible with Python3
#  (dict.iteritems->dict.items, dict.itervalues->dict.values...)
class Sensor(object):
    def __init__(self, name=None):
        self.name = name if name else self.__class__.__name__
        self.log = logging.getLogger(self.name)
        self._polling_period = None
        self._pollee = None
        self._rules = list()  # [rule1, rule2, ...]
        self._value = None

    # return sensor value
    @abc.abstractmethod
    def get_value(self):
        pass

    def update(self):
        self.log.debug("in")
        new_value = self.get_value()
        if self._value != new_value:
            self._value = new_value
            self.log.info("value change: %s", self._value)
            for r in self._rules:
                r.update_sensor_value(self.name, self._value)

    def _gen_pollee(self):
        if self._polling_period and self._polling_period > 0:
            self._pollee = Pollee(self.name, self._polling_period, self.update)

    def set_polling(self, period):
        self.log.info("polling period=%s", period)

        self._polling_period = period
        self._gen_pollee()

        return self

    def get_pollee(self):
        if not self._pollee:
            self._gen_pollee()

        return self._pollee

    def update_rules(self, all_rules):
        del self._rules[:]
        for rule in all_rules.itervalues():
            if rule.include_sensor(self.name):
                self._rules.append(rule)

    def reset(self):
        self._pollee = None
        self._value = None
        del self._rules[:]
        self._gen_pollee()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.__repr__()


class Rule(object):
    def __init__(self, name=None):
        self.name = name if name else self.__class__.__name__
        self.log = logging.getLogger(self.name)
        self._sensor_list = list()  # {sensor_name1, sensor_name2, ...}
        self._device_list = list()  # {dev_name1, dev_name2, ...}

        self._devices = dict()
        self._actions = dict()  # {dev_neme1: action1, dev_name2: action2}
        self._sensor_value = dict()

    def update_sensor_value(self, sensor_name, value):
        if sensor_name not in self._sensor_list:
            raise Exception(
                "sensor <{}> not exist in rule {}".format(
                    sensor_name, self.name))

        if sensor_name in self._sensor_value \
                and self._sensor_value[sensor_name] == value:
            # self.log.debug("sensor value not changed. do nothing...")
            return

        self.log.debug('update sensor value: %s %s', sensor_name, value)

        self._sensor_value[sensor_name] = value

        self.log.debug("all sensor value=%s", self._sensor_value)

        new_actions = self.gen_action()

        for dev_name, action in new_actions.iteritems():
            if dev_name not in self._device_list:
                # log error only?
                # self._log.error("device <%s> not exist", dev_name)
                raise Exception("device {} not valid!".format(dev_name))

            if dev_name not in self._actions \
                    or self._actions.get(dev_name, None) != action:
                self.log.info("update action <%s> to device <%s>", action,
                              dev_name)
                self._actions[dev_name] = action
                self._devices[dev_name].update_action(self.name, action)

    def get_sensor_value(self, sensor_name):
        return self._sensor_value.get(sensor_name, dict())

    def include_sensor(self, sensor_name):
        return sensor_name in self._sensor_list

    def add_sensor_list(self, sensor_list):
        for s in sensor_list:
            if s in self._sensor_list:
                raise Exception("sensor <{}> already exist".format(s))
            else:
                self._sensor_list.append(s)

    def add_device_list(self, device_list):
        for d in device_list:
            if d in self._device_list:
                raise Exception("device <{}> already exist".format(d))
            else:
                self._device_list.append(d)

    def get_sensor_list(self):
        return self._sensor_list

    def get_sensor_value(self):
        return self._sensor_value

    def get_device_list(self):
        return self._device_list

    # return: {dev_name: action, ...}
    @abc.abstractmethod
    def gen_action(self):
        pass

    def update_devices(self, all_devices):
        self._devices.clear()
        for dev_name in all_devices:
            if dev_name in self._device_list:
                self._devices[dev_name] = all_devices[dev_name]

    def reset(self):
        self._devices.clear()
        self._actions.clear()
        self._sensor_value.clear()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.__repr__()


class Device(object):
    def __init__(self, name=None):
        self.name = name if name else self.__class__.__name__
        self.log = logging.getLogger(self.name)
        self._actions = dict()  # {rule_name1: action1, ...}

    def update_action(self, name, data):
        if name in self._actions and self._actions[name] == data:
            # do nothing
            return

        self._actions[name] = data
        self.apply_action()

    def get_actions(self):
        return self._actions

    # select best data in self._actions and apply
    @abc.abstractmethod
    def apply_action(self):
        pass

    def reset(self):
        self._actions.clear()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.__repr__()


class ThermalEngine:
    def __init__(self, name=None):
        self.name = name if name else self.__class__.__name__
        self.log = logging.getLogger(self.name)
        self._rules = dict()
        self._sensors = dict()
        self._devices = dict()
        self._polling_hub = PollingHub()
        self._running = False

    def reg_sensor(self, sensor):
        self.log.info('register %s', sensor)

        if not isinstance(sensor, Sensor):
            self.log.error("invalid input type")
            return False

        if self._running:
            self.log.error("add sensor when running")
            return False

        if sensor.name in self._sensors:
            self.log.error("%s exist", sensor)
            return False

        self._sensors[sensor.name] = sensor
        return True

    def reg_device(self, device):
        self.log.info('register %s', device)

        if not isinstance(device, Device):
            self.log.error("invalid input type")
            return False

        if self._running:
            self.log.error("add device when running")
            return False

        if device.name in self._devices:
            self.log.error("%s exist", device.name)
            return False

        self._devices[device.name] = device
        return True

    def reg_rule(self, rule):
        self.log.info('register %s', rule)

        if not isinstance(rule, Rule):
            self.log.error("invalid input type")
            return False

        if self._running:
            self.log.error("add rule when running")
            return False

        if rule.name in self._rules:
            self.log.error("%s exist", rule.name)
            return False

        self._rules[rule.name] = rule
        return True

    def _refresh_sensor(self, sensor):
        sensor.reset()
        sensor.update_rules(self._rules)
        if sensor.get_pollee():
            self._polling_hub.reg(sensor.get_pollee())

    def _refresh_rule(self, rule):
        rule.reset()
        rule.update_devices(self._devices)

    def start(self):
        for s in self._sensors.itervalues():
            self._refresh_sensor(s)

        for r in self._rules.itervalues():
            self._refresh_rule(r)

        for d in self._devices.itervalues():
            d.reset()

        self._running = True
        self._polling_hub.start()

    def stop(self):
        self._polling_hub.stop()
        self._running = False
