"""Battery and power model of the lab robot: a 3S lithium-ion pack feeding a 12 V bus, a 5 V rail
(host computer and sensors, through a buck converter) and the four drive motors.

  pack current  I = (P_5V / eta_5V + P_motors) / V_pack
  P_5V          = host + LiDAR + camera + IMU (constant, from the power budget below)
  P_motors      = P_idle_drive + k_v |v| + k_w |wz| + k_a |dv/dt|      (a fitted, first-order drive model)
  V_pack        = OCV(SoC) - I R_int ;  SoC falls by I dt / C

Publishes: battery (sensor_msgs/BatteryState), voltage (std_msgs/Float32, pack volts, 10 Hz),
           power/current (std_msgs/Float32, pack amps), power/rails (std_msgs/Float32MultiArray: V5, I5, P_total).
time_scale > 1 speeds the discharge up (e.g. 30 = one simulated second drains 30 s of charge), so an
endurance test fits inside a lab session. The low-voltage alarm is logged at 9.6 V (3.2 V per cell).
"""
import math

from rcl_interfaces.msg import SetParametersResult

import numpy as np
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import BatteryState
from std_msgs.msg import Float32, Float32MultiArray

# 3S open-circuit voltage against state of charge (typical Li-ion NMC, per pack)
SOC = [0.0, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
OCV = [9.00, 10.20, 10.65, 10.95, 11.10, 11.25, 11.40, 11.55, 11.75, 11.95, 12.20, 12.55]


class Battery(Node):
    def __init__(self):
        super().__init__('battery')
        p = self.declare_parameter
        self.capacity_ah = p('capacity_ah', 6.0).value
        self.r_int = p('internal_resistance_ohm', 0.09).value
        self.soc = p('initial_soc', 0.95).value
        self.eta_5v = p('buck_efficiency', 0.85).value
        self.p_5v = p('load_5v_w', 16.5).value          # host 12 W + LiDAR 2.5 W + camera 1.5 W + IMU/misc 0.5 W
        self.p_drive_idle = p('drive_idle_w', 1.5).value
        self.k_v = p('k_v_w_per_mps', 28.0).value
        self.k_w = p('k_w_w_per_radps', 6.0).value
        self.k_a = p('k_a_w_per_mps2', 10.0).value
        self.time_scale = p('time_scale', 1.0).value
        self.alarm_v = p('alarm_voltage', 9.6).value
        self.v = self.w = self.prev_v = 0.0
        self.last = None
        self.alarmed = False
        self.create_subscription(Odometry, 'ground_truth/odom', self.on_truth, 10)
        self.pub_state = self.create_publisher(BatteryState, 'battery', 10)
        self.pub_v = self.create_publisher(Float32, 'voltage', 10)
        self.pub_i = self.create_publisher(Float32, 'power/current', 10)
        self.pub_rails = self.create_publisher(Float32MultiArray, 'power/rails', 10)
        self.create_timer(0.1, self.tick)
        self.add_on_set_parameters_callback(self.on_params)

    def on_params(self, params):
        """time_scale (and the load figures) can be changed while running: ros2 param set /battery time_scale 60.0"""
        names = {'time_scale': 'time_scale', 'load_5v_w': 'p_5v', 'buck_efficiency': 'eta_5v'}
        for p in params:
            if p.name in names:
                setattr(self, names[p.name], float(p.value))
        return SetParametersResult(successful=True)

    def on_truth(self, msg):
        t = msg.twist.twist
        self.v = math.hypot(t.linear.x, t.linear.y)
        self.w = abs(t.angular.z)

    def tick(self):
        now = self.get_clock().now()
        if self.last is None:
            self.last = now
            return
        dt = (now - self.last).nanoseconds * 1e-9
        self.last = now
        if dt <= 0.0:
            return
        acc = abs(self.v - self.prev_v) / dt
        self.prev_v = self.v
        p_motor = self.p_drive_idle + self.k_v * self.v + self.k_w * self.w + self.k_a * acc
        ocv = float(np.interp(self.soc, SOC, OCV))
        p_total = self.p_5v / self.eta_5v + p_motor
        # solve V = OCV - I R, P = V I  ->  I = (OCV - sqrt(OCV^2 - 4 R P)) / (2 R)
        disc = max(ocv * ocv - 4.0 * self.r_int * p_total, 0.0)
        i = (ocv - math.sqrt(disc)) / (2.0 * self.r_int)
        v_pack = ocv - i * self.r_int
        self.soc = max(self.soc - i * dt * self.time_scale / 3600.0 / self.capacity_ah, 0.0)
        if v_pack < self.alarm_v and not self.alarmed:
            self.alarmed = True
            self.get_logger().warn('LOW BATTERY: pack at %.2f V (alarm %.1f V) - stop and change the pack'
                                   % (v_pack, self.alarm_v))

        st = BatteryState()
        st.header.stamp = now.to_msg()
        st.voltage, st.current = float(v_pack), float(-i)
        st.charge = float(self.soc * self.capacity_ah)
        st.capacity = st.design_capacity = float(self.capacity_ah)
        st.percentage = float(self.soc)
        st.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_DISCHARGING
        st.power_supply_technology = BatteryState.POWER_SUPPLY_TECHNOLOGY_LION
        st.present = True
        st.cell_voltage = [float(v_pack / 3.0)] * 3
        self.pub_state.publish(st)
        self.pub_v.publish(Float32(data=float(v_pack)))
        self.pub_i.publish(Float32(data=float(i)))
        rails = Float32MultiArray()
        rails.data = [5.0 - 0.02 * self.p_5v / 5.0, self.p_5v / 5.0, float(p_total)]
        self.pub_rails.publish(rails)


def main():
    rclpy.init()
    node = Battery()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
