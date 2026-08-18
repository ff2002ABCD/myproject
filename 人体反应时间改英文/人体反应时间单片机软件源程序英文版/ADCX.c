//启动单路AD,启动时间10ms,稳态时间160ms
#include "ADCX.h"

bit adcxEn;

void adcxRst()
{
	unsigned char i;
	adcxEn=0;
	EIE1 &=~0x08;		//EADC0C=0
	ADC0CN &=0xdf;		//AD0INT=0
}

void adcxSt(unsigned char i)
{
	switch (i)
	{
	case 0:
		ADC0MX=0x13;	//P2.3
		break;
	case 1:
		ADC0MX=0x14;	//P2.4
		break;
	case 2:
		ADC0MX=0x15;	//P2.5
		break;
	case 3:
		ADC0MX=0x16;	//P2.6
	}
	ADC0CN &=0xdf;		//AD0INT=0
	EIE1 |=0x08;		//EADC0C=1
	AD0BUSY=1;			//开始
}

void adcxEnd()
{
	EIE1 &=~0x08;		//EADC0C=0
	ADC0CN &=0xdf;		//AD0INT=0
}

int adcxax=0;

void adcxCopy(unsigned int * datap)
{
	unsigned char * p=(unsigned char *) datap;
	*p=ADC0H;
	p++;
	*p=ADC0L;
	adcxax++;
}

