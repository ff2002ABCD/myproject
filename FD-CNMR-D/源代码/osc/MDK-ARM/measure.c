#include "measure.h"
#include "dac.h"
#include "adc.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"
#include "stdio.h"
#include "osc.h"
#include "stdlib.h"
#include "control.h"
uint16_t voltage_table[10]={10,20,50,100,200,500,1000,2000,5000,10000};
uint32_t time_table[21]={500,1000,2000,5000,10000,20000,50000,100000,200000,500000,1000000,2000000,5000000,10000000,20000000,50000000,100000000,200000000};
uint32_t freq_table[21]={0,0,1250000,500000,250000,125000,50000,25000,12500,5000,2500,1250,500,250,125,50,25,12};
	
float measure_voltage_V(uint16_t k,uint8_t ch)
{
	float Voltage_V;
	if(ch==1)
	Voltage_V=(int)(k-128)*voltage_table[voltage_per_grid]/1000.00/32.00;
	else if(ch==2) Voltage_V=(int)(k-128)*voltage_table[voltage_per_grid_1]/1000.00/32.00;
	return Voltage_V;
}

float measure_voltage_V_fft(uint16_t k,uint8_t ch)
{
	float Voltage_V;
	if(ch==1)
	Voltage_V=(int)k*voltage_table[voltage_per_grid]/1000.00/32.00;
	else if(ch==2) Voltage_V=(int)k*voltage_table[voltage_per_grid_1]/1000.00/32.00;
	return Voltage_V;
}

float cursor_measure_voltage_V(uint16_t y,uint8_t ch)
{
	float cursor_Voltage_V;
	uint16_t k;
	k=(384-y)/1.5;
	cursor_Voltage_V=measure_voltage_V(k,ch);
	return cursor_Voltage_V;
}

float cursor_measure_voltage_V_xy(uint16_t x,uint8_t ch)
{
	float cursor_Voltage_V;
	uint16_t k;
	k=x*48.0/50.0/1.5;
	cursor_Voltage_V=measure_voltage_V(k,ch);
	return cursor_Voltage_V;
}

float cursor_measure_voltage_V_fft(uint16_t y,uint8_t ch)
{
	float cursor_Voltage_V;
	uint16_t k;
	k=(384-y)/1.5;
	cursor_Voltage_V=measure_voltage_V_fft(k,ch);
	return cursor_Voltage_V;
}

float measure_time_us(int16_t x)
{	
	float time_us;
	time_us=(float)x*time_table[time_per_grid]/50.00/1000.00;
	return time_us;
}

float measure_time_ms(int16_t x)
{	
	float time_ms;
	time_ms=(float)x*time_table[time_per_grid]/50.00/1000000.00;
	return time_ms;
}

float measure_freq_KHz_fft(int16_t x)
{
	return x*freq_table[time_per_grid]/50.00/1000.00;
}

float measure_freq_Hz_fft(int16_t x)
{
	return x*freq_table[time_per_grid]/50.00;
}

void findzeropoint_ch1(int16_t *zeropoint1,int16_t *zeropoint2)
{
	for(int i=300;i<S/2;i++)
	{
		if(ad1[i]<=Trigger_set+Trigger_set_offset_ch1+offset_ch1)
		{
			if(ad1[i+2]>Trigger_set+Trigger_set_offset_ch1+offset_ch1&&ad1[i-4]<Trigger_set+Trigger_set_offset_ch1+offset_ch1&&ad1[i+5]>Trigger_set+Trigger_set_offset_ch1+offset_ch1) 
			{
				*zeropoint1=i;
				break;
			}
		}
		if(i==S/2-1)*zeropoint1=0;
	}
	for(int i=*zeropoint1+5;i<S/2;i++)
	{
		if(ad1[i]<=Trigger_set+Trigger_set_offset_ch1+offset_ch1)
		{
			if(ad1[i+2]>Trigger_set+Trigger_set_offset_ch1+offset_ch1&&ad1[i-4]<Trigger_set+Trigger_set_offset_ch1+offset_ch1&&ad1[i+5]>Trigger_set+Trigger_set_offset_ch1+offset_ch1) 
			{
				*zeropoint2=i;
				break;
			}
		}
		if(i==S/2-1)*zeropoint1=0;
	}
}

void findzeropoint_ch2(int16_t *zeropoint1,int16_t *zeropoint2)
{
	for(int i=300;i<S/2;i++)
	{
		if(ad2[i]<=Trigger_set+Trigger_set_offset_ch2+offset_ch2)
		{
			if(ad2[i+2]>Trigger_set+Trigger_set_offset_ch2+offset_ch2&&ad2[i-4]<Trigger_set+Trigger_set_offset_ch2+offset_ch2&&ad2[i+5]>Trigger_set+Trigger_set_offset_ch2+offset_ch2) 
			{
				*zeropoint1=i;
				break;
			}
		}
		if(i==S/2-1)*zeropoint1=*zeropoint2=0;
	}
	for(int i=*zeropoint1+5;i<S/2;i++)
	{
		if(ad2[i]<=Trigger_set+Trigger_set_offset_ch2+offset_ch2)
		{
			if(ad2[i+2]>Trigger_set+Trigger_set_offset_ch2+offset_ch2&&ad2[i-4]<Trigger_set+Trigger_set_offset_ch2+offset_ch2&&ad2[i+5]>Trigger_set+Trigger_set_offset_ch2+offset_ch2) 
			{
				*zeropoint2=i;
				break;
			}
		}
		if(i==S/2-1)*zeropoint1=*zeropoint2=0;
	}
}

float measure_cycletime_us(int16_t x1,int16_t x2)
{
	float T;
	T=(x2-x1)*time_table[time_per_grid]/50.00/1000.00;
	return T;
}

float measure_cycletime_ms(int16_t x1,int16_t x2)
{
	float T;
	T=(x2-x1)*time_table[time_per_grid]/50.00/1000000.00;
	return T;
}

float measure_freq_Hz(int16_t x1,int16_t x2)
{
	float freq;
	freq=1000.00/measure_cycletime_ms(x1,x2);
	return freq;
}

float measure_freq_kHz(int16_t x1,int16_t x2)
{
	float freq;
	freq=1000.00/measure_cycletime_us(x1,x2);
	return freq;
}

uint8_t find_max_ch1(void)
{
	uint8_t Vmax=0;
	for(int i=1200;i<2000;i++)
	{
		if(ad1[i]>Vmax) Vmax=ad1[i];
	}
	return Vmax;
}

uint8_t find_min_ch1(void)
{
	uint8_t Vmin=255;
	for(int i=1200;i<2000;i++)
	{
		if(ad1[i]<Vmin) Vmin=ad1[i];
	}
	return Vmin;
}

uint8_t find_max_ch2(void)
{
	uint8_t Vmax=0;
	for(int i=1200;i<2000;i++)
	{
		if(ad2[i]>Vmax) Vmax=ad2[i];
	}
	return Vmax;
}

uint8_t find_min_ch2(void)
{
	uint8_t Vmin=255;
	for(int i=1200;i<2000;i++)
	{
		if(ad2[i]<Vmin) Vmin=ad2[i];
	}
	return Vmin;
}


void caliboration(int16_t *calbo1,int16_t *calbo2)
{
	int16_t average_vol1=0,average_vol2=0;
	
	offset_ch1=0;
	offset_ch2=0;
	for(int i=100;i<120;i++)
	{
		average_vol1+=ad1[i];
		average_vol2+=ad2[i];
	}
	average_vol1/=20;
	average_vol2/=20;
	
	if(average_vol1<127) del_zero_ch1++;
	if(average_vol1<127) del_zero_ch2++;
	printf("t0.txt=\"%d\"\xff\xff\xff",average_vol1);
	printf("t1.txt=\"%d\"\xff\xff\xff",average_vol2);
	
}