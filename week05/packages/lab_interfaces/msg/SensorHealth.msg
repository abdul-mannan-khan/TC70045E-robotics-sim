# Health summary of one sensor stream, published by lab_sensing/sensor_monitor (TC70045E Week 5).
std_msgs/Header header
float32 imu_rate_hz        # arrival rate at this node, host (wall) clock
float32 imu_jitter_ms      # standard deviation of the arrival interval, host clock
float32 stamp_rate_hz      # rate from the header stamps, i.e. in the sensor's (simulated) clock
float32 stamp_jitter_ms    # standard deviation of the header-stamp interval
float32 accel_rms          # RMS |a| over the window, m/s^2
float32 gyro_rms           # RMS |w| over the window, rad/s
float32 body_speed         # sqrt(vx^2 + vy^2) from /vel_raw, m/s
float32 battery_v          # latest /voltage sample, V
uint32  samples            # samples in the window
uint32  missed             # samples expected from the stamps but not received
bool    healthy            # stamp rate within tolerance AND battery above threshold
