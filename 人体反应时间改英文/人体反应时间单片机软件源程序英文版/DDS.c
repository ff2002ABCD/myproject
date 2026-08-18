#include "DDS.H"

unsigned long ddsData;
unsigned char ddsMD;

void ddsSvNull() {}

void ddsRst()
{
	ddsMD=0;

	SPI0CFG=0X50;	//SPI MODE 1 12.5MHz
	SPI0CKR=0X00;

	PDDS=0;

	//use f0 in 28bits and p0,reset,sleep,disDAC
	SPI0DAT=0X21;
	while(SPI0CFG & 0X80)
		;
	SPI0DAT=0XC0;
	while(SPI0CFG & 0X80)
		;

	//set F0=Fmclk/1000,f0=0x0041893
	//LSB
	SPI0DAT=0X58;
	while(SPI0CFG & 0X80)
		;
	SPI0DAT=0X53;
	while(SPI0CFG & 0X80)
		;
	//MSB
	SPI0DAT=0X80;
	while(SPI0CFG & 0X80)
		;
	SPI0DAT=0X01;
	while(SPI0CFG & 0X80)
		;

	//set P0=0
	SPI0DAT=0XC0;
	while(SPI0CFG & 0X80)
		;
	SPI0DAT=0X00;
	while(SPI0CFG & 0X80)
		;

	SPI0CFG=SPI0CFGN;	
	SPI0CKR=SPI0CKRN;
}

void ddsSetF(unsigned long fn)		//28bits
{
	unsigned char x[4];
	if(spiBF)
	{
		ddsData=fn;
		ddsMD=1;
	}
	else
	{
		spiBF=1;
		x[1]=fn;
		fn>>=8;
		x[0]=fn&0x3f;
		x[0] |= 0x40;	 	
		fn>>=6;
		x[3]=fn;
		fn>>=8;
		x[2]=fn&0x3f;	 	
		x[2] |= 0x40;	 	
	
		SPI0CFG=0X50;	//SPI MODE 1 12.5MHz
		SPI0CKR=0X00;
	
		//set F0
		//LSB
		SPI0DAT=x[0];
		while(SPI0CFG & 0X80)
			;
		SPI0DAT=x[1];
		while(SPI0CFG & 0X80)
			;
		//MSB
		SPI0DAT=x[2];
		while(SPI0CFG & 0X80)
			;
		SPI0DAT=x[3];
		while(SPI0CFG & 0X80)
			;
	
		SPI0CFG=SPI0CFGN;	
		SPI0CKR=SPI0CKRN;
		spiBF=0;
	}
}

void ddsSetP(unsigned int pn)	//12 bits
{
	unsigned char x[2];
	if(spiBF)
	{
		ddsData=fn;
		ddsMD=2;
	}
	else
	{
		spiBF=1;
		x[1]=pn;
		pn>>=8;
		x[0]=pn&0x1f;
		x[0] |= 0xc0;	 	
	
		SPI0CFG=0X50;	//SPI MODE 1 12.5MHz
		SPI0CKR=0X00;
	
		//set P0
		SPI0DAT=x[0];
		while(SPI0CFG & 0X80)
			;
		SPI0DAT=x[1];
		while(SPI0CFG & 0X80)
			;
	
		SPI0CFG=SPI0CFGN;	
		SPI0CKR=SPI0CKRN;
		spiBF=0;
	}
}

void ddsCfg(unsigned int cfg)	//configdata
{
	unsigned char x[2];
	if(spiBF)
	{
		ddsData=fn;
		ddsMD=2;
	}
	else
	{
		spiBF=1;
		x[1]=cfg;
		pn>>=8;
		x[0]=cfg&0x3f;
	
		SPI0CFG=0X50;	//SPI MODE 1 12.5MHz
		SPI0CKR=0X00;
	
		//set P0
		SPI0DAT=x[0];
		while(SPI0CFG & 0X80)
			;
		SPI0DAT=x[1];
		while(SPI0CFG & 0X80)
			;
	
		SPI0CFG=SPI0CFGN;	
		SPI0CKR=SPI0CKRN;
		spiBF=0;
	}
}

