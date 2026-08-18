#ifndef RSP_H
#define RSP_H

#include "C8051F410X.H"
#include "KEY.H"
#include "MENU.H"
#include "DISPLCD.H"
#include "MATHFUN.H"
#include "TTL.H"

#define PFW P14		//油门 低电平有效
#define PBK P15		//刹车 低电平有效
#define PHB P16		//手刹 低电平有效
#define PRD P02		//绿灯 低电平有效
#define PGN P03		//红灯 低电平有效
#define PSK P17		//喇叭 低电平有效

#define RSPTOUTN 10000 //10S超时
#define RSPSPEAKERT 1000	//1S喇叭声

extern void rspSt();
extern void rspRst();
extern void rspProc();		//1ms
extern void rspCarSt();
extern void rspBikeSt();
extern void rspMP3St();
extern void rspReturn();	//返回测试界面

#endif
