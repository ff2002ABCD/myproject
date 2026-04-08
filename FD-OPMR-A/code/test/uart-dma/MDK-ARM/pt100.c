#include "pt100.h"
#include "adc.h"
#include "delay.h"
#define hadc_pt100 hadc1
#define Vcc 3.3

float K=49.4/6.2+1;
uint16_t pt100_adc,pt100_voltage,pt100_res,pt100_temp;


float pt100_getTemperature()
{
		HAL_ADC_Start(&hadc_pt100);
	//	delay_ms(50);
		HAL_ADC_PollForConversion(&hadc_pt100,50);

		if(HAL_IS_BIT_SET(HAL_ADC_GetState(&hadc_pt100),HAL_ADC_STATE_REG_EOC))
		pt100_adc=HAL_ADC_GetValue(&hadc_pt100);

		pt100_voltage=Vcc/4096*pt100_adc;
	
		//用adc电压计算pt100电阻
		pt100_res=(200*(pt100_voltage/K+Vcc/3))/(Vcc*2/3-pt100_voltage/K);
	
		//用pt100电阻计算温度,,,,;'''''
		pt100_temp=(pt100_res/100-1)/0.00385;
		
		return pt100_temp;
}