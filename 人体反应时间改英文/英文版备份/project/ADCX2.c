//启动双路AD,启动时间1~2S,稳态时间32S

#include "ADCX2.h"

unsigned int data adcx2Rs[4];

bit adcx2En;
unsigned char adcx2Cnl;


void adcx2Rst()
{
	unsigned char i;
	adcxRst();
	adcx2En=0;
	for(i=0;i<4;i++)
	{
		adcx2Rs[i]=0;
	}
	adcx2Cnl=0;
}

void adcx2St()
{
	adcx2En=1;
}

void adcx2End()
{
	adcx2En=0;
}

void adcx2()
{
	unsigned char i;
	if(adcx2En)
	{
		if(!ADCXBUSY)
		{
			adcxCopy(adcx2Rs+adcx2Cnl);
			switch (adcx2Cnl)
			{
			case 0:
				adcx2Cnl++;
				break;
			case 1:
				adcx2Cnl++;
				break;
			case 2:
				adcx2Cnl++;
				break;
			case 3:
				adcx2Cnl=0;
				break;
			default:
				adcx2Cnl=0;
			}
			adcxSt(adcx2Cnl);
		}
	}
}
