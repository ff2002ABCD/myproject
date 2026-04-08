#ifndef __PID_H
#define __PID_H
#include "main.h"
#define PWM_GPIO_PORT GPIOB
#define PWM_GPIO_PIN  GPIO_PIN_12
#define PWM_PERIOD    100  
extern uint8_t pwm_duty_cycle;  
extern uint16_t pwm_counter;    
float PID_Compute(float current_temp);
#endif
