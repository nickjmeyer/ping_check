import platform    # For getting the operating system name
import subprocess  # For executing a shell command
import matplotlib.pyplot as plt
import time
import datetime

def execute(command):
    return subprocess.run(command, capture_output = True)

def ping(host: str):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower()=='windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', "-W", "500", host]

    return execute(command).returncode == 0


def get_now():
    return datetime.datetime.now()

def as_seconds(seconds):
    return datetime.timedelta(0, seconds)

def get_sample():
    return get_now(), ping("8.8.8.8")

def get_wifi_ssid():
    command = ["networksetup", "-getairportnetwork", "en0"]
    result = execute(command).stdout.decode("utf-8")

    start = "Current Wi-Fi Network: "
    if result.startswith(start):
        ssid = result[23:].strip()
        return ssid.replace(" ", "_")
    return "Unknown"

def get_base_file_name(start_time, wifi_ssid):
    time_str = start_time.strftime("%Y-%m-%d_%H:%M:%S")
    file_name = f"data/{wifi_ssid}_{time_str}"
    return file_name

def get_data_file_name(start_time, wifi_ssid):
    return f"{get_base_file_name(start_time, wifi_ssid)}.csv"

def get_log_file_name(start_time, wifi_ssid):
    return f"{get_base_file_name(start_time, wifi_ssid)}.log"

def get_headers():
    return ["tov", "result"]

def index_to_range(index):
    if index == 0:
        return "        0%"
    if index == 11:
        return "      100%"
    return f"{((index-1)*10):2}% - {(index*10):3}%"

class Logger:
    def __init__(self, log_file):
        self._log_file = log_file
        with open(self._log_file, "w") as f:
            f.write(f"starting log: {get_now()}\n")

    def __call__(self, str):
        print(str)
        with open(self._log_file, "a") as f:
            f.write(str)
            f.write("\n")

if __name__ == "__main__":
    data = []

    window_s = as_seconds(30)
    sample_period_s = as_seconds(1)
    start_time = get_now()
    last_sample_time = start_time
    next_sample_time  = last_sample_time + sample_period_s

    min_rate = 1.0

    wifi_ssid = get_wifi_ssid()
    data_file_name = get_data_file_name(start_time, wifi_ssid)

    with open(data_file_name, "w") as f:
        f.write(",".join(get_headers()))
        f.write("\n")
        
    log_file_name = get_log_file_name(start_time, wifi_ssid)
    logger = Logger(log_file_name)

    percentiles = [0]*12

    num_samples = 0

    while True:
        time_to_sleep_s = (next_sample_time - get_now()).total_seconds()
        next_sample_time += sample_period_s
        time.sleep(max(time_to_sleep_s, 0))

        last_sample_time, result = get_sample()

        data.append((last_sample_time, result))
        num_samples += 1
        with open(data_file_name, "a") as f:
            f.write(",".join(map(str, data[-1])))
            f.write("\n")

        min_time = last_sample_time - window_s

        while len(data) > 0 and data[0][0] < min_time:
            data = data[1:]

        num_success = sum(i for _, i in data)
        avg_success = float(num_success) / len(data)

        min_rate = min(min_rate, avg_success)

        if num_success == 0:
            percentile_index = 0
        elif num_success == len(data):
            percentile_index = 11
        else:
            percentile_index = int(avg_success * 10) + 1

        percentiles[percentile_index] += 1

        uptime = last_sample_time - start_time

        logger("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        logger(f"Current time: {last_sample_time}")
        logger(f"Network: {wifi_ssid}")
        logger(f"Connectivity data:")
        logger(f"        Avg Success: {avg_success}")
        logger(f"              Count: {len(data)}")
        logger(f"        Min Success: {min_rate}")
        logger(f"        Total count: {num_samples}")
        logger(f"             Uptime: {uptime}")
        logger("         Percentiles:")
        for i in range(12):
            logger(f"                     {index_to_range(i)}: {int((percentiles[i] / num_samples)*100):3}% ({percentiles[i]})")
