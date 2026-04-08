#include "pid2.h"
//pid for pt100
float Kp2 = 10.0;  
float Ki2 = 0.1;  
float Kd2 = 1.0;  

float setpoint2 = 30.0; 
float error2 = 0.0;
float last_error2 = 0.0;
float integral2 = 0.0;
float derivative2 = 0.0;
float output2 = 0.0;

uint8_t pwm_duty_cycle2 = 50;  
uint16_t pwm_counter2 = 0;    


float PID_Compute2(float current_temp) {
    error2 = setpoint2 - current_temp; 
    integral2 += error2;         
    derivative2 = error2 - last_error2;  
    last_error2 = error2;
    output2 = Kp2 * error2 + Ki2 * integral2 + Kd2 * derivative2;

    if (output2 > 100.0) output2 = 100.0;
    if (output2 < 0.0) output2 = 0.0;

    return output2;
}