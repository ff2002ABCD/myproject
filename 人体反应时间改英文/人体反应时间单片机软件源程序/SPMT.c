#include "SPMT.H"

unsigned char code spmtData[4]={
0X10,0X40,0X20,0X80};
unsigned char spmtIn,spmtIt;

void spmtRst()
{
	P1 &= 0X0F;
	spmtI=0;
}

void spmtStep(i)
{
	spmtIt=i;
}

void spmtProc()
{
	if(spmtIt)
	{
		spmtIt--;
		spmtIn++;
		P1 &= 0X0F;
		P1 |= spmtData[spmtIn];
	}
}



