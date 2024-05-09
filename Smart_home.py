import dht
from machine import Pin, ADC, I2C
from time import sleep
from math import ceil
import ssd1306
import network
from BlynkLib import Blynk

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect("Esp", "987654321a")
while not wifi.isconnected():
    pass
print("WiFi Connected Successfully")

# Initialize Blynk
BLYNK_AUTH = "dZQwYDwtpF_Ludo7NflG6zA7H4oX-8i0"
blynk = Blynk(BLYNK_AUTH)

# Define pin number for DHT22 sensor
dht_pin = 4  # GPIO4
MQ135_PIN = 32
RELAY_PIN = 19
RELAY_PIN1=5
AC_PIN = 18
RED_LED_PIN = 23
GREEN_LED_PIN = 15
ORANGE_fan = 12
buzzer_pin=13

# Initialize DHT22 sensor
dht_sensor = dht.DHT22(Pin(dht_pin))

# Initialize ADC for MQ135 (multiple gases) sensor
mq135_sensor = ADC(Pin(MQ135_PIN))
mq135_sensor.atten(ADC.ATTN_11DB)

fan = Pin(RELAY_PIN, Pin.OUT)
Exhaust = Pin(RELAY_PIN1, Pin.OUT)  # Corrected initialization
Ac = Pin(AC_PIN, Pin.OUT)
red_led = Pin(RED_LED_PIN, Pin.OUT)
green_led = Pin(GREEN_LED_PIN, Pin.OUT)
fan_status = Pin(ORANGE_fan, Pin.OUT)
buzzer = Pin(buzzer_pin, Pin.OUT)

# Initialize I2C for OLED display
i2c = I2C(scl=Pin(22), sda=Pin(21))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# Function to read gas levels from MQ135 sensor
def read_gas_levels():
    raw_value = mq135_sensor.read()
    # Example calibration curve (replace with your own)
    # This is just a linear approximation for demonstration purposes
    gas_levels = {
        "CO2": raw_value * 0.1 * (44.01 / 24.45) / 1000,  # CO2 molar mass = 44.01 g/mol
        "NH3": raw_value * 0.05 * (17.03 / 24.45) / 1000,  # NH3 molar mass = 17.03 g/mol
        "NOx": raw_value * 0.03 * (46.01 / 24.45) / 1000,  # NOx molar mass = 46.01 g/mol
        "Alcohol": raw_value * 0.07 * (46.07 / 24.45) / 1000,  # Alcohol molar mass = 46.07 g/mol
        "Benzene": raw_value * 0.09 * (78.11 / 24.45) / 1000,  # Benzene molar mass = 78.11 g/mol
        "Smoke": raw_value * 0.08 * (30.00 / 24.45) / 1000  # Smoke molar mass = 30.00 g/mol
    }
    return gas_levels

# Function to display data on OLED
def display_data(gas_levels, temperature, humidity):
    oled.fill(0)  # Clear the display
    # Display temperature and humidity
    oled.text("Temp: {:.2f} C".format(temperature), 0, 0, 1)
    oled.text("Hum: {:.2f} %".format(humidity), 0, 8, 1)
    # Display gas levels
    y_offset = 16
    for gas, level in gas_levels.items():
        oled.text("{}: {:.2f} ug/m".format(gas, level), 0, y_offset, 1)
        y_offset += 8  # Increase y-offset for better spacing between lines
    oled.show()
    
def display_data_on_blynk(gas_levels,humidity,temperature):
    for i, (gas, level) in enumerate(gas_levels.items(), start=1):
        blynk.virtual_write(i, "{:.2f}".format(level))
    blynk.virtual_write(7,humidity)
    blynk.virtual_write(8,temperature)

while True:
    try:
        # Read sensor data
        dht_sensor.measure()
        t = dht_sensor.temperature()
        temperature = ceil(t)
        h = dht_sensor.humidity()
        humidity = ceil(h)

        gas_levels = read_gas_levels()

        display_data(gas_levels, temperature, humidity)
        display_data_on_blynk(gas_levels,humidity,temperature)


        print("CO2 Level:", gas_levels["CO2"])

        if gas_levels["CO2"] > 0.38:
            
            red_led.on()
            green_led.off()
            Exhaust.value(0)
            buzzer.on()
            blynk.virtual_write(9,1)
            blynk.virtual_write(10,0)
            # Start the buzzer if CO2 level is above 0.18
        elif gas_levels["CO2"] <= 0.38:
            
            # Turn off the buzzer if CO2 level is below 0.18
            red_led.off()
            green_led.on()
            Exhaust.value(1)
            buzzer.off()
            blynk.virtual_write(9,0)
            blynk.virtual_write(10,1)
        else:
            print("Buzzer Off")
            # Turn off the buzzer if CO2 level is below 0.18
            red_led.off()
            green_led.off()
            Exhaust.value(1)
            buzzer.off()
            blynk.virtual_write(9,0)
            blynk.virtual_write(10,0)
            

        # Print sensor data
        print("Temperature: {:.2f}°C".format(temperature))
        print("Humidity: {:.2f}%".format(humidity))

        # Check temperature conditions for fan and AC
        if 33<temperature <=35:
            fan.value(1)
            fan_status.off()
            Ac.off()  # Turn off the AC
        elif temperature <=33:
            print("Turn on AC")
            fan.value(0)
            fan_status.on()
            Ac.off()  # Turn on the AC
        elif 35<=temperature:
            fan.value(1)
            Ac.on()
            fan.value(1)
            fan_status.off()

    except OSError as e:
        print("Failed to read sensor:", e)
    blynk.run()
    sleep(2)  # Wait for 2 seconds before reading again


