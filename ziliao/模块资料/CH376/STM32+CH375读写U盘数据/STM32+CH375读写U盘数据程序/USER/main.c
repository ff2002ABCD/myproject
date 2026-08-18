/**
  ******************************************************************************
  * @file    main.c
  * @author  西电 刘亮
  * @version V1.0
  * @date    2021-2-12
  * @brief   STM32+CH375读写U盘数据
  ******************************************************************************
  * 硬件平台	 :正点原子STM32F103精英板(其他32开发板同样适用)+CH375模块+LCD显示屏+U盘
  * 本人QQ   :1920108735
  * 本人能力有限，设计难免有问题和漏洞，欢迎大家交流讨论。
  ******************************************************************************
  */ 
#include "main.h"
/**
  * @brief  主函数
  * @param  无
  * @retval 无
  */
int main(void)
{
	SYS_Init();									//系统初始化总函数
	Udish_Init();
	while(1)									//主循环
	{	
		Main_Disp();							//主菜单显示界面
		key = KEY_Scan(0);						//按键扫描
		switch (key)							//键值判断
		{
			case WKUP_PRES:Udish_Init();break;	//U盘初始化及属性参数读取			
			case KEY0_PRES:Udish_Read();break;	//U盘读操作实例		
			case KEY1_PRES:Udish_Write();break;	//U盘写操作实例
			default:break;						//默认方法
		}
	} 
}
/**
  * @brief  系统初始化总函数
  * @param  无
  * @retval 无
  */
void SYS_Init(void)
{
	delay_init();	    						//延时函数初始化	  
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);	 //设置NVIC中断分组2:2位抢占优先级，2位响应优先级
	uart_init(115200);	 						//串口初始化为115200
//	LED_Init();			     					//LED端口初始化
	KEY_Init();									//按键初始化
//	LCD_Init();             					//显示屏初始化
//	TPAD_Init();								//触摸键初始化
//	Lsens_Init(); 								//光敏传感器初始化
}
/**
  * @brief  主菜单显示界面函数
  * @param  无
  * @retval 无
  */
void Main_Disp(void)
{
	POINT_COLOR=RED;							//设置画笔颜色
	LCD_ShowString(40,80,240,24,24,(u8*)"UDisk Control System");	//LCD显示字符串
	POINT_COLOR=BLACK;							//设置画笔颜色
	LCD_ShowString(60,170,240,16,16,(u8*)"WKUP:  Initialization");	//LCD显示字符串
	LCD_ShowString(60,200,240,16,16,(u8*)"KEY0:  Read Information");	//LCD显示字符串
	LCD_ShowString(60,230,240,16,16,(u8*)"KEY1:  Write Information");//LCD显示字符串	
	LCD_ShowString(60,260,240,16,16,(u8*)"TPAD:  Return");	//LCD显示字符串
	i+=20;if(i>0XFFFF)i=0;						//画笔颜色渐变
	POINT_COLOR=i;								//画笔颜色赋值	
	LCD_DrawRectangle(50,160,270,288);			//LCD显示矩形
}
/**
  * @brief  U盘初始化及属性参数读取函数
  * @param  无
  * @retval 无
  */
void Udish_Init(void)
{
	struct znFAT_Init_Args Init_Args;			//znFAT初始化结构体
//	LCD_Clear(WHITE);							//清屏
//	POINT_COLOR=RED;							//画笔颜色赋值
//	LCD_ShowString(80,40,200,24,24,(u8*)"Initialization");//LCD显示字符串
//	POINT_COLOR=BLACK;							//画笔颜色赋值
	CH375_Configuration();						//CH375时钟引脚配置
	status=CH375_Init();						//CH375芯片初始化
	if(status==0)								//运行返回值判断
	{
		printf("CH375初始化成功");				//串口数据上报
//		LCD_ShowString(40,100,200,16,16,(u8*)"CH375 Init:  Success");//LCD显示字符串
	}
	else
	{
		printf("CH375初始化失败");				//串口数据上报
//		LCD_ShowString(40,100,200,16,16,(u8*)"CH375 Init:  failed");//LCD显示字符串
	}
	CH375_WriteCmd(CMD_GET_IC_VER);				//写入CH375芯片及固件版本命令
	status = CH375_ReadDat();					//读取接收数据
	printf("CH375 版本:0X%x\r\n",status);		//串口数据上报
	sprintf((char*)str,"CH375 Vision:  0X%x",status);//字符串格式化
//	LCD_ShowString(40,130,200,16,16,str);		//LCD显示字符串	
	status = znFAT_Device_Init();				//存储设备初始化
	if(status==0)								//运行返回值判断
	{
		printf("U盘初始化成功");					//串口数据上报
//		LCD_ShowString(40,160,200,16,16,(u8*)"U_dish Init:  Success");//LCD显示字符串
	}
	else
	{
		printf("U盘初始化失败");					//串口数据上报
//		LCD_ShowString(40,160,200,16,16,(u8*)"U_dish Init:  Failed");//LCD显示字符串
		goto X;									//直接跳到该程序结束处
	}
	
	znFAT_Select_Device(0,&Init_Args);			//选定存储设备
	znFAT_Init();								//znFAT文件系统初始化
	printf("U盘容量:%ldKB\r\n",Init_Args.Total_SizeKB);//串口数据上报
//	sprintf((char*)str,"Udish SizeKB:%ldKB",Init_Args.Total_SizeKB);//字符串格式化
//	LCD_ShowString(40,190,300,16,16,str);		//LCD显示字符串
	printf("U盘引导扇区号:%ldKB\r\n",Init_Args.BPB_Sector_No);//串口数据上报
//	sprintf((char*)str,"Udish BPB_Sector_No:%ld",Init_Args.BPB_Sector_No);//字符串格式化
//	LCD_ShowString(40,220,300,16,16,str);		//LCD显示字符串
	printf("U盘每个扇区大小:%ldB\r\n",Init_Args.BytesPerSector);//串口数据上报
//	sprintf((char*)str,"Udish BytesPerSector:%ldB",Init_Args.BytesPerSector);//字符串格式化
//	LCD_ShowString(40,250,300,16,16,str);		//LCD显示字符串
	printf("U盘FAT表占扇区数:%ld\r\n",Init_Args.FATsectors);//串口数据上报
//	sprintf((char*)str,"Udish FATsectors:%ld",Init_Args.FATsectors);//字符串格式化
//	LCD_ShowString(40,280,300,16,16,str);		//LCD显示字符串
	printf("U盘每簇扇区数:%ld\r\n",Init_Args.SectorsPerClust);//串口数据上报
//	sprintf((char*)str,"Udish SectorsPerClust:%ld",Init_Args.SectorsPerClust);//字符串格式化
//	LCD_ShowString(40,310,300,16,16,str);		//LCD显示字符串
	printf("U盘首个FAT表所在扇区:%ld\r\n",Init_Args.FirstFATSector);//串口数据上报
//	sprintf((char*)str,"Udish FirstFATSector:%ld",Init_Args.FirstFATSector);//字符串格式化
//	LCD_ShowString(40,340,300,16,16,str);		//LCD显示字符串
	printf("U盘首个目录所在扇区:%ld\r\n",Init_Args.FirstDirSector);//串口数据上报
//	sprintf((char*)str,"Udish FirstDirSector:%ld",Init_Args.FirstDirSector);//字符串格式化
//	LCD_ShowString(40,370,300,16,16,str);		//LCD显示字符串
	printf("U盘空闲簇的数量:%ld\r\n",Init_Args.Free_nCluster);//串口数据上报
//	sprintf((char*)str,"Udish Free_nCluster:%ld",Init_Args.Free_nCluster);//字符串格式化
//	LCD_ShowString(40,400,300,16,16,str);		//LCD显示字符串
	printf("U盘可用容量:%ldKB\r\n",(u32)Init_Args.Free_nCluster*Init_Args.SectorsPerClust*Init_Args.BytesPerSector/1024);//串口数据上报
//	sprintf((char*)str,"Udish Free_SizeKB:%ldKB",(u32)Init_Args.Free_nCluster*Init_Args.SectorsPerClust*Init_Args.BytesPerSector/1024);//字符串格式化
//	LCD_ShowString(40,430,300,16,16,str);		//LCD显示字符串
	znFAT_Flush_FS();							//刷新文件系统
	while(1)									//循环，等待退出
	{
		if(TPAD_Scan(0))						//检测到触摸按键按下
		{
			LCD_Clear(WHITE);					//清屏
			goto X;								//跳出循环，至函数末	
		}
		delay_ms(10);							//延时
	}
	X:;
}
/**
  * @brief  U盘读操作实例函数
  * @param  无
  * @retval 无
  */
void Udish_Read(void)
{
	struct znFAT_Init_Args Init_Args;			//znFAT初始化结构体 
	struct FileInfo fileinfo;					//znFAT文件属性结构体
	UINT8 read_test[30] = "";					//读空字符串	
	LCD_Clear(WHITE);							//清屏
	POINT_COLOR=RED;							//画笔颜色赋值
	LCD_ShowString(100,40,200,24,24,(u8*)"READ TASK");//LCD显示字符串
	POINT_COLOR=BLACK;							//画笔颜色赋值
	CH375_Configuration();						//CH375时钟引脚配置
	status=CH375_Init();						//CH375芯片初始化
	if(status==0)								//运行返回值判断
	{
		printf("CH375初始化成功");				//串口数据上报
		LCD_ShowString(40,100,200,16,16,(u8*)"CH375 Init:  Success");//LCD显示字符串
	}
	else
	{
		printf("CH375初始化失败");				//串口数据上报
		LCD_ShowString(40,100,200,16,16,(u8*)"CH375 Init:  failed");//LCD显示字符串
	}
	status = znFAT_Device_Init();				//存储设备初始化
	if(status==0)								//运行返回值判断
	{
		printf("U盘初始化成功");					//串口数据上报
		LCD_ShowString(40,130,200,16,16,(u8*)"U_dish Init:  Success");//LCD显示字符串
	}
	else
	{
		printf("U盘初始化失败");					//串口数据上报
		LCD_ShowString(40,130,200,16,16,(u8*)"U_dish Init:  Failed");//LCD显示字符串
	}
	znFAT_Select_Device(0,&Init_Args);			//选定存储设备
	znFAT_Init();								//znFAT文件系统初始化
	status=znFAT_Init(); 						//文件系统初始化
	if(!status)									//如果打开文件成功
	{
		printf("文件系统初始化成功\n");			//串口数据上报
		LCD_ShowString(40,160,200,16,16,(u8*)"znFAT_Init Init:  Success");//LCD显示字符串
	}
	else
	{
		printf("文件系统初始化失败\n");			//串口数据上报
		LCD_ShowString(40,160,300,16,16,(u8*)"znFAT_Init Init:  Failed");//LCD显示字符串
	}
	
	status=znFAT_Open_File(&fileinfo,"/time.txt",0,1);//打开指定文件
	if(!status)									//打开文件成功
	{
		printf("打开文件成功\r\n");				//串口数据上报
		LCD_ShowString(40,190,300,16,16,(u8*)"File opened successfully");//LCD显示字符串
		
		printf("文件名为:%s\r\n",fileinfo.File_Name);//串口数据上报
		sprintf((char*)str,"File name:  %s",fileinfo.File_Name);//字符串格式化
		LCD_ShowString(40,220,300,16,16,str);	//LCD显示字符串
		
		znFAT_ReadData(&fileinfo,0,18,read_test);//文件数据读取
		printf("文件大小:%d(bytes)\n",(int)fileinfo.File_Size);//串口数据上报
		sprintf((char*)str,"File Size:  %dB",(int)fileinfo.File_Size);//字符串格式化
		LCD_ShowString(40,250,300,16,16,str);	//LCD显示字符串
		
		printf("文件内容:%s\r\n",read_test);		//串口数据上报
		sprintf((char*)str,"Content:  %s",read_test);//字符串格式化
		LCD_ShowString(40,280,300,16,16,str);	//LCD显示字符串	
	}
	else
	{
		printf("打开文件失败\n");				//串口数据上报
		LCD_ShowString(40,190,300,16,16,(u8*)"Fail to open file");//LCD显示字符串
	}
	znFAT_Close_File(&fileinfo);				//关闭文件
	znFAT_Flush_FS();							//刷新文件系统
	while(1)									//循环，等待退出
	{
		if(TPAD_Scan(0))						//检测到触摸按键按下
		{
			LCD_Clear(WHITE);					//清屏
			goto Y;								//跳出循环，至函数末	
		}
		delay_ms(10);							//延时
	}
	Y:;
}
/**
  * @brief  U盘写操作实例函数
  * @param  无
  * @retval 无
  */
void Udish_Write(void)
{
	struct znFAT_Init_Args Init_Args;			//znFAT初始化结构体  
	struct FileInfo fileinfo;					//znFAT文件属性结构体
	struct DateTime dt;							//时间信息
	UINT8 write_test[200] = "";					//写空字符串
	u8 adcx;									//ADC数据采集变量
	u8 i;										//内部循环变量
	UINT32 len;									//写入数据长度变量
	LCD_Clear(WHITE);							//清屏
	POINT_COLOR=RED;							//画笔颜色赋值
	LCD_ShowString(100,40,200,24,24,(u8*)"WRITE TASK");//LCD显示字符串
	POINT_COLOR=BLACK;							//画笔颜色赋值
	CH375_Configuration();						//CH375时钟引脚配置	
	status=CH375_Init();						//CH375芯片初始化
	if(status==0)								//运行返回值判断
	{
		printf("CH375初始化成功");				//串口数据上报
		LCD_ShowString(40,100,200,16,16,(u8*)"CH375 Init:  Success");//LCD显示字符串
	}
	else
	{
		printf("CH375初始化失败");				//串口数据上报
		LCD_ShowString(40,100,200,16,16,(u8*)"CH375 Init:  failed");//LCD显示字符串
	}
	status = znFAT_Device_Init();				//存储设备初始化
	if(status==0)								//运行返回值判断
	{
		printf("U盘初始化成功");					//串口数据上报
		LCD_ShowString(40,130,200,16,16,(u8*)"U_dish Init:  Success");//LCD显示字符串
	}
	else
	{
		printf("U盘初始化失败");					//串口数据上报
		LCD_ShowString(40,130,200,16,16,(u8*)"U_dish Init:  Failed");//LCD显示字符串
	}
	znFAT_Select_Device(0,&Init_Args);			//选定存储设备
	znFAT_Init();								//znFAT文件系统初始化
	status=znFAT_Init(); 						//文件系统初始化
	if(!status) 								//如果打开文件成功
	{
		printf("文件系统初始化成功\n");			//串口数据上报
		LCD_ShowString(40,160,200,16,16,(u8*)"znFAT_Init Init:  Success");//LCD显示字符串
	}
	else
	{
		printf("文件系统初始化失败\n");			//串口数据上报
		LCD_ShowString(40,160,200,16,16,(u8*)"znFAT_Init Init:  Failed");//LCD显示字符串
	}
	POINT_COLOR=BLUE;							//设置字体为蓝色
	LCD_ShowString(40,190,200,16,16,(u8*)"LSENS_VAL:");//LCD显示字符串	
	for(i = 0;i<=20;i++)						//循环任务
	{
		adcx=Lsens_Get_Val();					//光强ADC数据采集
		LCD_ShowxNum(120,190,adcx,3,16,0);		//显示ADC的值 
		delay_ms(500);							//延时	
		sprintf((char*)str,"%d:  %d\r",i,adcx);	//字符串格式化
		strcat((char*)write_test,(char*)str);	//字符串追加
	}
	printf("text:%s",write_test);				//串口数据上报
	if(!znFAT_Create_File(&fileinfo,"/adc.txt",&dt))//文件创建成功事件
	{
		LCD_ShowString(40,220,200,16,16,(u8*)"Create File:  Success");//LCD显示字符串
		printf("文件名为:%s\r\n",fileinfo.File_Name);//串口数据上报
		sprintf((char*)str,"File name:  %s",fileinfo.File_Name);//字符串格式化
		LCD_ShowString(40,250,300,16,16,str);	//LCD显示字符串
		printf("文件大小:%d(bytes)\n",(int)fileinfo.File_Size);//串口数据上报
		sprintf((char*)str,"File Size:  %dB",(int)fileinfo.File_Size);//字符串格式化
		LCD_ShowString(40,280,300,16,16,str);	//LCD显示字符串
		znFAT_Flush_FS();						//刷新文件系统
		len=znFAT_WriteData(&fileinfo,sizeof(write_test),write_test);//向文件中写入数据
		if(len)									//写入成功
		{
			printf("写入数据成功\n");			//串口数据上报
			LCD_ShowString(40,310,200,16,16,(u8*)"Write Data:  Success");//LCD显示字符串	
			printf("写入数据大小:%d(bytes)\n",(int)len);//串口数据上报
			sprintf((char*)str,"Write Data Length:  %dB",(int)len);//字符串格式化
			LCD_ShowString(40,340,300,16,16,str);//LCD显示字符串
		}
		else									//写入失败
		{
			printf("写入数据失败\n");			//串口数据上报
			LCD_ShowString(40,310,300,16,16,(u8*)"Write Data:  Failed");//LCD显示字符串
		}
		znFAT_Close_File(&fileinfo);			//关闭文件
	}
	else										//文件创建失败事件
	{
		printf("fail to create file.\n");		//串口数据上报
		LCD_ShowString(40,220,200,16,16,(u8*)"Create File:  Failed");//LCD显示字符串
	}
	znFAT_Flush_FS();							//刷新文件系统
	while(1)									//循环，等待退出
	{
		if(TPAD_Scan(0))						//检测到触摸按键按下
		{
			LCD_Clear(WHITE);					//清屏
			goto Z;								//跳出循环，至函数末	
		}
		delay_ms(10);							//延时
	}
	Z:;
}
