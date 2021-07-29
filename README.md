# barometer
A simple project using a Raspberry Pi Pico, Bosch BMP280 and 16x2 LCD display to make a clock featuring current room temperature and air pressure.

The code takes a reading of the temperature and pressure of the BMP280 every second and updates the display.
Every 60 readings the current reading is added to a list, if this list is longer than 185 items long the oldest reading is deleted.
The median of the oldest 10 readings is found and the difference between that and the current reading is also displayed to help determine current trends.
