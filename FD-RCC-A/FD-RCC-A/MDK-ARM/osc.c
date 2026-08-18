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
#include "fft.h"
#include "filter.h"
#include "menu.h"
#include "button.h"
#include "pid.h"

#include "function.h"
#include "AC.h"
#include "button.h"
#include "string.h"
#include "18B20.h"
#include "pt100.h"     
//#include "encoder.h"
_Bool dac_need_update;

//TIM5 KEY
//TIM6 PULSE

void Init_Osc(void)
{
	TIM5->PSC=200-1;
	TIM5->ARR=10000-1;//10ms
	HAL_TIM_Base_Start_IT(&htim5);//key
	HAL_TIM_Base_Start_IT(&htim6);//pulse
	renew_menu();
//	TIM3->PSC=100-1;
//	TIM3->ARR=200-1;//10khz

}

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{	
	
	if (htim->Instance == htim4.Instance) 
	{
		if(start_temp_ctrl==0)
		{
			HAL_GPIO_WritePin(PWM_GPIO_PORT, PWM_GPIO_PIN, GPIO_PIN_RESET); 
		}
		else
		{
			temp_ctrl();
			pwm_counter++;
			if (pwm_counter >= PWM_PERIOD) 
			{
				pwm_counter = 0;
			}
			if (pwm_counter < pwm_duty_cycle) 
			{
				HAL_GPIO_WritePin(PWM_GPIO_PORT, PWM_GPIO_PIN, GPIO_PIN_SET);
			} 
			else 
			{
				HAL_GPIO_WritePin(PWM_GPIO_PORT, PWM_GPIO_PIN, GPIO_PIN_RESET); 
			}
		}
	}
	if(htim->Instance==htim6.Instance)//100us	
	{

		output_ctrl2();
		if(adc_start==1)
		{
			adc_start=0;
			Test_ADC_Direct();
		}
	}	
	if(htim->Instance==htim5.Instance)//10ms
	{	
		Key_Scan();
		static int tim5_counter=0;
		static int tim5_counter_1=0;
		tim5_counter++;
		tim5_counter_1++;
		if(tim5_counter>=10)//100/10=10Hz
		{	
		
			tim5_counter=0;
				do_key();
				
			}
			if(tim5_counter_1>=20)
			{
				tim5_counter_1=0;
				DAC_renew();
				temperature_now=DS18B20_Get_Temperature()*0.0625;
				
				//LEDµçÁ÷
				printf("current1.txt=\"%.2fmA\"\xff\xff\xff",current);
				//LEDµçÑ¹
				printf("vol_led1.txt=\"%.4fV\"\xff\xff\xff",(voltage_sum_mv-current*11.1)/1000.0000);	
				printf("temp_now_1.txt=\"%.1f¡æ\"\xff\xff\xff",temperature_now);
			}
	}	
		
	

}



	