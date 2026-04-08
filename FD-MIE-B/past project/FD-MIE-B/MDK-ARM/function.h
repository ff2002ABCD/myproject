#ifndef __FUNCTION_H
#define __FUNCTION_H
#include "main.h"
#define MAX_NUM 100000
extern uint16_t count[MAX_NUM];
extern uint16_t voltage[MAX_NUM];
extern uint32_t index_send,index_save;
void save_data();
void Send_Coordinate_U16(uint16_t x, uint16_t y);
void Send_Coordinates_U16(uint16_t *x_values, uint16_t *y_values, int count);
#endif