#include "function.h"
#include "menu.h"
#include "pid.h"
#include "pid2.h"
#include "pt100.h"
#include "DS18B20.h"
#include "i2c.h"
#include "AC.h"
#include "tim.h"
#include "osc.h"

float k=6;float Vcc=3.3;
	
void init_tempctrl()
{
	HAL_GPIO_WritePin(PWM_GPIO_PORT, PWM_GPIO_PIN, GPIO_PIN_RESET); 
	HAL_GPIO_WritePin(PWM_GPIO_PORT2, PWM_GPIO_PIN2, GPIO_PIN_RESET); 
	HAL_TIM_Base_Start_IT(&htim2);
	HAL_TIM_Base_Start_IT(&htim4);
	
}

void output_ctrl1()
{
	uint8_t data[3];
  uint16_t dac_value0 = (Vcc-k*current_hori/1000)/2/Vcc*4096;  // 12-bit value (0-4095)
	data[0]=0x40;
  data[1] = (dac_value0 >> 4); // Upper 4 bits
  data[2] = (dac_value0&0xF)<<4;         // Lower 8 bits

  HAL_I2C_Master_Transmit(&hi2c1, 0x60 << 1, data, 3, HAL_MAX_DELAY);
}

void output_ctrl2()
{
	switch(AC_type)
	{
		case sine:
			sin_handle();
			break;
		case triangle:
			triangle_handle();
			break;
		case square:
			square_handle();
			break;
	}
	uint8_t data[3];
//  uint16_t dac_value = 4095;  // 12-bit value (0-4095)
	data[0]=0x40;
  data[1] = (dac_value >> 4) ;  // Upper 8 bits
  data[2] = (dac_value & 0xF)<<4;         // Lower 4 bits

  HAL_I2C_Master_Transmit(&hi2c4, 0x60 << 1, data, 3, HAL_MAX_DELAY);
//	HAL_I2C_Master_Transmit_IT(&hi2c4, 0x60 << 1, data, 3);
//	HAL_I2C_Mem_Write_DMA()
}

void lighttemp_ctrl()
{
	static float temp[pt100_AverNum];
	float sum=0;
	static int i=0;
	temp[i]=pt100_getTemperature();
	i++;if(i==pt100_AverNum)i=0;
	
	for(int j=0;j<pt100_AverNum;j++)
	{
		sum+=temp[j];
	}
	temp_light_now=sum/pt100_AverNum;
	printf("T_light.txt=\"%.1f\"\xff\xff\xff",temp_light_now);
	float pid_output = PID_Compute(temp_light_now);
	pwm_duty_cycle=(uint8_t)pid_output;
}

void pooltemp_ctrl()
{
//	temp_pool_now=DS18B20_ReadTemp();
	printf("T_pool.txt=\"%.1f\"\xff\xff\xff",temp_pool_now);
	float pid_output2=PID_Compute2(temp_pool_now);
	pwm_duty_cycle2=(uint8_t)pid_output2;
}
		
void DAC_init()
{
	
	DC_value=fabs(current_vert/1000.0000);
	AC_value=current_scan/1000.0000;
	uint16_t freq=freq_scan;	
	if(freq<30) num=50;
	else num=30;
	dac_forward_max=(((DC_value+AC_value*0.707)*k)+Vcc)/2/Vcc*4096;
	dac_forward_min=(((DC_value-AC_value*0.707)*k)+Vcc)/2/Vcc*4096;
	dac_reverse_max=(((-DC_value+AC_value*0.707)*k)+Vcc)/2/Vcc*4096;
	dac_reverse_min=(((-DC_value-AC_value*0.707)*k)+Vcc)/2/Vcc*4096;
	VPP=dac_forward_max-dac_forward_min;
	switch(scan_shape_now)
	{
		case 0:
			AC_type=triangle;
			break;
		case 1:
			AC_type=square;
			break;
		case 2:
			AC_type=sine;
			break;
	}
	if(current_vert>=0) current_direction=reverse;
	else current_direction=forward;
	
	switch(AC_type)
	{
		case square:
			TIM6->PSC=20000-1;
			TIM6->ARR=200000000/(TIM6->PSC+1)/freq/num-1;
			break;
		case sine:
			TIM6->PSC=20000-1;
			TIM6->ARR=200000000/(TIM6->PSC+1)/freq/num-1;
			GenerateSineTable();
			break;
		case triangle:
			TIM6->PSC=20000-1;
			TIM6->ARR=200000000/(TIM6->PSC+1)/freq/num-1;
			if(current_direction==forward)
			{
				dac_value=dac_forward_min;
			}
			else
			{
				dac_value=dac_reverse_min;
			}
			break;
	}
}

void DAC_renew()
{
	DC_value=fabs(current_vert/1000.0000);
	AC_value=current_scan/1000.0000;
	uint16_t freq=freq_scan;
	if(freq<30) num=50;
	else num=30;
	dac_forward_max=(((DC_value+AC_value*0.707)*k)+Vcc)/2/Vcc*4096;
	dac_forward_min=(((DC_value-AC_value*0.707)*k)+Vcc)/2/Vcc*4096;
	dac_reverse_max=(((-DC_value+AC_value*0.707)*k)+Vcc)/2/Vcc*4096;
	dac_reverse_min=(((-DC_value-AC_value*0.707)*k)+Vcc)/2/Vcc*4096;
	VPP=dac_forward_max-dac_forward_min;
	switch(scan_shape_now)
	{
		case 0:
			AC_type=triangle;
			break;
		case 1:
			AC_type=square;
			break;
		case 2:
			AC_type=sine;
			break;
	}
	if(current_vert>=0) current_direction=reverse;
	else current_direction=forward;
	index=0;
	direction_counter=0;
	switch(AC_type)
	{
		case square:
			//TIM6->PSC=20000-1;
			TIM6->ARR=200000000/(TIM6->PSC+1)/freq/num-1;
			break;
		case sine:
		//	TIM6->PSC=20000-1;
			TIM6->ARR=200000000/(TIM6->PSC+1)/freq/num-1;
			GenerateSineTable();
			break;
		case triangle:
		//	TIM6->PSC=20000-1;
			TIM6->ARR=200000000/(TIM6->PSC+1)/freq/num-1;
			if(current_direction==forward)
			{
				dac_value=dac_forward_min;
			}
			else
				{
				dac_value=dac_reverse_min;
			}
			break;
	}
}

void calibo_step()
{
	switch(caliboration_state)
	{
		case CH1_OFFSET:
		{
			offset_ch1=0;
			printf("move zero1,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*offset_ch1),grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*(offset_ch1)));
		}break;
		case CH1_K_1:
		{
			offset_ch1=100;
			printf("move zero1,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*offset_ch1),grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*(offset_ch1)));
		}break;
		case CH1_K_2:
		{
			offset_ch1=-100;
			printf("move zero1,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*offset_ch2),grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*(offset_ch1)));
		}break;	
		case CH2_OFFSET:
		{
			offset_ch2=0;
			printf("move zero2,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*offset_ch2),grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*(offset_ch2)));
		}break;
		case CH2_K_1:
		{
			offset_ch2=100;
			printf("move zero2,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*offset_ch2),grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*(offset_ch2)));
		}break;
		case CH2_K_2:
		{
			offset_ch2=-100;
			printf("move zero2,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*offset_ch2),grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*(offset_ch2)));
		}break;
		case SAVE:
		{
			offset_ch1=0;
			printf("move zero1,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*offset_ch1),grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*(offset_ch1)));
			offset_ch2=0;
			printf("move zero2,%d,%d,%d,%d,0,30\xFF\xFF\xFF",grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*offset_ch2),grid_left,(int)((grid_up+grid_down)/2-half_txt_height-1.5*(offset_ch2)));
		}break;
		default:break;
	}
}

