#ifndef __MEASURE_H
#define __MEASURE_H
#include "main.h"
float measure_voltage_V(uint16_t k,uint8_t ch);

float cursor_measure_voltage_V(uint16_t y,uint8_t ch);
float cursor_measure_voltage_V_xy(uint16_t x,uint8_t ch);

float measure_time_us(int16_t x);

float measure_time_ms(int16_t x);

float measure_cycletime_us(int16_t x1,int16_t x2);
float measure_cycletime_ms(int16_t x1,int16_t x2);
float measure_freq_kHz(int16_t x1,int16_t x2);
float measure_freq_Hz(int16_t x1,int16_t x2);
	
void findzeropoint_ch1(int16_t *zeropoint1,int16_t *zeropoint2);
void findzeropoint_ch2(int16_t *zeropoint1,int16_t *zeropoint2);

uint8_t find_max_ch1(void);
uint8_t find_min_ch1(void);
uint8_t find_max_ch2(void);
uint8_t find_min_ch2(void);

void caliboration(int16_t *calbo1,int16_t *calbo2);

float measure_voltage_V_fft(uint16_t k,uint8_t ch);
float cursor_measure_voltage_V_fft(uint16_t y,uint8_t ch);
float measure_freq_KHz_fft(int16_t x);
float measure_freq_Hz_fft(int16_t x);
#endif