#ifndef _ENCODER_H
#define _ENCODER_H

#define htim_encoder htim1
#define TIM_ENCODER TIM1
void encoder_init();
void get_encoder();
void clockwise();
void counter_clockwise();
#endif