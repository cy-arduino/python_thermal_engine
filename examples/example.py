from thermal_engine import ThermalEngine, Sensor, Rule, Device
import logging
import time


##########
class Temp(Sensor):
    def get_value(self):
        ret = {'temp': 0}
        try:
            with open('temp_{}'.format(self.name), 'r') as f:
                ret['temp'] = int(f.read())
        except Exception as e:
            self.log.error(e)

        self.log.debug("get_value: %s", ret)
        return ret


class CoolDownCpu(Rule):
    def __init__(self):
        super(CoolDownCpu, self).__init__(self.__class__.__name__)

        self.add_sensor_list(['temp_cpu'])
        self.add_device_list(['fan_cpu', 'fan_sys'])

    def gen_action(self):
        self.log.debug(self._sensor_value)

        new_actions = {}
        cpu_temp = self._sensor_value.get('temp_cpu', {}).get('temp', None)

        # default full speed
        fan_cpu = 1.0
        fan_sys = 1.0

        if cpu_temp:
            if cpu_temp < 30:
                fan_cpu = 0
                fan_sys = 0.5
            elif cpu_temp < 60:
                fan_cpu = 0.5
                fan_sys = 0.8

        new_actions['fan_cpu'] = {'speed': fan_cpu}
        new_actions['fan_sys'] = {'speed': fan_sys}

        return new_actions


class CoolDownSys(Rule):
    def __init__(self):
        super(CoolDownSys, self).__init__(self.__class__.__name__)
        self.add_sensor_list(['temp_cpu', 'temp_sys'])
        self.add_device_list(['fan_sys'])

    def gen_action(self):
        self.log.debug(self._sensor_value)

        new_actions = {}

        cpu_temp = self._sensor_value.get('temp_cpu', {}).get('temp', None)
        sys_temp = self._sensor_value.get('temp_sys', {}).get('temp', None)
        self.log.debug('cpu_temp=%s, sys_temp=%s', cpu_temp, sys_temp)
        # default full speed
        fan_sys_speed = 1.0

        if sys_temp:
            if sys_temp < 30:
                fan_sys_speed = 0
            elif sys_temp < 50:
                fan_sys_speed = 0.4
            else:
                if cpu_temp and cpu_temp < 80:
                    fan_sys_speed = 0.9

        self.log.debug('fan_sys_speed: %s', fan_sys_speed)
        new_actions['fan_sys'] = {'speed': fan_sys_speed}

        return new_actions


class CoolDownWifi(Rule):
    def __init__(self):
        super(CoolDownWifi, self).__init__(self.__class__.__name__)
        self.add_sensor_list(['temp_wifi'])
        self.add_device_list(['fan_sys'])

    def gen_action(self):
        self.log.debug(self._sensor_value)

        new_actions = {}

        temp_wifi = self._sensor_value.get('temp_wifi', {}).get('temp', None)

        fan_sys = 0
        if temp_wifi and temp_wifi > 50:
            fan_sys = 0.7

        new_actions['fan_sys'] = {'speed': fan_sys}
        return new_actions


class Fan(Device):
    def __init__(self, name):
        super(Fan, self).__init__(name)
        self.fan_speed = None

    def apply_action(self):
        self.log.debug("actions: %s", self._actions)

        # choose fastest speed
        max_fan_speed = 0.0
        action_name = ''
        for name, action in self._actions.iteritems():
            if action['speed'] > max_fan_speed:
                max_fan_speed = action['speed']
                action_name = name

        if self.fan_speed != max_fan_speed:
            self.fan_speed = max_fan_speed
            self.log.info("apply action from <%s>, speed=%s", action_name,
                           max_fan_speed)


################################
def test_thermal_engine():
    te = ThermalEngine()

    temp_cpu = Temp('temp_cpu').set_polling(1)
    if not te.reg_sensor(temp_cpu):
        print("reg failed")

    temp_sys = Temp('temp_sys').set_polling(2)
    if not te.reg_sensor(temp_sys):
        print("reg failed")

    temp_wifi = Temp('temp_wifi').set_polling(3)
    if not te.reg_sensor(temp_wifi):
        print("reg failed")

    r1 = CoolDownCpu()
    if not te.reg_rule(r1):
        print("reg failed")


    r2 = CoolDownSys()
    if not te.reg_rule(r2):
        print("reg failed")

    r3 = CoolDownWifi()
    if not te.reg_rule(r3):
        print("reg failed")

    fan_cpu = Fan('fan_cpu')
    if not te.reg_device(fan_cpu):
        print("reg failed")

    fan_sys = Fan('fan_sys')
    if not te.reg_device(fan_sys):
        print("reg failed")

    te.start()
    time.sleep(10)
    te.stop()


###############################
if __name__ == '__main__':
    LOG_FMT = "%(asctime)s [%(levelname)s] " \
              "%(filename)s:%(lineno)s %(name)s %(funcName)s() : %(message)s"
    logging.basicConfig(level=logging.INFO, format=LOG_FMT)

    test_thermal_engine()


