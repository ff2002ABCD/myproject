#include "gui.h"
#include "stdio.h"
#include "function.h"
int fputc(int ch, FILE* file);
void drawline(uint16_t x1,uint16_t y1,uint16_t x2,uint16_t y2)
{
	printf("line %d,%d,%d,%d,RED\xff\xff\xff",grid_left+x1,grid_up+grid_height-y1,grid_left+x2,grid_up+grid_height-y2);
}

void drawpoint(uint16_t x1,uint16_t y1)
{
	printf("fill %d,%d,3,3,RED\xff\xff\xff",x1,y1);
}

void drawcircle(uint16_t x1,uint16_t y1)
{
	printf("cir %d,%d,1,RED\xff\xff\xff",grid_left+x1,grid_up+grid_height-y1);
}

void renew_screen()
{
	static uint32_t xstart,xend,xstart_last;
	xstart=(current_count-300+65536)%65536;
	xend=(current_count+300+65536)%65536;
	if(xstart_last==xstart) return;
//	if(index_save==index_send) return;
	printf("page 0\xff\xff\xff");

	xstart_last=xstart;
	
	printf("xstart.txt=\"%d\"\xff\xff\xff",xstart);
	printf("xend.txt=\"%d\"\xff\xff\xff",xend);
	if(xstart<xend)
	{
		for(int i=0;i<600-1;i++)
		{
			if(count[(index_save-600+i+MAX_NUM)%MAX_NUM]>=xstart && count[(index_save-600+i+MAX_NUM)%MAX_NUM]<=xend)
			{
			//	drawcircle((count[(index_save-600+i+MAX_NUM)%MAX_NUM]-xstart+65536)%65536,voltage[(index_save-600+i+MAX_NUM)%MAX_NUM]/65536.000*384);
				drawline((count[(index_save-600+i+MAX_NUM)%MAX_NUM]-xstart+65536)%65536,
								voltage[(index_save-600+i+MAX_NUM)%MAX_NUM]/65536.000*384,
								(count[(index_save-600+i+1+MAX_NUM)%MAX_NUM]-xstart+65536)%65536,
								voltage[(index_save-600+i+1+MAX_NUM)%MAX_NUM]/65536.000*384);
			//	HAL_Delay(1);
			}
		}
	}
	else if(xstart>xend)
	{
		for(int i=0;i<600-1;i++)
		{
			if(count[(index_save-600+i+MAX_NUM)%MAX_NUM]>=xstart || count[(index_save-600+i+MAX_NUM)%MAX_NUM]<=xend)
			{
			//	drawcircle((count[(index_save-600+i+MAX_NUM)%MAX_NUM]-xstart+65536)%65536,voltage[(index_save-600+i+MAX_NUM)%MAX_NUM]/65536.000*384);
				drawline((count[(index_save-600+i+MAX_NUM)%MAX_NUM]-xstart+65536)%65536,
									voltage[(index_save-600+i+MAX_NUM)%MAX_NUM]/65536.000*384,
									(count[(index_save-600+i+1+MAX_NUM)%MAX_NUM]-xstart+65536)%65536,
									voltage[(index_save-600+i+1+MAX_NUM)%MAX_NUM]/65536.000*384);
				//	HAL_Delay(1);
			}
		}
	}

}

