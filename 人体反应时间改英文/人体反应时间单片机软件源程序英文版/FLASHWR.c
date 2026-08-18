//FLASH读写

#include "flashwr.h"

//flashData[0]为标志位
unsigned char code flashData[512] _at_ FLASHDATAADDR; 
unsigned char xdata flashBkdata[FLASHDATASIZE+1];
unsigned char flashITmp;	//使用局部变量时会出错

//-----------------------------------------------------------------------------
// FLASH写
//-----------------------------------------------------------------------------
void flashWrite (unsigned char index,unsigned char byte)
{
	bit EA_SAVE = EA; // Preserve EA
	char xdata * data pwrite; // FLASH write pointer
	EA = 0; // Disable interrupts
	pwrite = (char xdata *) flashData+index;
	FLKEY = 0xA5; // Key Sequence 1
	FLKEY = 0xF1; // Key Sequence 2
	PSCTL |= 0x01; // PSWE = 1 which enables writes
	*pwrite = byte; // Write the byte
	PSCTL &= ~0x01; // PSWE = 0 which disable writes
	EA = EA_SAVE; // Restore interrupts
}
//-----------------------------------------------------------------------------
// FLASH读
//-----------------------------------------------------------------------------
unsigned char flashRead (unsigned char index)
{
	return flashData[index];
}
//-----------------------------------------------------------------------------
// FLASH擦除
//-----------------------------------------------------------------------------
void flashPageErase ()
{
	bit EA_SAVE = EA; // Preserve EA
	char xdata * data pwrite; // FLASH write pointer
	EA = 0; // Disable interrupts
	pwrite = (char xdata *) flashData;
	FLKEY = 0xA5; // Key Sequence 1
	FLKEY = 0xF1; // Key Sequence 2
	PSCTL |= 0x03; // PSWE = 1; PSEE = 1 擦除
	*pwrite = 0; // Initiate page erase
	PSCTL &= ~0x03; // PSWE = 0; PSEE = 0
	EA = EA_SAVE; // Restore interrupts
}

//FLASH更改数据
void flashChange (unsigned char index,unsigned char byte)
{
	//unsigned char flashITmp;	//使用局部变量时会出错
	for(flashITmp=0;flashITmp<=FLASHDATASIZE;flashITmp++)
		flashBkdata[flashITmp]=flashData[flashITmp];
	flashBkdata[index]=byte;
	flashPageErase ();
	for(flashITmp=0;flashITmp<=FLASHDATASIZE;flashITmp++)
		flashWrite (flashITmp,flashBkdata[flashITmp]);
}

//FLASH初始化
void flashInit()
{
	//unsigned char flashITmp;	//使用局部变量时会出错
	if(flashData[0]!=FLASHON)
	{
		flashPageErase ();
		flashWrite(0,FLASHON);
		for(flashITmp=1;flashITmp<=FLASHDATASIZE;flashITmp++)
			flashWrite(flashITmp,0x00);
	}
}

void flashChangeI(unsigned char index,unsigned int dataI)
{
	//unsigned char flashITmp;	//使用局部变量时会出错
	unsigned char * datap;
	for(flashITmp=0;flashITmp<=FLASHDATASIZE;flashITmp++)
		flashBkdata[flashITmp]=flashData[flashITmp];
	datap=(unsigned char *)& dataI;
	flashBkdata[index]=*datap;
	datap++;
	flashBkdata[index+1]=*datap;
	flashPageErase ();
	for(flashITmp=0;flashITmp<=FLASHDATASIZE;flashITmp++)
		flashWrite (flashITmp,flashBkdata[flashITmp]);
}

unsigned int flashReadI(unsigned char index)
{
	unsigned int iTmp;
	unsigned char * datap;
	datap=(unsigned char *) & iTmp;
	*datap=flashData[index];
	datap++;
	*datap=flashData[index+1];
	return iTmp;
}

#endif		