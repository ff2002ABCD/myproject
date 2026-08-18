#include "uart0.h"

void uart0TProc();
void uart0RProc();

bit uart0TBusy,uart0RBusy,uart0Tf;
bit urat0TEn,uart0REn;
unsigned char uart0Ti,uart0Tlen,uart0Ri,uart0Rlen;
unsigned char *uart0TDatap,*uart0Rdatap;


void uart0Proc() //1ms
{
	unsigned char t;
	if(uart0TBusy)
	{
		uart0TProc();
	}
	if(uart0RBusy)
	{
		uart0RProc();
	}
}

void uart0TProc()
{
	if(uart0TBusy)
	{
		if(uart0Tf)
		{
			uart0tf=0;
			SBUF0=uart0TDatap[uart0Ti];
			uart0Ti++;
		}
		if(TI0)
		{
			TI0=0;
			if(uart0Ti<uart0Tlen)
			{
				uart0Tf=1;
			}
			else
			{
				uart0TBusy=0;
			}
		}
	}
}

void uart0TSt(unsigned char *tdatap,unsigned char len)
{
	uart0TDatap=tdatap;
	uart0Tlen=len;
	uart0Ti=0;
	if(len)
	{
		uart0Tf=1;
	}
	TI0=0;

	uart0TBusy=1;
}

void uart0RProc()
{
	if(uart0RBusy)
	{
		if(RI0)
		{
			RI0=0;
			if(uart0Ri<uart0Rlen)
			{
				uart0RDatap[uart0Ri]=SBUF0;
				uart0Ri++;
			}
			if(uart0Ri>=uart0Rlen)
			{
				uart0RBusy=0;
			}
		}
	}
}

void uart0RSt(unsigned char *rdatap,unsigned char len)
{
	uart0RDatap=rdatap;
	uart0Rlen=len;
	uart0Ri=0;
	RI0=0;

	uart0RBusy=1;
}

void uart0Rst()
{
	uart0RBusy=0;
	uart0TBusy=0;
}
