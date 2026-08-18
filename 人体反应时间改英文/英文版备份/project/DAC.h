#ifndef DAC_H
#define DAC_H

extern void dacRst();
extern void dacSt();
extern void dacProc();	//100ms
extern void dacCopy(unsigned char i);

#include "menu.h"
#include "DISPLCD.h"
#include "KEY.h"
#include "MATH.h"
#include "DACX.H"

extern void dacEnd();
extern void dacProcSt();
extern void dacProcEnd();
extern void dacInc();
extern void dacDec();
extern void dacDisp();
extern void dacSel();

bit dacProcEn;
unsigned int dacSet[2];	//预设值，当前值
unsigned char dacSeln;

unsigned char code dacDispData[4][0x10]={
	"DAC0:           ",
	"               V",
	"DAC1:           ",
	"               V",
};

void dacSt()
{
	dispSelCG=1;
	keyUpSv=dacInc;
	keyDownSv=dacDec;
	keyFunSv=dacEnd;
	keyEntSv=dacSel;
	dispSvProc=dacDisp;
}

void dacEnd()
{
	menuSt();
}

void dacRst()
{
	dacProcEn=0;
	dacSet[0]=0;
	dacSet[1]=0;
	dacSeln=0;
}

void dacInc()
{
	dacSet[dacSeln]++;
	if(dacSet[dacSeln]>1000)
	{
		dacSet[dacSeln]=1000;
	}
	dacxD[dacSeln]=dacSet[dacSeln];
	dacxCopy(dacSeln);
}

void dacDec()
{
	dacSet[dacSeln]--;
	if(dacSet[dacSeln]>=1000)
	{
		dacSet[dacSeln]=0;
	}
	dacxD[dacSeln]=dacSet[dacSeln];
	dacxCopy(dacSeln);
}

void dacDisp()
{
	dispCopy(dacDispData);
	int2char(dispData[1],dacSet[0],2,15);
	int2char(dispData[3],dacSet[1],2,15);
	dispTs();
	dispRefreshSt();
	if(dispSelCG)
	{
		switch (dacSeln)
		{
		case 0:
				dispSelSt(2);
				break;
		case 1:
				dispSelSt(4);
		}
		dispSelCG=0;
	}
}


void dacSel()
{
	switch (dacSeln)
	{
	case 0:
		dacSeln=1;
		break;
	case 1:
		dacSeln=0;
	}
	dispSelCG=1;
}

#endif