//TMR2L专用中断
#include "DISPLCD.H"

void (*dispSvProc) ();
void (*dispFDProc) ();

bit dispSelCG;
unsigned char dispData[LCDCHR][LCDCHC];

bit lcdBF0,lcdBF1,lcdWrDC,lcdGCrH;
bit dispRefreshEn,lcdWrEn,lcdWr1En,dispInitEn;
bit dispRefreshWk,lcdGCrWk,dispInitWk,lcdGCrEn;
bit dispSelWk,dispSelEn;
unsigned char disp0Datai,disp0Dataj,disp0Mth;
unsigned char lcdWrData,lcdWrMth;
unsigned char dispSelMth,dispInitMth,lcdGCrMth,dispSeli,dispSelj;
unsigned char disp180usT,dispSelI0,dispSelI1;
unsigned char lcdData[LCDCHR][LCDCHC];

extern void dispRefresh();
extern void lcdWrSt(unsigned char,unsigned char);
extern void lcdWr();
extern void dispInitSt();
extern void dispInit();
extern void dispSelSt(unsigned char index)	 ;
extern void dispSel();
extern void dispSelTs(unsigned char);
extern void lcdGCr();
extern void dispSt();
extern void dispEnd();
extern void dispSvNull();

void dispRefreshSt()
{
	if(!dispRefreshEn)
	{
		dispTs();
		disp0Mth=0;
		disp0Datai=0;
		disp0Dataj=0;
		dispRefreshEn=1;
		dispSt();
	}
}

void dispRefresh() using 2
{
	if(!lcdBF1)
	{
		switch (disp0Mth)
		{
			case 0:
				lcdWrSt(0,0x30);	//基本指令
				disp0Mth++;
				break;
			case 1:
				lcdWrSt(0,0x80);	//设定DDRAM地址0
				disp0Mth++;
				break;
			case 2:
				if(disp0Datai<LCDCHR)
					if(disp0Dataj<LCDCHC)
						lcdWrSt(1,lcdData[disp0Datai][disp0Dataj++]);
					else
						{
							disp0Datai++;
							disp0Dataj=0;
						}
				else
				{
					disp0Datai=0;
					disp0Dataj=0;
					disp0Mth++;
				}
				break;
			default:
				dispRefreshEn=0;	//结束
				disp0Datai=0;
				disp0Dataj=0;
				disp0Mth=0;
				dispRefreshWk=0;
				lcdBF0=0;
		}
	}
}

void lcdWrSt(unsigned char dc,unsigned char wrData)	 using 2
{
	lcdBF1=1;
	lcdWrData=wrData;
	lcdWrDC=dc;
	lcdWrMth=0;
	lcdWrEn=1;
}


void lcdWr() using 2
{
	if(!(SPI0CFG & 0x80))
		switch (lcdWrMth)
		{
			case 0:
				spiBF=1;
				SPI0CKR=0x3C;
			    SPI0CFG=0x60;
				lcdWrMth++;
				break;
			case 1:
				PDCS=0;
				lcdWrMth++;
				break;
			case 2:
				if(lcdWrDC)
					SPI0DAT=0xfa;	//data
				else
					SPI0DAT=0xf8;	//cmd
				lcdWrMth++;
				break;
			case 3:
				SPI0DAT=lcdWrData&0xf0;		//D7~D4
				lcdWrMth++;
				break;
			case 4:
				SPI0DAT=lcdWrData<<4;	//D3~D0
				lcdWrMth++;
				break;
			case 5:
				PDCS=1;
				lcdWrEn=0;		//结束
				lcdBF1=0;
		}
}

void dispRst()
{
	unsigned char i,j;
	PDRST=0;
	PDCS=1;
	spiRst();
	dispEnd();
	dispSvProc=dispSvNull;
	dispFDProc=dispSvNull;
	dispRefreshEn=0;
	dispRefreshWk=0;
	lcdGCrWk=0;
	dispInitWk=0;
	lcdGCrEn=0;
	dispInitEn=0;
	lcdWrEn=0;
	lcdBF0=0;
	lcdBF1=0;
	disp0Mth=0;
	disp0Datai=0;
	disp0Dataj=0;
	dispSelI0=0;
	dispSelI1=0;
	disp180usT=disp180usTN;
	dispSelI0=0;
	dispSelI1=0;
	dispSelCG=0;
	for(i=0;i<255;i++)
		for(j=0;j<255;j++)
		;
	PDRST=1;
	dispInitSt();
	lcdGCrSt();
}


void dispInitSt()
{
	if(!dispInitEn)
	{
		dispSt();
		disp0Mth=0;
		dispInitEn=1;
	}
}

void dispInit() using 2
{
	if(!lcdBF1)
	{
		switch(disp0Mth)
		{
			case 0:
				lcdWrSt(0,0x30);disp0Mth++;break;	
			case 1:
				lcdWrSt(0,0x01);disp0Mth++;break;
			case 15:
				lcdWrSt(0,0x06);disp0Mth++;break;
			case 16:
				lcdWrSt(0,0x0c);disp0Mth++;break;
			case 17:
				dispInitEn=0;
				dispInitWk=0;
				disp0Mth=0;
				lcdBF0=0;
				break;
			default:
				disp0Mth++;
		}
	}
}

void lcdGCrSt()
{
	if(!lcdGCrEn)
	{
		dispSt();
		disp0Datai=0;
		disp0Dataj=0;
		lcdGCrMth=0;
		lcdGCrH=0;
		lcdGCrEn=1;
	}
}

void lcdGCr() using 2
{
	if(!lcdBF1)
	{
		if(disp0Datai<0x20)
		{
			switch(lcdGCrMth)
			{
				case 0:
					lcdWrSt(0,0x34);
					lcdGCrMth++;
					break;
				case 1:
					lcdWrSt(0,disp0Datai+0x80);
					lcdGCrMth++;
					break;
				case 2:
					lcdWrSt(0,0x80);
					lcdGCrMth++;
					break;
				case 3:
					lcdWrSt(0,0x30);
					lcdGCrMth++;
					break;
				case 4:
						if(disp0Dataj<0x20)
						{
							lcdWrSt(1,0x00);
							disp0Dataj++;
						}
						else
						{
							disp0Dataj=0;
							lcdGCrMth=0;
							disp0Datai++;
						}
			}
		}
		else
		{
			lcdGCrEn=0;
			lcdGCrWk=0;
			disp0Datai=0;
			disp0Dataj=0;
			disp0Mth=0;
			lcdBF0=0;
		}
	}
}


void dispCopy(unsigned char code p[LCDCHR][LCDCHC])
{
	int i,j;
	for(i=0;i<LCDCHR;i++)
		for(j=0;j<LCDCHC;j++)
			dispData[i][j]=p[i][j];
}

void dispTs()
{
	unsigned char i,j;
	for(i=0;i<LCDCHR;i++)
		switch (i)
		{
		case 0:
			for(j=0;j<0x10;j++)
				lcdData[0][j]=dispData[0][j];
			break;
		case 1:
			for(j=0;j<0x10;j++)
				lcdData[2][j]=dispData[1][j];
			break;
		case 2:
			for(j=0;j<0x10;j++)
				lcdData[1][j]=dispData[2][j];
			break;
		case 3:
			for(j=0;j<0x10;j++)
				lcdData[3][j]=dispData[3][j];
		}
}

void dispSel() using 2
{
	if(!lcdBF1)
	{
		switch (disp0Mth)
		{
		case 0:
			if (dispSelI0)
			{
				dispSelTs(dispSelI0);
				disp0Mth=1;
			}
			else
			{
				dispSelI0=dispSelI1;
				if(dispSelI0)
				{
					dispSelTs(dispSelI0);
					disp0Mth=2;
				}
				else
					disp0Mth=3;
			}
			break;
		case 1:
			if(disp0Datai<16)
				switch(dispSelMth)
				{
				case 0:
					lcdWrSt(0,0x34);
					dispSelMth++;break;
				case 1:
					lcdWrSt(0,dispSeli+disp0Datai);
					dispSelMth++;break;
				case 2:
					lcdWrSt(0,dispSelj);
					dispSelMth++;break;
				case 3:
					lcdWrSt(0,0x30);
					dispSelMth++;break;
				case 4:
					if(disp0Dataj<0x10)
					{
						lcdWrSt(1,0x00);
						disp0Dataj++;
					}
					else
					{
						disp0Dataj=0;
						dispSelMth=0;
						disp0Datai++;
					}
				}
			else
			{
				dispSelI0=dispSelI1;
				if(dispSelI0)
				{
					dispSelTs(dispSelI0);
					disp0Datai=0;
					disp0Dataj=0;
					dispSelMth=0;
					disp0Mth++;
				}
				else
					disp0Mth=3;
			}
			break;
		case 2:
			if(disp0Datai<16)
			{
				switch(dispSelMth)
				{
				case 0:
					lcdWrSt(0,0x34);
					dispSelMth++;break;
				case 1:
					lcdWrSt(0,dispSeli+disp0Datai);
					dispSelMth++;break;
				case 2:
					lcdWrSt(0,dispSelj);
					dispSelMth++;break;
				case 3:
					lcdWrSt(0,0x30);
					dispSelMth++;break;
				case 4:
					if(disp0Dataj<0x10)
					{
						lcdWrSt(1,0xff);
						disp0Dataj++;
					}
					else
					{
						disp0Dataj=0;
						dispSelMth=0;
						disp0Datai++;
					}
				}
				break;
			}
		default:
				lcdWrSt(0,0x36);
				dispSelWk=0;
				dispSelEn=0;
				disp0Datai=0;
				disp0Dataj=0;
				disp0Mth=0;
				lcdBF0=0;
		}
	}
}

void dispSelTs(unsigned char index)
{
	switch (index)
	{
	case 1:
		dispSeli=0x80;
		dispSelj=0x80;
		break;
	case 2:
		dispSeli=0x80+16;
		dispSelj=0x80;
		break;
	case 3:
		dispSeli=0x80;
		dispSelj=0x80+8;
		break;
	default:
		dispSeli=0x80+16;
		dispSelj=0x80+8;
	}
}						   

void dispSelSt(unsigned char index)
{
	if(!dispSelEn)
	{
		dispSt();
		dispSelI1=index;
		dispSelMth=0;
		dispSelEn=1;
	}
}


#define dex 1
unsigned int lcddly=dex;

bit spid=0;

void dispInt() interrupt INTERRUPT_TIMER2 using 2
{
	TF2H=0;
	TF2L=0;
	if(lcdWrEn)
		lcdWr();
	if(!disp180usT--)
	{
		if(lcdBF0)
		{
			if(dispRefreshWk)
				dispRefresh();
			if(dispInitWk)
				dispInit();
			if(lcdGCrWk)
				lcdGCr();
			if(dispSelWk)
				dispSel();
		}
		else
		{
			if(spid | !spiBF)
			if(dispRefreshEn)
			{
				spiBF=1;
				spid=1;
				dispRefreshWk=1;
				dispRefresh();
				lcdBF0=1;
			}
			else if(dispInitEn)
			{
				spiBF=1;
				spid=1;
				dispInitWk=1;
				dispInit();
				lcdBF0=1;
			}
			else if(lcdGCrEn)
			{
				spiBF=1;
				spid=1;
				lcdGCrWk=1;
				lcdGCr();
				lcdBF0=1;
			}
			else if(dispSelEn)
			{
				spiBF=1;
				spid=1;
				dispSelWk=1;
				dispSel();
				lcdBF0=1;
			}
			else
			{
				dispEnd();
			}
		}
		disp180usT=disp180usTN;
	}
}

void dispSt()
{
	DISPEN=1;
}

void dispEnd() using 2
{
	DISPEN=0;
	spiBF=0;
	spid=0;
}


void dispFD()
{
	if(!DISPEN)
	{
		(* dispFDProc)();
		dispFDProc=dispSvNull;
	}
}

void dispSvNull(){}
	
