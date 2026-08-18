#include "WELCOME.h"

#define welcomeTN 5

void welcomeDisp();
void welcomeEnd();

bit welcomeEn;
unsigned char welcomeT;

unsigned char code welcomeDispData[4][0x10]={
	"----------------",
	"    Welcome    ",
	"               ",
	"----------------",
};

void welcomeSt()
{
	welcomeT=welcomeTN;
	welcomeEn=1;
	keyUpSv=keySvNull;
	keyDownSv=keySvNull;
	keyFunSv=keySvNull;
	keyEntSv=welcomeEnd;
	dispSvProc=welcomeDisp;
	welcomeDisp();
}

void welcomeProc()
{
	if(welcomeEn)
	{
		welcomeT--;
		if (!welcomeT)
		{
			welcomeEn=0;
			menuSt();
			dispFDProc=dispSvProc;
			dispFD();
		}
	}
}

void welcomeEnd()
{
	welcomeEn=0;
	menuSt();
}

void welcomeDisp()
{
	dispCopy(welcomeDispData);
	//dispTs();
	dispRefreshSt();
}
