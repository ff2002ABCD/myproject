#include "key.h"
#include "tim.h"
#include "gpio.h"


uint16_t K1_cnt=0,K1_bit=0;

	
uint8_t Key_GetNum(void)
{
	if(K1_bit==3)
	{
		K1_bit=0;
		return 1;
	}
	else if(K1_bit==5)
	{
		K1_bit=0;
		return 2;
	}
	return 0;
}

