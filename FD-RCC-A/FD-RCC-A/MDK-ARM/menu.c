#include "main.h"
#include "dac.h"
#include "adc.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"
#include "stdio.h"
#include "osc.h"
#include "stdlib.h"
#include "control.h"
//#include "measure.h"
#include "menu.h"
//#include "flash.h"
#include "string.h"
#include "function.h"
#include <math.h>
#include "stdio.h"
#include "button.h"
CURSOR cursor=TEMP;
CURSOR_TEMP cursor_temp=99;
CURSOR_PULSE cursor_pulse=99;
CURSOR_DUTY cursor_duty=99;
_Bool voltage_sum_ctrl; 

CURSOR cursor_last;
char *txtname[]={"temp","pulse_width","duty","vol_sum"};
int voltage_sum_mv=0;

int temperature_set=20;
float temperature_now=19.99;
float current;
float voltage_led;
uint32_t pulse_width_us=50;
int duty_cycle=1000;
_Bool direct_current_output=0;
_Bool start_temp_ctrl=0;

void up_button()
{
	if(cursor!=CURSOR_NONE)
	{
		if(cursor>0) cursor--;
		else cursor=CURSOR_MAX-1;
	}
	
	
	switch(cursor_temp)
	{
		case TEMP1:temperature_set+=100;break;
		case TEMP2:temperature_set+=10;break;
		case TEMP3:temperature_set++;break;
		default:break;
	}
	if(temperature_set>100) temperature_set=100;
	
	if(cursor_pulse!=99)
	{
		pulse_width_us+=pow(10,CURSOR_PULSE_DIGIT-cursor_pulse-1);
		if(pulse_width_us>1000000) pulse_width_us=1000000;
	}
	
	if(cursor_duty!=99&&cursor_duty!=CURSOR_DUTY_MAX-1)
	{
		duty_cycle+=pow(10,CURSOR_DUTY_DIGIT-cursor_duty-1);
		if(duty_cycle>1000) duty_cycle=1000;
	}
	
	if(voltage_sum_ctrl==1)
	{
		if(current>350) return;
		if(long_counter<10)
		voltage_sum_mv+=2;
		else voltage_sum_mv+=10;
		if(voltage_sum_mv>VOLTAGE_SUM_MV_MAX) voltage_sum_mv=VOLTAGE_SUM_MV_MAX;
	}

}

void down_button()
{	
	if(cursor!=CURSOR_NONE)
	{
		cursor++;
	}
	if(cursor==CURSOR_MAX) cursor=0;
	
	switch(cursor_temp)
	{
		case TEMP1:temperature_set-=100;break;
		case TEMP2:temperature_set-=10;break;
		case TEMP3:temperature_set--;break;
		default:break;
	}
	if(temperature_set<0) temperature_set=0;
	
	if(cursor_pulse!=99)
	{
		pulse_width_us-=pow(10,CURSOR_PULSE_DIGIT-cursor_pulse-1);
		if(pulse_width_us<50) pulse_width_us=50;
	}
	
	if(cursor_duty!=99&&cursor_duty!=CURSOR_DUTY_MAX-1)
	{
		duty_cycle-=pow(10,CURSOR_DUTY_DIGIT-cursor_duty-1);
		if(duty_cycle<2) duty_cycle=2;
	}
	
	if(voltage_sum_ctrl==1)
	{
		if(long_counter<10)
		voltage_sum_mv-=2;
		else voltage_sum_mv-=10;
		if(voltage_sum_mv<0) voltage_sum_mv=0;
	}
}

void left_button()
{
	if(cursor_temp!=99)
	{
		if(cursor_temp>0)
		cursor_temp--;
		else cursor_temp=CURSOR_TEMP_MAX-1;
	}
	
	if(cursor_pulse!=99)
	{
		if(cursor_pulse>0)
		cursor_pulse--;
		else cursor_pulse=CURSOR_PULSE_MAX-1;
	}
	
	if(cursor_duty!=99)
	{
		if(cursor_duty>0)
		cursor_duty--;
		 else cursor_duty=CURSOR_DUTY_MAX-1;
	}
}

void right_button()
{
	if(cursor_temp!=99)
	{
		if(cursor_temp<CURSOR_TEMP_MAX-1)
		cursor_temp++;
		 else cursor_temp=0;
	}
	
	if(cursor_pulse!=99)
	{	
		if(cursor_pulse<CURSOR_PULSE_MAX-1)
		cursor_pulse++;
		 else cursor_pulse=0;
	}
	
	if(cursor_duty!=99)
	{
		if(cursor_duty<CURSOR_DUTY_MAX-1)
		cursor_duty++;
		else cursor_duty=0;
	}
}

void confirm_button()
{
	switch(cursor)
	{
		case TEMP:
			cursor=99;
			cursor_temp=0;
			break;
		case PULSE_WIDTH:
			cursor=99;
			cursor_pulse=0;
			break;
		case DUTY:
			cursor=99;
			cursor_duty=0;
			break;
		case VOL_SUM:
			cursor=99;
			voltage_sum_ctrl=1;
			break;
		default:break;
	}
	if(cursor_temp==CURSOR_TEMP_MAX-1)
		start_temp_ctrl=!start_temp_ctrl;
	
	if(cursor_duty==CURSOR_DUTY_MAX-1) 
		direct_current_output=!direct_current_output;
	
}

void cancel_button()
{	
	if(cursor!=99) return;
	if(cursor_temp!=99)
	{
		cursor_temp=99;
		cursor=TEMP;
	}
	if(cursor_pulse!=99)
	{
		cursor_pulse=99;
		cursor=PULSE_WIDTH;
	}
	if(cursor_duty!=99)
	{
		cursor_duty=99;
		cursor=DUTY;
	}
	if(voltage_sum_ctrl==1)
	{
		cursor_duty=99;
		cursor=VOL_SUM;
		voltage_sum_ctrl=0;
	}
}

void renew_menu()
{
//	printf("page 0\xff\xff\xff");
	//刷新主菜单高亮
	for(int i=0;i<CURSOR_MAX;i++) printf("%s.bco=50779\xff\xff\xff",txtname[i]);
	if(cursor!=99) printf("%s.bco=61277\xff\xff\xff",txtname[cursor]);
	//刷新各副菜单高亮
	for(int i=0;i<CURSOR_TEMP_MAX;i++) printf("temp%d.bco=50779\xff\xff\xff",i+1);
	if(cursor_temp!=99) printf("temp%d.bco=61277\xff\xff\xff",cursor_temp+1);
	
	for(int i=0;i<CURSOR_PULSE_MAX;i++) printf("pulse%d.bco=50779\xff\xff\xff",i+1);
	if(cursor_pulse!=99) printf("pulse%d.bco=61277\xff\xff\xff",cursor_pulse+1);
	
	for(int i=0;i<CURSOR_DUTY_MAX;i++) printf("duty%d.bco=50779\xff\xff\xff",i+1);
	if(cursor_duty!=99) printf("duty%d.bco=61277\xff\xff\xff",cursor_duty+1);
	
	printf("vol_sum1.bco=50779\xff\xff\xff");
	if(voltage_sum_ctrl==1) printf("vol_sum1.bco=61277\xff\xff\xff");
	//刷新设定数值
	for(int i=0;i<CURSOR_TEMP_DIGIT;i++)
		printf("temp%d.txt=\"%d\"\xff\xff\xff",i+1,temperature_set/(int)pow(10,CURSOR_TEMP_DIGIT -(i+1))%10);
	
	for(int i=0;i<CURSOR_PULSE_DIGIT;i++)
		printf("pulse%d.txt=\"%d\"\xff\xff\xff",i+1,pulse_width_us/(int)pow(10,CURSOR_PULSE_DIGIT -(i+1))%10);
	
	for(int i=0;i<CURSOR_DUTY_DIGIT;i++)
		printf("duty%d.txt=\"%d\"\xff\xff\xff",i+1,duty_cycle/(int)pow(10,CURSOR_DUTY_DIGIT -(i+1))%10);
	
	printf("vol_sum1.txt=\"%.3fV\"\xff\xff\xff",voltage_sum_mv/1000.000);
	
	if(start_temp_ctrl==1) printf("temp4.txt=\"结束控温\"\xff\xff\xff");
	else printf("temp4.txt=\"开始控温\"\xff\xff\xff");
	
	if(direct_current_output==1) printf("duty5.txt=\"直流输出：开\"\xff\xff\xff");
	else printf("duty5.txt=\"直流输出：关\"\xff\xff\xff");
}

