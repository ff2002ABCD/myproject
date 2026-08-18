#include "RSP.H"
#include <stdlib.h>

#define RSPIODN 10	//delay 10ms

void rspCarProc();
void rspBikeProc();
void rspMP3Proc();
void rspMinMaxDelayProc();
void rspCarSt();
void rspBikeSt();
void rspMP3St();
void rsptime();			//1ms
void rsptimeSt();
void rsptimeEnd();		//put rsptime to rspDTime
void rspCarAga();		//test Again
void rspBikeAga();		//test Again
void rspMP3Aga();		//test Again
void rspMinMaxDelayAga();//max delay
void rspDisp();
void rspDelaySt();		//start Delay 10,000+(rand()>>3)mSec,from 10S to 18S
void rspDelay();		//1ms
void rspEnd();
void rspIO();			//1ms
void rspSpeakerSt();	
void rspSpeaker();		//1ms
void rspMinMaxDelaySt();

unsigned char rspMD,rspMD2;	//MD:mode 1~3
unsigned int rsptimeT;	//test times
unsigned char rspErr;	//Error Times
unsigned char rspIOT;
unsigned char rspDispMD;
unsigned int rspDelayT;
bit rspFW,rspBK,rspHB;
bit rspCarEn,rspBikeEn,rspMP3En,rspMinMaxDelayEn;
bit rspEn,rspDelayEn,rsptimeEn;
unsigned int rspSpeakerI;

void rspSt()	//
{
	rspEn=1;
	rspSpeakerI=0;

	ttlRst();
}

void rspRst()	//	
{
	PFW=1;
	PBK=1;
	PHB=1;
	PRD=1;
	PGN=1;
	PSK=1;

	srand(56);

	rspEn=0;		
	rspDelayEn=0;
	rsptimeEn=0;
	rspIOT=RSPIODN;
}

void rspEnd()
{
	PFW=1;
	PBK=1;
	PHB=1;
	PRD=1;
	PGN=1;
	PSK=1;

	rspEn=0;
	rspCarEn=0;
	rspBikeEn=0;
	rspMP3En=0;		
	rspDelayEn=0;
	rsptimeEn=0;
	rspIOT=RSPIODN;

	menuSt();
}

void rspProc()
{
	if(rspEn)
	{
		switch(rspMD)
		{
		case 1:
			rspCarProc();
			break;
		case 2:
			rspBikeProc();
			break;
		case 3:
			rspMP3Proc(); 
			break;
		case 4:
			rspMinMaxDelayProc();
		}
		
		rsptime();
		rspDelay();
		rspIO();
		rspSpeaker();
	}	
}

void rspCarProc()
{
	if(rspCarEn)
	{
		switch (rspMD2)
		{
		case 2:
			if(!rspFW)
			{
				rspMD2=3;
				rspDelaySt();

				rspDispMD=3;
				dispFDProc=rspDisp;
				dispFD();
			}
			break;
		case 3:
			if(!rspDelayEn)
			{
				rsptimeSt();
				rspMD2=4;

				PGN=1;
				PRD=0;
			}			
			else
			{
				if(rspFW)
				{
					ttlErr++;
					rspMD2=0;
					rspDispMD=4;
					dispFDProc=rspDisp;
					dispFD();
					keyUpSv=ttlSt;
					keyDownSv=ttlRst;
					keyEntSv=rspCarAga;

					PGN=1;
				}
			}
			break;
		case 4:
			if(rsptimeT>RSPTOUTN)
			{
				rsptimeEnd();
				rspDispMD=6;
				dispFDProc=rspDisp;
				dispFD();
				rspMD2=0;
				keyUpSv=ttlSt;
				keyDownSv=ttlRst;
				keyEntSv=rspCarAga;

				PRD=1;
			}
			else
			{
				if(!rspBK)
				{
					rsptimeEnd();
					rspDispMD=5;
					dispFDProc=rspDisp;
					dispFD();
					rspMD2=0;
					keyUpSv=ttlSt;
					keyDownSv=ttlRst;
					keyEntSv=rspCarAga;
					ttlPush(rsptimeT);
					PRD=1;
				}

			}
			break;
		}
	}
}

void rspCarSt()
{
	rspDispMD=1;
	rspMD=1;
	rspMD2=0;
	dispSvProc=rspDisp;
	dispFDProc=rspDisp;
	dispFD();

	rspCarEn=1;

	keyUpSv=ttlSt;
	keyDownSv=ttlRst;
	keyEntSv=rspCarAga;
	keyFunSv=rspEnd;

	rspSt();
}

void rspReturn()
{
	rspDispMD=1;
	dispSvProc=rspDisp;

	keyUpSv=ttlSt;
	keyDownSv=ttlRst;
	if(rspCarEn)
	{
		keyEntSv=rspCarAga;
	}
	else if(rspBikeEn)
	{
		keyEntSv=rspBikeAga;
	}
	else if(rspMP3En)
	{
		keyEntSv=rspMP3Aga;
	}
	keyFunSv=rspEnd;
}

void rsptime()
{
	if(rsptimeEn)
	{
		rsptimeT++;
	}
}

void rsptimeSt()
{
	rsptimeT=0;
	rsptimeEn=1;
}

void rsptimeEnd()
{
	rsptimeEn=0;
}

void rspCarAga()
{
	keyUpSv=keySvNull;
	keyDownSv=keySvNull;
	keyEntSv=keySvNull;
	rspMD2=2;

	rspDispMD=2;
	dispFDProc=rspDisp;
	dispFD();

	PGN=0;
}

void rspIO()
{
	if(PFW ^ rspFW)
	{
		rspIOT--;
		if(!rspIOT)
		{
			rspIOT=RSPIODN;
			rspFW=PFW;
		}
	}
	else if(PBK ^ rspBK)	
	{
		rspIOT--;
		if(!rspIOT)
		{
			rspIOT=RSPIODN;
			rspBK=PBK;
		}
	}
	else if(PHB ^ rspHB)	
	{
		rspIOT--;
		if(!rspIOT)
		{
			rspIOT=RSPIODN;
			rspHB=PHB;
		}
	}
	else
	{
		rspIOT=RSPIODN;
	}
}

void rspDelaySt()
{
	rspDelayT=(rand()>>3)+10000;
	rspDelayEn=1;
}

void rspDelay()
{
	if(rspDelayEn)
	{
		rspDelayT--;
		if(!rspDelayT)
		{
			rspDelayEn=0;
		}
	}
}

unsigned char code rspDispData[8][4][16]={
{	"                ",
	"   Press Set    ",
	"   to start     ",
	"                ",},
{	"  Please step  ",
	"    on the      ",
	"  accelerator   ",
	"                ",},
{	"  Please brake  ",
	"  immediately  ",
	"  when the red  ",
	"  light is on   ",},
{	" You're offside",
	"               ",
	"     Press Set",
	"     to restart ",},
{	"Translation    ",
	"time:         ms",
	"     Press Set",
	"     to restart ",},
{	"    Time out   ",
	"                ",
	"     Press Set",
	"     to restart ",},
{	"  Please brake  ",
	"  immediately  ",
	" After hearing ",
	"   the horn     ",},
{	"Minimum delay:  ",
	"                ",
	"Maximum delay   ",
	"                ",},
};

void rspDisp()
{
	dispCopy(rspDispData[rspDispMD-1]);
	switch (rspDispMD)
	{
	case 5:
		int2char(dispData[1],rsptimeT,0,14);
	}
	dispRefreshSt();
}


void rspBikeProc()
{
	if(rspBikeEn)
	{
		switch (rspMD2)
		{
		case 3:
			if(!rspDelayEn)
			{
				rsptimeSt();
				rspMD2=4;

				PGN=1;
				PRD=0;
			}			
			else
			{
				if(!rspHB)
				{
					ttlErr++;
					rspMD2=0;
					rspDispMD=4;
					dispFDProc=rspDisp;
					dispFD();
					keyUpSv=ttlSt;
					keyDownSv=ttlRst;
					keyEntSv=rspBikeAga;

					PGN=1;
				}
			}
			break;
		case 4:
			if(rsptimeT>RSPTOUTN)
			{
				rsptimeEnd();
				rspDispMD=6;
				dispFDProc=rspDisp;
				dispFD();
				rspMD2=0;
				keyUpSv=ttlSt;
				keyDownSv=ttlRst;
				keyEntSv=rspBikeAga;

				PRD=1;
			}
			else
			{
				if(!rspHB)
				{
					rsptimeEnd();
					rspDispMD=5;
					dispFDProc=rspDisp;
					dispFD();
					rspMD2=0;
					keyUpSv=ttlSt;
					keyDownSv=ttlRst;
					keyEntSv=rspBikeAga;
					ttlPush(rsptimeT);
					PRD=1;
				}
			}
			break;
		}
	}
}

void rspBikeSt()
{
	rspDispMD=1;
	rspMD=2;
	rspMD2=0;
	dispSvProc=rspDisp;
	dispFDProc=rspDisp;
	dispFD();

	rspBikeEn=1;

	keyUpSv=ttlSt;
	keyDownSv=ttlRst;
	keyEntSv=rspBikeAga;
	keyFunSv=rspEnd;

	rspSt();
}

void rspBikeAga()
{
	keyUpSv=keySvNull;
	keyDownSv=keySvNull;
	keyEntSv=keySvNull;
	rspMD2=3;
	rspDelaySt();

	rspDispMD=3;
	dispFDProc=rspDisp;
	dispFD();

	PGN=0;
}

void rspMP3Proc()
{
	if(rspMP3En)
	{
		switch (rspMD2)
		{
		case 3:
			if(!rspDelayEn)
			{
				rsptimeSt();
				rspMD2=4;

				//PGN=1;
				//PSK=0;
				rspSpeakerSt();
			}			
			else
			{
				if(!rspHB)
				{
					ttlErr++;
					rspMD2=0;
					rspDispMD=4;
					dispFDProc=rspDisp;
					dispFD();
					keyUpSv=ttlSt;
					keyDownSv=ttlRst;
					keyEntSv=rspMP3Aga;
					//PGN=1;
				}
			}
			break;
		case 4:
			if(rsptimeT>RSPTOUTN)
			{
				rsptimeEnd();
				rspDispMD=6;
				dispFDProc=rspDisp;
				dispFD();
				rspMD2=0;
				keyUpSv=ttlSt;
				keyDownSv=ttlRst;
				keyEntSv=rspMP3Aga;

				PSK=1;
			}
			else
			{
				if(!rspHB)
				{
					rsptimeEnd();
					rspDispMD=5;
					dispFDProc=rspDisp;
					dispFD();
					rspMD2=0;
					keyUpSv=ttlSt;
					keyDownSv=ttlRst;
					keyEntSv=rspMP3Aga;
  					ttlPush(rsptimeT);

					PSK=1;
				}
			}
			break;
		}
	}
}

void rspMP3St()
{
	rspDispMD=1;
	rspMD=3;
	rspMD2=0;
	dispSvProc=rspDisp;
	dispFDProc=rspDisp;
	dispFD();

	rspMP3En=1;

	keyUpSv=ttlSt;
	keyDownSv=ttlRst;
	keyEntSv=rspMP3Aga;
	keyFunSv=rspEnd;

	rspSt();
}

void rspMP3Aga()
{
	keyUpSv=keySvNull;
	keyDownSv=keySvNull;
	keyEntSv=keySvNull;
	rspMD2=3;
	rspDelaySt();

	rspDispMD=7;
	dispFDProc=rspDisp;
	dispFD();

	//PGN=0;
}

void rspSpeakerSt()
{
	rspSpeakerI=RSPSPEAKERT;
}
	
void rspSpeaker()
{
	if(rspSpeakerI)
	{
		rspSpeakerI--;
		PSK=0;
	}
	else
	{
		PSK=1;
	}
}

//最小延时
void rspMinMaxDelaySt()
{
	rspDispMD=1;
	rspMD=4;
	rspMD2=0;
	dispSvProc=rspDisp;
	dispFDProc=rspDisp;
	dispFD();

	rspMinMaxDelayEn=1;

	keyUpSv=ttlSt;
	keyDownSv=ttlRst;
	keyEntSv=rspMinMaxDelayAga;
	keyFunSv=rspEnd;

	rspSt();
}

//最大延时
void rspMinMaxDelayAga()
{
	keyUpSv=keySvNull;
	keyDownSv=keySvNull;
	keyEntSv=keySvNull;
	rspMD2=1;
	rspDelaySt();

	rspDispMD=7;
	dispFDProc=rspDisp;
	dispFD();

	//PGN=0;
}
