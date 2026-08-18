#include "DACX.h"

unsigned int dacxD[2];

void dacxRst()
{
	dacxD[0]=500;
	dacxD[1]=0;
}

void dacxCopy(unsigned char i)
{
	unsigned char *p;
	switch (i)
	{
	case 0:
		p=(unsigned char *)dacxD;
		p++;
		IDA0L=*p;
		p--;
		IDA0H=*p;
		break;
	case 1:
		p=(unsigned char *)(dacxD+1);
		p++;
		IDA1L=*p;
		p--;
		IDA1H=*p;
	}
}
