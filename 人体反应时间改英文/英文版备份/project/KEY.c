#include "key.h"

void (* keyUpSv)();
void (* keyDownSv)();
void (* keyFunSv)();
void (* keyEntSv)();
void keyAuto();			//10ms
void keySvProc();
void keyAutoEnd();
void keySpeedUp();

bit keyAutoEn,keyPt;
unsigned char keyNum,keySN,keySp;
unsigned char keyCode,keyAutoT;
unsigned char bdata keyt;
sbit PK4=keyt^4;
sbit PK5=keyt^5;
sbit PK6=keyt^6;
sbit PK7=keyt^7;

void keySvNull() {}

void keyRst()
{
	keyAutoEnd();
	keyUpSv=keySvNull;
	keyDownSv=keySvNull;
	keyFunSv=keySvNull;
	keyEntSv=keySvNull;
	keyNum=keyNumN;
	keySN=keySNN0;
	keyPt=0;
}

void keyProc()
{
	keyt=0xff;
	PK4=PKUP;
	PK5=PKDN;
	PK6=PKET;
	PK7=PKFN;
	keyt = ~keyt;
	if (keyt)
		if(keyPt)
		{
			if(!keyAutoEn)
			{
				keySN--;
				if(!keySN)
				{
					keySN=keySNN1;
					keySpeedUp();
				}
			}
		}
		else
		{
			keyNum--;
			if(!keyNum)
			{
				keyPt=1;
				keyCode=keyt;
				keySvProc();
				dispFDProc=dispSvProc;
				dispFD();
			}
		}

	else
	{
		if(keyAutoEn)
		{
			keyAutoEnd();
			dispFDProc=dispSvProc;
			dispFD();
		}
		keyPt=0;														 
		keyNum=keyNumN;
		keySN=keySNN0;
	}

	if(keyAutoEn)
	{
		keyAuto();
	}
}

void keySvProc()
{
	switch (keyCode)
	{
	case 0x10:
		(* keyUpSv)();
		break;
	case 0x20:
		(* keyDownSv)();
		break;
	case 0x40:
		(* keyEntSv)();
		break;
	case 0x80:
		(* keyFunSv)();
	}
}

void keyAuto()
{
	switch (keySp)
	{
	case 1:
		keyAutoT--;
		if(!keyAutoT)
		{
			keyAutoT=keyAutoTN1;
			keySvProc();
			(* dispSvProc)();
			keySN--;
			if(!keySN)
			{
				keySN=keySNN2;
				keySpeedUp();
			}
		}
		break;
	case 2:
		keyAutoT--;
		if(!keyAutoT)
		{
			keyAutoT=keyAutoTN2;
			keySvProc();
			(* dispSvProc)();
			keySN--;
			if(!keySN)
			{
				keySN=keySNN3;
				keySpeedUp();
			}
		}
		break;
	case 3:
		keyAutoT--;
		if(!keyAutoT)
		{
			keyAutoT=keyAutoTN3;
			keySvProc();
			keySvProc();
			keySvProc();
			(* dispSvProc)();
			keySN--;
			if(!keySN)
				keySpeedUp();
		}
		break;
	case 4:
		for(keyAutoT=keyAutoTN4;keyAutoT>0;keyAutoT--)
			keySvProc();
		(* dispSvProc)();
	}
}

void keyAutoEnd()
{
	keyAutoEn=0;
	keySp=0;
}

void keySpeedUp()
{
	keyAutoEn=1;
	keySp++;
	if(keySp>4)
		keySp=4;
	switch (keySp)
	{
	case 1:
		keyAutoT=keyAutoTN1;
		break;
	case 2:
		keyAutoT=keyAutoTN2;
		break;
	case 3:
		keyAutoT=keyAutoTN3;
	}
}

