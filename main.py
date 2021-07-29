# https://github.com/dafvid/micropython-bmp280

# import the required libraries
from bmp280 import *
from machine import Pin, I2C, PWM
import utime


count =0
diff = lambda i: ("+" if i > 0 else "") + str(round(i,1))
v0 = PWM(Pin(28))

v0.freq(10000)
v0.duty_u16(20000)

a = PWM(Pin(18))
a.freq(10000)
a.duty_u16(65025)



#i2c = I2C(0, sda = Pin(16), scl = Pin(17), freq = 400000)

#pins out to LCD display
rs = machine.Pin(27,machine.Pin.OUT)
e = machine.Pin(26,machine.Pin.OUT)
d4 = machine.Pin(22,machine.Pin.OUT)
d5 = machine.Pin(21,machine.Pin.OUT)
d6 = machine.Pin(20,machine.Pin.OUT)
d7 = machine.Pin(19,machine.Pin.OUT)

# declare pins for I2C communication
sclPin = Pin(17) # serial clock pin
sdaPin = Pin(16) # serial data pin

history=[] #create empty list for historical readings

# Initiate I2C 
i2c_object = I2C(0,              # positional argument - I2C id
                 scl = sclPin,   # named argument - serial clock pin
                 sda = sdaPin,   # named argument - serial data pin
                 freq = 1000000) # named argument - i2c frequency


bmp280_object = BMP280(i2c_object,
                       addr = 0x76, # change it 
                       use_case = BMP280_CASE_WEATHER)

# configure the sensor
# These configuration settings give most accurate values in my case
# tweak them according to your own requirements

bmp280_object.power_mode = BMP280_POWER_NORMAL
bmp280_object.oversample = BMP280_OS_HIGH
bmp280_object.temp_os = BMP280_TEMP_OS_8
bmp280_object.press_os = BMP280_TEMP_OS_4
bmp280_object.standby = BMP280_STANDBY_250
bmp280_object.iir = BMP280_IIR_FILTER_2

#function to find median of a list
def median(lst):
    n = len(lst)
    s = sorted(lst)
    return (sum(s[n//2-1:n//2+1])/2.0, s[n//2])[n % 2] if n else None


def pulseE():
    e.value(1)
    utime.sleep_us(40)
    e.value(0)
    utime.sleep_us(40)
    
def send2LCD4(BinNum):
    d4.value((BinNum & 0b00000001))# >>0)
    d5.value((BinNum & 0b00000010))# >>1)
    d6.value((BinNum & 0b00000100))# >>2)
    d7.value((BinNum & 0b00001000))# >>3)
    pulseE()
def send2LCD8(BinNum):
    d4.value((BinNum & 0b00010000))# >>4)
    d5.value((BinNum & 0b00100000))# >>5)
    d6.value((BinNum & 0b01000000))# >>6)
    d7.value((BinNum & 0b10000000))# >>7)
    pulseE()
    d4.value((BinNum & 0b00000001))# >>0)
    d5.value((BinNum & 0b00000010))# >>1)
    d6.value((BinNum & 0b00000100))# >>2)
    d7.value((BinNum & 0b00001000))# >>3)
    pulseE()
def setUpLCD():
    rs.value(0)
    send2LCD4(0b0011)#8 bit
    send2LCD4(0b0011)#8 bit
    send2LCD4(0b0011)#8 bit
    send2LCD4(0b0010)#4 bit
    send2LCD8(0b00101000)#4 bit,2 lines?,5*8 bots
    send2LCD8(0b00001100)#lcd on, blink off, cursor off.
    send2LCD8(0b00000110)#increment cursor, no display shift
    send2LCD8(0b00000001)#clear screen
    utime.sleep_ms(2)#clear screen needs a long delay

deg=0b11011111
up=0b00010000
down=0b11011111
setUpLCD()
rs.value(1)
while True:
    # accquire temperature value in celcius
    temperature_c = bmp280_object.temperature # degree celcius
    temp=round(temperature_c,1)
    
    # accquire pressure value
    pressure = bmp280_object.pressure  # pascal
    


    pressure_hPa = ( pressure * 0.01 ) 

    press = "{:.1f}".format(pressure_hPa) #pressure as a string with 1dp


    rs.value(0)               #send instruction
    send2LCD8(0b00000010)     #move cursor to start of line 1
    rs.value(1)               #send data
    
    for x in str(temp):       #print temperature
        send2LCD8(ord(x))
    send2LCD8(deg)
    send2LCD8(ord('C'))

    dateTime = utime.gmtime(utime.time())
    for x in ("  {:02d}:{:02d}:{:02d}".format(dateTime[3],dateTime[4],dateTime[5])):
        send2LCD8(ord(x))
    
    
    rs.value(0)
    send2LCD8(0b11000000)
    rs.value(1)
    
    
    
    
#     for x in press +" mbar "+str(pressure_hPa-median(ten_min)):
#         send2LCD8(ord(x))
    #history.append(pressure_hPa) #add current reading to end of list
    #history.append(temp) #add current reading to end of list


    

    if count ==0:                #when the count is zero, at the start and then every minute, add current reading into history list
        history.append(pressure_hPa) 
        while len (history) > 185: # if list is longer than maximum, delete oldest value
            del history[0]
    count+=1
    if count >= 59: #reset counter after ~ 1 minute
        count=0
    #print (len(history))
    #print (history[-1200:])
    ten_min=history[:10] # a second list containing the oldest 10 readings

    for x in press +" mbar "+diff(pressure_hPa-median(ten_min)): #send current reading and difference between current and median of 10 oldest readings(from 2 hours 55 mins to 3 hours 5 minutes ago)
        send2LCD8(ord(x))
    utime.sleep(1)
