The way a servo motor reads the information it's being sent is by using an electrical signal called PWM. 
PWM stands for "Pulse Width Modulation". That just means sending ON electrical signals for a certain amount of time, 
followed by an OFF period, repeated hundreds of times a second. The amount of time the signal 
is on sets the angle the servo motor will rotate to. In most servos, the expected frequency is 50Hz, 
or 3000 cycles per minute. Servos will set to 0 degrees if given a signal of .5 ms, 90 when given 1.5 ms, and 180 when given 2.5ms pulses. 
This translates to about 2.5-12.5% duty in a 50Hz PWM cycle.

Normally, in any servo the duty cycle is from 2.5-12.5%, so to find the duty cycle of any angle, divide it by 18 and add the minimun value to the result.
In SG90, freq is 50Hz and duty cycle is 2-12%, so to find the duty cycle corresponding to, say 90 degree, divide 90 by 18, we get 5 and adding the minimum value which is 2 in this case, so the duty cycle corresponding to 90 degree is 7%.
