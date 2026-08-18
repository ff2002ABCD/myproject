#include "TTL.h"

void ttlPageDown();
void ttlPageUp();
void ttlEnt();
void ttlDisp();

unsigned char ttlLn,ttlErr,ttlPage,ttlDispMD;
unsigned int ttlData[TTLDATAN];

void ttlSt()
{
	ttlPage=0;
	ttlDispMD=0;
	dispSvProc=ttlDisp;

	keyUpSv=keySvNull;
	keyDownSv=keySvNull;
	keyEntSv=ttlEnt;
	keyFunSv=rspReturn;
}

void ttlRst()
{
	ttlLn=0;
	ttlErr=0;
}

void ttlPageDown()
{
	ttlPage++;
	if(ttlPage>ttlLn/4)
	{
		ttlPage=0;
	}
}

void ttlPageUp()
{
	if(ttlPage)
	{
		ttlPage--;
	}
	else
	{
		ttlPage=ttlLn/4;
	}
}

void ttlEnt()
{
	if(ttlDispMD)
	{
		ttlDispMD=0;
		keyUpSv=keySvNull;
		keyDownSv=keySvNull;
	}
	else
	{
		ttlDispMD=1;
		keyUpSv=ttlPageUp;
		keyDownSv=ttlPageDown;
	}
}

unsigned char code ttlDispData[3][4][16]={
{	"Average grade: ",
	"              ms",
	"Number of fouls:",
	"           times",},
{	"                ",
	"                ",
	"                ",
	"                ",},
{	"No tests at all ",
	"                ",
	"Press Return to",
	"return test page",}};

void ttlDisp()
{
	unsigned char i,j;
	unsigned long s;

	if(ttlLn)
	{
		dispCopy(ttlDispData[ttlDispMD]);
		if(ttlDispMD)
		{
		 	for(i=ttlPage*4,j=0;j<4 && i<ttlLn;j++,i++)
			{
				int2char(dispData[j],i+1,0,2);
				dispData[j][2]=':';
				int2char(dispData[j]+3,ttlData[i],0,11);
				dispData[j][14]='m';
				dispData[j][15]='s';
			}
		}
		else
		{
			for(i=0,s=0;i<ttlLn;i++)
			{
				s+=ttlData[i];
			}
			s/=ttlLn;
			int2char(dispData[1],s,0,14);
			int2char(dispData[3],ttlErr,0,14);
		}
	}
	else
	{
		dispCopy(ttlDispData[2]);
	}

	dispRefreshSt();
}

void ttlPush(unsigned int x)
{
	int i;
	for(i=TTLDATAN-1;i;i--)
	{
		ttlData[i]=ttlData[i-1];
	}
	ttlData[0]=x;

	if(ttlLn<TTLDATAN)
	{
		ttlLn++;
	}
}

