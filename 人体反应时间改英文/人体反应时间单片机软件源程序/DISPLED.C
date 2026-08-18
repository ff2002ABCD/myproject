#include "DISPLED.H"

#define PCS P22

unsigned char displedData[8];

bit displedBF;
unsigned char displedDataH,displedDataL,displedMD,displedI.displedMD2;

void displedRefresh()		//trans displedData to MAX7219
{
	displedMD=1;
	displedMD2=0;		
}

void displedSetNum(unsigned char num)		//set led number
{
	displedDataH=0X0B;
	displedDataL=num-1;
	displedMD=2;
	displedMD2=1;		
}

void displedTurnOn() 		//turn on led
{
	displedDataH=0X0C;
	displedDataL=0X01;
	displedMD=2;
	displedMD2=1;		
}

void displedTurnOff();		//turn off led
{
	displedDataH=0X0C;
	displedDataL=0X00;
	displedMD=2;
	displedMD2=1;		
}

void displedSetIntens(unsigned char its)		//set led intensity
{
	displedDataH=0X0A;
	displedDataL=its;
	displedMD=2;
	displedMD2=1;		
}

void displedRst()			//reset	turn on led decode mode B displedData=0;
{
	int i,j;
	spiRst();
	while(spiBusy)
		;
	for(i=1;i<9;i++)
	{
		spiTrans(i);
		while(spiBusy())
			;
		spiTrans(0);
		while(spiBusy())
			;
	}
	spiTrans(0x09);		//decode mode
	while(spiBusy())
		;
	spiTrans(0xff);
	while(spiBusy())
		;

	spiTrans(0x0a);		//intensity
	while(spiBusy())
		;
	spiTrans(0x0a);
	while(spiBusy())
		;

	spiTrans(0x0b);
	while(spiBusy())
		;
	spiTrans(0x07);		//8 leds
	while(spiBusy())
		;

	spiTrans(0x0c);
	while(spiBusy())
		;
	spiTrans(0x01);		//turn on
	while(spiBusy())
		;
}

void displedSetDM(unsigned char dm) 			//set decode mode
{
	displedDataH=0X09;
	displedDataL=dm;
	displedMD=2;
	displedMD2=1;		
}

void displedProc()			//1ms
{
	if(!SPIBF)
	{
		switch(displedMD)	//CONTROL
		{
		case 1:
			SPIBF=1;
			if(displedI<8)
			{
				if(!displedMD2)
				{
					displedMD2=1;
					displedDataL=displedData[displedI];
					displedI++;
					displedDataH=displedI;
				}
			}
			else
			{
				displedMD=0;
				SPIBF=0;
				displedBF=0;
			}
		case 2:
			SPIBF=1;
			if(!displedMD2)
			{
				displedMD=0;
				SPIBF=0;
				displedBF=0;
			}
		}

		switch(displedMD2)	//TRANS
		{
		case 1:
			PCS=0;
			displedMD2++;
		case 2:
			if(!spiBusy())
			{
				spiTrans(displedDataH);
			}
			displedMD2++;
		case 2:
			if(!spiBusy())
			{
				spiTrans(displedDataL);
			}
			displedMD2++;
		case 4:
			PCS=1;
			displedMD2=0;
		}
	}
}

