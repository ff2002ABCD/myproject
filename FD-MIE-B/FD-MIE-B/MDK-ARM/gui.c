#include "gui.h"
#include "stdio.h"
#include "function.h"
#include "menu.h"

int fputc(int ch, FILE* file);
void drawline(int16_t x1,int16_t y1,int16_t x2,int16_t y2)
{
	if(y1<10||y1>grid_height-10) return;
	if(y2<10||y2>grid_height-10) return;
	printf("line %d,%d,%d,%d,RED\xff\xff\xff",
		grid_left+x1/xgrid_multiple_journey[xgrid_multiple_journey_index],grid_up+grid_height-2-y1,
		grid_left+x2/xgrid_multiple_journey[xgrid_multiple_journey_index],grid_up+grid_height-2-y2);
}

void drawpoint(uint16_t x1,uint16_t y1)
{
	printf("fill %d,%d,3,3,RED\xff\xff\xff",x1,y1);
}

void drawcircle(uint16_t x1,uint16_t y1)
{
	if(y1<=1||y1>grid_height-2) return;
	if(page==MEA_JOURNEY||page==QUERY_JOURNEY)
		printf("cir %d,%d,1,RED\xff\xff\xff",grid_left+x1/xgrid_multiple_journey[xgrid_multiple_journey_index],
		grid_up+grid_height-1-y1);
	else if(page==MEA_ANGLE||page==QUERY_ANGLE)
		printf("cir %d,%d,1,RED\xff\xff\xff",grid_left+x1/xgrid_multiple_angle[xgrid_multiple_angle_index],
		grid_up+grid_height-1-y1);}


void renew_screen()
{
	
	static float min;
	min=100;
	static int32_t xstart,xend,xstart_last,xnow;
	static uint8_t xgrid_multiple_journey_index_last,ygrid_multiple_journey_index_last;
		xstart=current_count-(grid_width-1)/2*xgrid_multiple_journey[xgrid_multiple_journey_index]
				+2000*round_now-30000;
		xend=current_count+(grid_width-1)/2*xgrid_multiple_journey[xgrid_multiple_journey_index]
				+2000*round_now-30000;
	if(page==QUERY_JOURNEY)
	{
		xstart+=x_offset_journey*xgrid_multiple_journey[xgrid_multiple_journey_index];
		xend+=x_offset_journey*xgrid_multiple_journey[xgrid_multiple_journey_index];
//		if(x_offset_journey>-count[index_save-1]/xgrid_multiple_journey[xgrid_multiple_journey_index])
//		x_offset_journey=-count[index_save-1]/xgrid_multiple_journey[xgrid_multiple_journey_index];
		if(x_offset_journey>=(count_max-count[index_save-1])/xgrid_multiple_journey[xgrid_multiple_journey_index])
		{
			x_offset_journey=(count_max-count[index_save-1])/xgrid_multiple_journey[xgrid_multiple_journey_index];
		}
		if(x_offset_journey<=(count_min-count[index_save-1])/xgrid_multiple_journey[xgrid_multiple_journey_index])
		{
			x_offset_journey=(count_min-count[index_save-1])/xgrid_multiple_journey[xgrid_multiple_journey_index];
		}
	}
	else 
	{
		x_offset_journey=0;
	}
	
	
	xnow=(xstart+xend)/2*5;
	
	if(xstart_last==xstart
		&&xgrid_multiple_journey_index==xgrid_multiple_journey_index_last
		&&ygrid_multiple_journey_index==ygrid_multiple_journey_index_last
		&&renew_screen_flag==0
		) return;
	renew_screen_flag=0;
//	if(button_called==1) {button_called=0;return;}
//	x_offset_journey=x_offset_journey*xgrid_multiple_journey[xgrid_multiple_journey_index_last]/
//								xgrid_multiple_journey[xgrid_multiple_journey_index];
	xgrid_multiple_journey_index_last=xgrid_multiple_journey_index;
	ygrid_multiple_journey_index_last=ygrid_multiple_journey_index;
//	printf("page 0\xff\xff\xff");
	printf("ref 1\xff\xff\xff");
//	HAL_Delay(20);
	xstart_last=xstart;
	printf("xstart.txt=\"%d\"\xff\xff\xff",xstart);
	printf("xend.txt=\"%d\"\xff\xff\xff",xend);
	printf("xnow.txt=\"%dnm\"\xff\xff\xff",xnow);
//	printf("vol.txt=\" \"\xff\xff\xff");
	if(page==MEA_JOURNEY&& index_save>1)
	printf("vol.txt=\"%.1fμW\"\xff\xff\xff",(VOLTAGE_CENTER+VOLTAGE_INPUT_RANGE/65536.000*voltage[index_save-1])*1000);
	printf("x_grid.txt=\"%s/格\"\xff\xff\xff",xgrid_txt_journey[xgrid_multiple_journey_index]);
	printf("y_grid.txt=\"%s/格\"\xff\xff\xff",ygrid_txt_journey[ygrid_multiple_journey_index]);

	if(index_save==0) return;
	
	
	for(int i=0;i<index_save-1;i+=xgrid_multiple_journey[xgrid_multiple_journey_index])
	{		
	//筛选输出范围
		if(count[i]>=xstart && count[i]<=xend)
		{
			//筛选光标位置
			if(fabs(count[i]-(xstart+xend)/2)<=100&&page==QUERY_JOURNEY)
			{ 
				if(fabs(count[i]-(xstart+xend)/2)<min)
				{
					min=fabs(count[i]-(xstart+xend)/2);
					printf("vol.txt=\"%.1fμW\"\xff\xff\xff",(VOLTAGE_CENTER+VOLTAGE_INPUT_RANGE/65536.000
						*voltage[i])*1000);
				}
			}
			if(voltage[(i+MAX_NUM_JOURNEY)%MAX_NUM_JOURNEY]==0) continue;
//			drawcircle(count[i]-xstart,voltage[i]/65536.000*(grid_height-1)*ygrid_multiple_journey[ygrid_multiple_journey_index]+(grid_height-1)*(1/2.00
//							+(ygrid_multiple_journey[ygrid_multiple_journey_index]-1)/3.00)
//			
//			);
			drawline(count[i]-xstart,voltage[i]/65536.000*(grid_height-1)*ygrid_multiple_journey[ygrid_multiple_journey_index]+(grid_height-1)*(1/2.00
							+(ygrid_multiple_journey[ygrid_multiple_journey_index]-1)/3.00),
			count[i+1]-xstart,voltage[i+1]/65536.000*(grid_height-1)*ygrid_multiple_journey[ygrid_multiple_journey_index]+(grid_height-1)*(1/2.00
							+(ygrid_multiple_journey[ygrid_multiple_journey_index]-1)/3.00)
			);
		}

	}
}

void renew_screen_angle()
{
	static float min;
	min=100;
	static int32_t xstart,xend,xstart_last,xnow;
	static uint8_t xgrid_multiple_angle_index_last,ygrid_multiple_angle_index_last;
	xstart=current_angle-(grid_width-1)/4/2*xgrid_multiple_angle[xgrid_multiple_angle_index]+2000*round_now_angle-30000;
	xend=current_angle+(grid_width-1)/4/2*xgrid_multiple_angle[xgrid_multiple_angle_index]+2000*round_now_angle-30000;
	if(page==QUERY_ANGLE)
	{
		xstart+=x_offset_angle*xgrid_multiple_angle[xgrid_multiple_angle_index];
		xend+=x_offset_angle*xgrid_multiple_angle[xgrid_multiple_angle_index];
		if(x_offset_angle>=(angle_max-angle[index_save_angle-1])/xgrid_multiple_angle[xgrid_multiple_angle_index])
		{
			x_offset_angle=(angle_max-angle[index_save_angle-1])/xgrid_multiple_angle[xgrid_multiple_angle_index];
		}
		if(x_offset_angle<=(angle_min-angle[index_save_angle-1])/xgrid_multiple_angle[xgrid_multiple_angle_index])
		{
			x_offset_angle=(angle_min-angle[index_save_angle-1])/xgrid_multiple_angle[xgrid_multiple_angle_index];
		}
	}
	else 
	{
		x_offset_angle=0;
	}
	
	
	xnow=(xstart+xend)/2*18;
	if(xstart_last==xstart
		&&xgrid_multiple_angle_index==xgrid_multiple_angle_index_last
		&&ygrid_multiple_angle_index==ygrid_multiple_angle_index_last
		&&renew_screen_flag==0
		) return;
	renew_screen_flag=0;
	xgrid_multiple_angle_index_last=xgrid_multiple_angle_index;
	ygrid_multiple_angle_index_last=ygrid_multiple_angle_index;
	
	printf("ref 1\xff\xff\xff");
	HAL_Delay(20);
	xstart_last=xstart;
	printf("xstart.txt=\"%d\"\xff\xff\xff",xstart);
	printf("xend.txt=\"%d\"\xff\xff\xff",xend);
	printf("xnow.txt=\"%.2f°\"\xff\xff\xff",xnow/100.00);
//	printf("vol.txt=\" \"\xff\xff\xff");
	if(page==MEA_ANGLE &&index_save>1)
	printf("vol.txt=\"%.1fμW\"\xff\xff\xff",(VOLTAGE_CENTER+VOLTAGE_INPUT_RANGE/65536.000*voltage_angle[index_save_angle-1])*1000);
	
	printf("x_grid.txt=\"%s/格\"\xff\xff\xff",xgrid_txt_angle[xgrid_multiple_angle_index]);
	printf("y_grid.txt=\"%s/格\"\xff\xff\xff",ygrid_txt_angle[ygrid_multiple_angle_index]);

	if(index_save_angle==0) return;
	for(int i=0;i<index_save_angle-1;i++)
	{
		
		//筛选输出范围
		if(angle[i]>=xstart 
			&& angle[i]<=xend)
		{
			//筛选光标位置
			if(fabs(angle[i]-(xstart+xend)/2)<=100&&
				page==QUERY_ANGLE)
			{
				if(fabs(angle[i]-(xstart+xend)/2)<min)
				{
					min=fabs(angle[i]-(xstart+xend)/2);
					printf("vol.txt=\"%.1fμW\"\xff\xff\xff",(VOLTAGE_CENTER+VOLTAGE_INPUT_RANGE/65536.000*
							voltage_angle[i])*1000);
				}	
			}
			if(voltage_angle[i]==0) continue;
//				drawcircle((angle[i]-xstart)*4,
//										voltage_angle[i]/65536.000
//									*(grid_height-1)*ygrid_multiple_angle[ygrid_multiple_angle_index]+(grid_height-1)*(1/2.00
//									+(ygrid_multiple_angle[ygrid_multiple_angle_index]-1)/3.00)
//				);
				drawline((angle[i]-xstart)*4,
										voltage_angle[i]/65536.000
									*(grid_height-1)*ygrid_multiple_angle[ygrid_multiple_angle_index]+(grid_height-1)*(1/2.00
									+(ygrid_multiple_angle[ygrid_multiple_angle_index]-1)/3.00),
									(angle[i+1]-xstart)*4,
										voltage_angle[i+1]/65536.000
									*(grid_height-1)*ygrid_multiple_angle[ygrid_multiple_angle_index]+(grid_height-1)*(1/2.00
									+(ygrid_multiple_angle[ygrid_multiple_angle_index]-1)/3.00)
				);
	//			drawline((angle[(index_save_angle-((grid_width-1)/4-i)*xgrid_multiple_angle[xgrid_multiple_angle_index]
	//									+MAX_NUM_ANGLE)%MAX_NUM_ANGLE]-xstart)*4,
	//							voltage_angle[(index_save_angle-((grid_width-1)/4-i)*xgrid_multiple_angle[xgrid_multiple_angle_index]
	//									+MAX_NUM_ANGLE)%MAX_NUM_ANGLE]/65536.000
	//									*(grid_height-1)*ygrid_multiple_angle[ygrid_multiple_angle_index]+(grid_height-1)/2,
	//							(angle[(index_save_angle-((grid_width-1)/4-i-1)*xgrid_multiple_angle[xgrid_multiple_angle_index]
	//									+MAX_NUM_ANGLE)%MAX_NUM_ANGLE]-xstart)*4,
	//							voltage_angle[(index_save_angle-((grid_width-1)/4-i-1)*xgrid_multiple_angle[xgrid_multiple_angle_index]
	//									+MAX_NUM_ANGLE)%MAX_NUM_ANGLE]/65536.000*
	//									(grid_height-1)*ygrid_multiple_angle[ygrid_multiple_angle_index]+(grid_height-1)/2);			
		}
	}
}

void renew_screen_time()
{
	printf("x_grid.txt=\"%ds/格\"\xff\xff\xff",5*sample_interval);
//	printf("x_grid.txt=\"%s/格\"\xff\xff\xff",xgrid_txt_time[xgrid_multiple_time_index]);
	printf("y_grid.txt=\"%s/格\"\xff\xff\xff",ygrid_txt_time[ygrid_multiple_time_index]);
	printf("xnow.txt=\"%.1fs\"\xff\xff\xff",time[index_save_time-1]/10.000);
	printf("vol.txt=\"%.1fμW\"\xff\xff\xff",(VOLTAGE_CENTER+VOLTAGE_INPUT_RANGE/65536.000*voltage_time[index_save_time-1])*1000);
	if(index_save_time>=2)
	printf("add 1,0,%.0f\xff\xff\xff",voltage_time[index_save_time-1]/65536.000
								*256*ygrid_multiple_time[ygrid_multiple_time_index]+256*(1/2.00
								+(ygrid_multiple_time[ygrid_multiple_time_index]-1)/3.00)
				);
}

void renew_query_time()
{
	static float xnow=0;
	if(renew_screen_flag==0)return;
	renew_screen_flag=0;
	printf("x_grid.txt=\"%ds/格\"\xff\xff\xff",5*sample_interval*xgrid_multiple_time[xgrid_multiple_time_index]);
//	printf("x_grid.txt=\"%s/格\"\xff\xff\xff",xgrid_txt_time[xgrid_multiple_time_index]);
	printf("y_grid.txt=\"%s/格\"\xff\xff\xff",ygrid_txt_time[ygrid_multiple_time_index]);
	xnow=((int)time[index_save_time-1-x_offset_time*xgrid_multiple_time[xgrid_multiple_time_index]]
											-query_grid*sample_interval*xgrid_multiple_time[xgrid_multiple_time_index]
											)/10.000;
	printf("xnow.txt=\"%.1fs\"\xff\xff\xff",xnow);
	if(index_save_time>query_grid&&xnow>0)	
		printf("vol.txt=\"%.1fμW\"\xff\xff\xff",(VOLTAGE_CENTER+VOLTAGE_INPUT_RANGE/65536.000*
															voltage_time[index_save_time-1-(x_offset_time+query_grid)
															*xgrid_multiple_time[xgrid_multiple_time_index]])*1000);
	else printf("vol.txt=\" \"\xff\xff\xff");
	printf("cle 1,0\xff\xff\xff");
	HAL_Delay(50);
//	for(int i=0;i<800;i++)
//	{
//		if(index_save_time+i*xgrid_multiple_time[xgrid_multiple_time_index]<=
//			(x_offset_time+800)*xgrid_multiple_time[xgrid_multiple_time_index]) continue;
//		printf("add 1,0,%.0f\xff\xff\xff",voltage_time[index_save_time+(i-800-x_offset_time)
//						*xgrid_multiple_time[xgrid_multiple_time_index]
//						]/65536.000
//								*256*ygrid_multiple_time[ygrid_multiple_time_index]+256*(1/2.00
//								+(ygrid_multiple_time[ygrid_multiple_time_index]-1)/3.00)
//				);
//	}
	static int i;
	for(i=0;i<800;i++)
	{
		if(index_save_time+i*xgrid_multiple_time[xgrid_multiple_time_index]>
			(x_offset_time+800)*xgrid_multiple_time[xgrid_multiple_time_index]) break;
	}
	printf("addt 1,0,%d\xff\xff\xff",800-i);
	HAL_Delay(50);
	for(;i<800;i++)
	{
		printf("%c",(int)(voltage_time[index_save_time+(i-800-x_offset_time)
						*xgrid_multiple_time[xgrid_multiple_time_index]
						]/65536.000
								*256*ygrid_multiple_time[ygrid_multiple_time_index]+256*(1/2.00
								+(ygrid_multiple_time[ygrid_multiple_time_index]-1)/3.00)));
	}
	printf("\x01\xff\xff\xff");
	
}
