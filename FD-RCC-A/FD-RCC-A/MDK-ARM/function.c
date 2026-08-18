#include "function.h"
#include "menu.h"
#include "pid.h"
#include "pt100.h"
#include "DS18B20.h"
#include "i2c.h"
#include "AC.h"
#include "tim.h"
#include "osc.h"
uint32_t freq;
float k=4;float Vcc=3.3;
	
void init_tempctrl()
{
	HAL_GPIO_WritePin(PWM_GPIO_PORT, PWM_GPIO_PIN, GPIO_PIN_RESET); 
	HAL_TIM_Base_Start_IT(&htim4);
//	HAL_TIM_Base_Start_IT(&htim4);
	
}

void output_ctrl1()
{
//	uint8_t data[3];
//  uint16_t dac_value0 = (Vcc-k*current_vert/1000)/2/Vcc*4096;  // 12-bit value (0-4095)
//	data[0]=0x40;
//	
//  data[1] = (dac_value0 >> 4); // Upper 4 bits
//  data[2] = (dac_value0&0xF)<<4;         // Lower 8 bits

//  HAL_I2C_Master_Transmit(&hi2c1, 0x60 << 1, data, 3, 100);
}

void output_ctrl2()
{
    switch(AC_type)
    {
        case sine: sin_handle(); break;
        case triangle: triangle_handle(); break;
        case square: square_handle(); break;
    }
    
    uint8_t data[2];  // 改为 2 字节！
    if(dac_value > 4095) dac_value = 4095;
    
    // 正确格式
    data[0] = 0x00 | ((dac_value >> 8) & 0x0F);  // 快速模式
    data[1] = dac_value & 0xFF;
    
    // 超时用 1ms 就够了
    HAL_I2C_Master_Transmit(&hi2c4, 0x60 << 1, data, 2, 1);
}


void temp_ctrl()
{

	float pid_output=PID_Compute(temperature_now);
	pwm_duty_cycle=(uint8_t)pid_output;
}
		
void DAC_init()
{
		freq=1000000/pulse_width_us;	
	
		dac_reverse_max=4095;
		dac_reverse_min=4095-voltage_sum_mv/1.0000/VOLTAGE_SUM_MV_MAX*4096;
		VPP=dac_forward_max-dac_forward_min;
		
		AC_type=square;
	
	switch(AC_type)
	{
		case square:
			
			TIM6->PSC=200-1;
			if(freq<20) TIM6->PSC=20000-1;
			TIM6->ARR=200000000/(TIM6->PSC+1)/freq-1;
			break;
		case sine:
			TIM6->PSC=20000-1;
			TIM6->ARR=200000000/(TIM6->PSC+1)/freq/num-1;
			GenerateSineTable();
			break;
		case triangle:
			TIM6->PSC=20000-1;
			TIM6->ARR=200000000/(TIM6->PSC+1)/freq/num-1;
			dac_value=dac_reverse_min;
	
	}
}

void DAC_renew()
{
	  freq=1000000/pulse_width_us;	
	
		dac_reverse_max=4095;
		dac_reverse_min=4095-voltage_sum_mv/1.0000/VOLTAGE_SUM_MV_MAX*4096;
		VPP=dac_forward_max-dac_forward_min;
		
		AC_type=square;
	
	switch(AC_type)
	{
		case square:
			TIM6->PSC=200-1;
			if(freq<20) TIM6->PSC=20000-1;
			TIM6->ARR=200000000/(TIM6->PSC+1)/freq-1;
			break;
		case sine:
			TIM6->PSC=20000-1;
			TIM6->ARR=200000000/(TIM6->PSC+1)/freq/num-1;
			GenerateSineTable();
			break;
		case triangle:
			TIM6->PSC=20000-1;
			TIM6->ARR=200000000/(TIM6->PSC+1)/freq/num-1;
			dac_value=dac_reverse_min;
	
	}
}



