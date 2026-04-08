#ifndef __FUNCTION_H
#define __FUNCTION_H
#include "main.h"
#include "stdio.h"
extern int fputc(int ch, FILE* file);
void output_ctrl1();
void output_ctrl2();
void pooltemp_ctrl();
void lighttemp_ctrl();
void DAC_init();
void DAC_renew();
void calibo_step();
void init_tempctrl();
#define pt100_AverNum 50
#endif
