#include "TADDA.H"

#define TADDAN 2000

void taddaEnd();
void taddaDisp();

unsigned int data tadday[2],taddaul[1];
unsigned int data taddaI;

void taddaDisp();

unsigned char code taddaDispData[4][0x10]={
	"µçÁ÷:           ",
	"              \241\346",
	"ADC1:           ",
	"               V",
};

void taddaRst()
{
	adcxRst();
	dacxRst();
	taddaI=TADDAN;
	tadday[0]=0;
	tadday[1]=0;
	taddaul[0]=0;
}

void taddaSt()
{
	//keyUpSv=keySvNull;
	//keyDownSv=keySvNull;
	//keyEntSv=keySvNull;
	//keyFunSv=adcEnd;
	//dispSvProc=adcDisp;
	adcxSt(0);
	dacxD[0]=2002;
	dacxCopy(0);
	taddaDisp();
}

void taddaEnd()
{
	//menuSt();
}

unsigned char taddaax=0;

void taddaDisp()
{
	dispCopy(taddaDispData);
	int2char(dispData[1],tadday[0],2,12);
	int2char(dispData[3],tadday[0],2,15);
	dispRefreshSt();
	taddaax++;
}

void taddaProc()
{
	unsigned int data u;
	//uart0Proc();
	if(!ADCXBUSY)
	{
		adcxCopy(&u);
		adcxSt(0);
		vflt3(tadday,taddaul,u);
	}
	taddaI--;
	if(!taddaI)
	{
		taddaI=TADDAN;
		taddaDisp();
	}
}

