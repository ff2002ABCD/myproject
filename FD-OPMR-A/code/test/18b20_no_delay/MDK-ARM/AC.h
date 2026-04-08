#ifndef __AC_H
#define __AC_H

#include "stdint.h"

void sin_handle();
void triangle_handle();
void square_handle();
void GenerateSineTable(void);
typedef enum {sine,triangle,square} AC_TYPE;
typedef enum {forward=0,reverse=1} CURRENT_DIRECTION;

extern uint16_t dac_forward_max;
extern uint16_t dac_forward_min;
extern uint16_t dac_reverse_max;
extern uint16_t dac_reverse_min;
extern uint16_t VPP;
extern uint8_t duty;
extern uint16_t dac_value;
extern uint16_t num;
extern float DC_value,AC_value;
extern AC_TYPE AC_type;
extern CURRENT_DIRECTION current_direction;
extern uint16_t index;
extern uint16_t direction_counter;
#endif
