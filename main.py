# https://github.com/dafvid/micropython-bmp280

# import the required libraries
from bmp280 import *
from machine import Pin, I2C, PWM
import utime


count =0
diff = lambda i,j: ("+ " if i-j >= 0 else "- ") + str(abs(round(i-j,2)))


#set PWM for contrast and led brightness settings
v0 = PWM(Pin(28))
v0.freq(10000)
v0.duty_u16(20000)

a = PWM(Pin(18))
a.freq(10000)
a.duty_u16(65025)



i2c = I2C(0, sda = Pin(16), scl = Pin(17), freq = 400000)

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

press_history=[]

Error=-4.2

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

def median_11(lst):
    n = len(lst)
    s = sorted(lst)
    return s[5] if n==11 else s[0]


def pulseE():
    e.value(1)
    utime.sleep_us(40)
    e.value(0)
    utime.sleep_us(40)
def send2LCD4(BinNum):
    d4.value((BinNum & 0b0001))# >>0)
    d5.value((BinNum & 0b0010))# >>1)
    d6.value((BinNum & 0b0100))# >>2)
    d7.value((BinNum & 0b1000))# >>3)
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

deg=0xdf
up=0b00010000
down=0b11011111
setUpLCD()
rs.value(1)


#half second delay from powering to initial reading to allow sensor to stabilise
utime.sleep(0.5)

min_press=bmp280_object.pressure*0.01 + Error
max_press=bmp280_object.pressure*0.01 + Error

while True:
    # accquire temperature value in celcius
    temperature_c = bmp280_object.temperature # degree celcius
    temp=round(temperature_c,1)
    
    # accquire pressure value
    pressure = bmp280_object.pressure  # pascal
    
    #convert pressure in pascals to mbar and add offset
    pressure_hPa = ( pressure * 0.01 ) + Error
    if pressure_hPa > max_press:
        max_press = pressure_hPa
        
    if pressure_hPa < min_press:
        min_press=pressure_hPa


    rs.value(0)               #send instruction
    send2LCD8(0b00000010)     #move cursor to start of line 1
    rs.value(1)               #send data
    


    dateTime = utime.gmtime(utime.time())
    for x in ("{:02d}:{:02d}:{:02d}  {:02d}/{:02d}/{:04d}".format(dateTime[3],dateTime[4],dateTime[5],dateTime[2],dateTime[1],dateTime[0])):
        send2LCD8(ord(x))
    

#add every 60th reading to history(~one a minute)    

    if count ==0:
        press_history.append(pressure_hPa)
        while len (press_history) > 185: # if list is longer than maximum(~3 hours, 5 minutes), delete oldest value
            del press_history[0]
    count+=1
    if count >= 60:
        count=0
    #oldest 11 readings, actually 11 minute history to simplify median calculation
    ten_min=press_history[:11]


    #move to start of line 3 
    rs.value(0)
    send2LCD8(0b10010100)
    rs.value(1)
    
    for x in 'max: '+'{:.2f}'.format(max_press):
        send2LCD8(ord(x))


        
    #move to start of line 2
    rs.value(0)
    send2LCD8(0b11000000)
    rs.value(1)
    for x in "{:.2f}".format(pressure_hPa) +" mbar "+diff(pressure_hPa, median_11(ten_min))+ ' ' :
        send2LCD8(ord(x))    



    #move to start of line 4    
    rs.value(0)
    send2LCD8(0b11010100)
    rs.value(1)
    
    for x in 'min: '+ '{:.2f}'.format(min_press):#+' max: '+'{:.2f}'.format(max_press):
        send2LCD8(ord(x))   

        
    rs.value(0)
    send2LCD8(0b10100010)
    rs.value(1)    
        
    for x in str(temp):
        send2LCD8(ord(x))
    send2LCD8(deg)
    send2LCD8(ord('C'))    


    #wait one second before taking further reading and updating display
    utime.sleep(1)
