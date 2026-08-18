#include "F410INIT.h"
#include "C8051F410X.H"
#include "DISPLCD.H"
#include "KEY.H"
#include "RSP.H"
#include "MENU.H"
#include "WELCOME.H"

unsigned char ucT10MS,ucT100MS,ucT1S;
unsigned char ucStateT1MS,ucStateT10MS,ucStateT100MS,ucStateT1S;
bit bT10MSEn,bT100MSEn,bT1SEn;

unsigned char tx[10];

void rst()
{
	Init_Device();

	ucStateT1MS=1;
	ucStateT10MS=1;
	ucStateT100MS=1;
	ucStateT1S=1;
	ucT10MS=10;
	ucT100MS=10;
	ucT1S=10;
	bT10MSEn=0;
	bT100MSEn=0;
	bT1SEn=0;

	dispRst();
	keyRst();
	menuRst();
	rspRst();
}

void main()
{
	EA=0;
	rst();
 	EA=1;

	while(DISPEN) 	//完成显示初始化
		;

	welcomeSt();

	while(1)
	{
//		RSTSTAT=0;
		if(TMR3CN & 0X80)
		{
			ucT10MS--;
			if (!ucT10MS)
			{
				bT10MSEn=1;
				ucT10MS=10;
			}

			switch (ucStateT1MS)
			{
			case 1:
				ucStateT1MS++;
				rspProc(); 		//
			case 2:
				ucStateT1MS++;
			default:
				TMR3CN &= ~0X80;
				ucStateT1MS=1;
			}
		}
  
		if(bT10MSEn)
		{
			ucT100MS--;
			if (!ucT100MS)
			{
				bT100MSEn=1;
				ucT100MS=10;
			}

			switch (ucStateT10MS)
			{
			case 1:
				if(TMR3CN & 0X80)
					break;
				keyProc();		//
				ucStateT10MS++;
			default:
				bT10MSEn=0;
				ucStateT10MS=1;
			}
		}

		if(bT100MSEn)
		{
			ucT1S--;
			if (!ucT1S)
			{
				bT1SEn=1;
				ucT1S=10;
			}

			switch (ucStateT100MS)
			{
			case 1:
				if(TMR3CN & 0X80)
					break;
				
				ucStateT100MS++;
			case 2:
				if(TMR3CN & 0X80)
					break;
				dispFD();		//
				ucStateT100MS++;
			case 3:
				if(TMR3CN & 0X80)
					break;
				ucStateT100MS++;
			default:
				bT100MSEn=0;
				ucStateT100MS=1;
			}
		}

		if(bT1SEn)
		{
			switch (ucStateT1S)
			{
			case 1:
				if(TMR3CN & 0X80)
					break;
				welcomeProc();
				ucStateT1S++;
			case 2:
				if(TMR3CN & 0X80)
					break;
				ucStateT1S++;
			default:
				bT1SEn=0;
				ucStateT1S=1;
			}
		}
	}
}
