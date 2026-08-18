#include "pt100.h"
#include "adc.h"
#include "delay.h"
#define hadc_pt100 hadc1
#define Vcc 3.3

float K=49.4/6.2+1;
uint16_t pt100_adc;
float pt100_voltage,pt100_temp,pt100_res;
_Bool adc_conversion_complete=0;

float pt100_getTemperature()
{
//		HAL_ADC_Start(&hadc_pt100);
//	//	delay_ms(50);
//		HAL_ADC_PollForConversion(&hadc_pt100,50);

//		if(HAL_IS_BIT_SET(HAL_ADC_GetState(&hadc_pt100),HAL_ADC_STATE_REG_EOC))
//		pt100_adc=HAL_ADC_GetValue(&hadc_pt100);

//		pt100_voltage=Vcc/4096*pt100_adc;
	
		//用adc电压计算pt100电阻
		pt100_res=(200.0000*(pt100_voltage/K+Vcc/3.0000))/(Vcc*2.0000/3.000000-pt100_voltage/K);
	
		//用pt100电阻计算温度,,,,;'''''
		pt100_temp=(pt100_res/100.00000-1.0000)/0.00385;
		
		return pt100_temp;
}

void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc)
{
    if(hadc->Instance == ADC1)
    {
        // 直接读取数据寄存器（会自动清除 EOC 标志）
        pt100_adc = ADC1->DR;
        adc_conversion_complete = 1;
        
        // 连续模式下，不需要做任何额外操作
        // ADC 会自动开始下一次转换
    }
}

void Start_ADC_Conversion(void)
{
    HAL_ADC_Start(&hadc_pt100);  // 不启动中断
}

float Convert_To_Voltage()
{
  // ????3.3V????,12????
  return (pt100_adc * 3.3f) / 65535.0f;
}