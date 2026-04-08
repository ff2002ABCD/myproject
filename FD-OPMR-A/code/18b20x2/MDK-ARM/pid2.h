#ifndef __PID2_H
#define __PID2_H
#include "main.h"

#define PWM_GPIO_PORT2 GPIOB
#define PWM_GPIO_PIN2  GPIO_PIN_13
#define PWM_PERIOD2    100  
extern uint8_t pwm_duty_cycle2;  
extern uint16_t pwm_counter2;    
float PID_Compute2(float current_temp);
#endif