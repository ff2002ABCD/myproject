#include "c8051F410.h"
//#include "C8051F410_defs.h"
#include "Timer0.h"
//#include "Key.h"

unsigned char KeyNum;

//#define TCO P1_3
//#define TP5 P0_0
//#define DRST P0_1
//#define SCK P0_2
//#define MOSI P0_4
//#define DCS P0_5
//#define TP1 P2_0
//#define TP2 P2_1
//#define TP3 P2_2
//#define TP4 P2_3
//#define AD0 P2_4
void main()
{
	P1=0x00;
//	P1_4=0;
	//Timer0Init();
	while(1)
	{
		KeyNum=Key();		//获取独立按键键码
		if(KeyNum)			//如果按键按下
		{
			if(KeyNum==1)	//PUP
			{
					
			}
			if(KeyNum==2)	//PDN
			{
					
			}
			if(KeyNum==3)	//PENT
			{
					
			}
			if(KeyNum==4)	//PFUN
			{
					
			}
		}
	}
}

void Timer0_Routine() interrupt 1
{
	static unsigned int T0Count;
	TL0 = 0x18;		//设置定时初值
	TH0 = 0xFC;		//设置定时初值
	T0Count++;		//T0Count计次，对中断频率进行分频
	if(T0Count>=500)//分频500次，500ms
	{
		T0Count=0;
//		if(TCO==0) TCO=1;
//		else TCO=0;
	}
}
