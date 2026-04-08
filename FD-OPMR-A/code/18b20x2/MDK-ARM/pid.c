#include "pid.h"
#include "menu.h"
//pid for 18b20
float Kp = 200.0;  
float Ki = 0.0001;  
float Kd = 1.0;  

float setpoint = 26.0; 
float error = 0.0;
float last_error = 0.0;
float integral = 0.0;
float derivative = 0.0;
float output = 0.0;

uint8_t pwm_duty_cycle = 80;  
uint16_t pwm_counter = 0;    


float PID_Compute(float current_temp) {
		setpoint=temp_light_set;
    error = setpoint - current_temp; 
    integral += error;   
    derivative = error - last_error;  
    last_error = error;
    output = Kp * error + Ki * integral + Kd * derivative;

    if (output > 100.0) output = 100.0;
    if (output < 0.0) output = 0.0;

    return output;
}
