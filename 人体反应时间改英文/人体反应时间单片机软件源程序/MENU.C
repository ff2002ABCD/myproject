#include "MENU.H"

#define MENUC 16
#define MENU0MAX 3

bit menu0En;
unsigned char (* menu0p) [MENUC];
unsigned char menu0Index;
unsigned char menu0SelI;

void menuUp();
void menuDown();
void menuDisp();
void menuEnt();

#if MENU0MAX<4
#define MENU0R 4
#else
#define MENU0R MENU0MAX
#endif
unsigned char code menuListData[MENU0R][MENUC]={
	"汽车测试        ",
	"自行车测试      ",
	"声音测试        ",
	"                ",
};

void menuSt()
{
	menu0En=1;
	keyUpSv=menuUp;
	keyDownSv=menuDown;
	keyFunSv=keySvNull;
	keyEntSv=menuEnt;
	dispSvProc=menuDisp;
	menuDisp();
}

void menuEnd()
{
	menu0En=0;
	dispSelSt(0);	//关选项
}

void menuRst()
{
	menu0p=menuListData;
	menu0Index=1;
	menu0SelI=1;
}

#if MENU0MAX<4
#define MENU0S MENU0MAX
#else
#define MENU0S 4
#endif

void menuUp()
{
	if(menu0Index>1)
	{
		menu0Index--;
		if(menu0SelI>1)
			menu0SelI--;
		else
			menu0p--;
	}
	else
	{
		menu0Index=MENU0MAX;
		menu0SelI=MENU0S;
		menu0p=menuListData+MENU0R-4;
	}
}

void menuDown()
{
	if(menu0Index<MENU0MAX)
	{
		menu0Index++;
		if(menu0SelI<4)
			menu0SelI++;
		else
			menu0p++;
			
	}
	else
	{
		menu0Index=1;
		menu0SelI=1;
		menu0p=menuListData;
	}
}

void menuDisp()
{
	dispCopy(menu0p);
	dispRefreshSt();
	dispSelSt(menu0SelI);
}

void menuEnt()
{
	menuEnd();
	switch (menu0Index)
	{
	case 1:
		rspCarSt();
		break;
	case 2:
		rspBikeSt();
		break;
	case 3:
		rspMP3St();
		break;
	case 4:
		//pwmSt();
		break;
	case 5:
		//sgmSt();
		break;
	default:
		menuRst();
		menuSt();
	}

}
	
#undef MENUR 
#undef MENUC 
#undef MENU0MAX 
