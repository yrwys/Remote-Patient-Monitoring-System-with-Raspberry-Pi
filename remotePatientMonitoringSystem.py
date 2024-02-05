import matplotlib.pyplot as plt
import matplotlib.animation as animation
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
from scipy import stats
import multiprocessing
import datetime
import time
import BlynkLib

SPI_PORT = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
x_len = 150
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
xs = list(range(0, x_len))
ys = [0] * x_len
ax.set_ylim(-5, 5)
ecg = []
timeecg = []
line, = ax.plot(xs, ys)
lastBeatTime = 0
low_count = 0
high_count = 0
blynk = BlynkLib.Blynk('1AB76gAJZ-M4BUimU93Z3NcVUQjl_3Z6')

def figure(values, window):
    if window < 1:
        raise ValueError("Window size must be at least 1.")

    filtered = []

    for i in range(len(values)):
        if i < window - 1:
            windowVals = values[0:i + 1]
        else:
            windowVals = values[i - window + 1 : i + 1]
        avg = sum(windowVals) / len(windowVals)
        filtered.append(avg)

    return filtered

def calculation():
    global lastBeatTime
    global low_count
    global high_count

    currentTime = time.time() * 1000
    beatInterval = currentTime - lastBeatTime
    lastBeatTime = currentTime
    beatPerMinute = 60000.0 / beatInterval
    print(f"BPM: {beatPerMinute:.2f}")
    print(f"IBI: {beatInterval:.2f} ms")
    
    blynk.virtual_write(5, beatPerMinute)
    blynk.virtual_write(10, beatPerMinute)
    time.sleep(0.1)

    if beatPerMinute < 60:
        low_count += 1
        if low_count >= 5:
            blynk.log_event("alert", "The patient's heart rate is decreasing!")
            low_count = 0
    else:
        low_count = 0
    
    if beatPerMinute > 100:
        high_count += 1
        if high_count >= 5:
            blynk.log_event("alert", "The patient's heart rate is increasing!")
            high_count = 0
    else:
        high_count = 0
    
    return (beatPerMinute, beatInterval)

def plotter(i, ys):
    adc_value = mcp.read_adc(0)
    ys.append(adc_value)
    ys = ys[-x_len:]
    y_ = stats.zscore(ys)
    y = figure(y_, 2)
    y = y[-x_len:]
    ecg.append(y[x_len - 1])
    timeecg.append(datetime.datetime.now())

    line.set_ydata(y)
    
    if i % 60 == 0:
        calculation()
        
    return line,

def loop():
    ani = animation.FuncAnimation(
        fig, plotter, fargs=(ys,), interval=3, blit=True
    )
    plt.show()
    
@blynk.on("connected")
def blynk_connected_handler():
    print("Connected to Blynk server.")

if __name__ == '__main__':
    p1 = multiprocessing.Process(target=loop)
    p1.start()
    p1.join()
    blynk.run()
