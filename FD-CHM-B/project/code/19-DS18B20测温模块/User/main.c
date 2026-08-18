#include "stm32f10x.h"                  // Device header
#include "Delay.h"
#include "OLED.h"
#include "DS18B20.h"

	
	
int main(void)
{
	
	
	OLED_Init();
	DS18B20_Init();
	
	uint16_t Temp ;
	
	while (1)
	{
		if(DS18B20_Reset()==0)
		{
			Temp = DS18B20_ReadTemp();
			if(flag==1)
			{
				OLED_ShowString(1, 1, "Temp=-");
				OLED_ShowString(1, 10, ".");
				OLED_ShowNum(1,7,Temp/10%100,3);
				OLED_ShowNum(1,11,Temp%10,1);
			}
			else
			{
				OLED_ShowString(1, 1, "Temp=+");
				OLED_ShowString(1, 10, ".");
				OLED_ShowNum(1,7,Temp/10%100,3);
				OLED_ShowNum(1,11,Temp%10,1);
			}
		}
		else
		{
			OLED_ShowString(1,1,"No   sensor  ");
			Delay_ms(5);
		}
		
	  
		Delay_ms(50);
		
	}
}
