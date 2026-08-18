#include "c8051F410.h"
#include "Delay.h"

/**
  * @brief  获取独立按键键码
  * @param  无
  * @retval 按下按键的键码，范围：0~4，无按键按下时返回值为0
  */
	
//#define PUP P1_4
//#define PDN P1_5
//#define PENT P1_6
//#define PFUN P1_7

unsigned char Key()
{
	unsigned char KeyNumber=0;
	
//	if(PUP==0){Delay(20);while(PUP==0);Delay(20);KeyNumber=1;}
//	if(PDN==0){Delay(20);while(PDN==0);Delay(20);KeyNumber=2;}
//	if(PENT==0){Delay(20);while(PENT==0);Delay(20);KeyNumber=3;}
//	if(PFUN==0){Delay(20);while(PFUN==0);Delay(20);KeyNumber=4;}
	
	return KeyNumber;
}
