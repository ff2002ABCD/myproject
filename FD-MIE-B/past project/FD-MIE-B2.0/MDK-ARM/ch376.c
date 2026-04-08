#include "ch376.h"
#include "main.h"
#include "usart.h"
#include "stdio.h"
#include "string.h"
#include "FILE_SYS.H"
#include "menu.h"
#include "function.h"

_Bool init_flag=0;
_Bool output_flag=0;

void xWriteCH376Cmd( unsigned char cmd ) { 
	uint8_t command[3]={0x57,0xAB,cmd};
	HAL_UART_Transmit(&huart2, command, 3,HAL_MAX_DELAY);
}

void xWriteCH376Data( unsigned char dat ) {
	uint8_t *data=&dat;
	HAL_UART_Transmit(&huart2, data, 1,HAL_MAX_DELAY);
}

/* 串口方式未用到 */
void xEndCH376Cmd(void)
{
}

unsigned char xReadCH376Data(void) { 
	uint8_t buffer[1];
	HAL_UART_Receive(&huart2, buffer, 1,100);
	return buffer[0];
}

uint8_t CH376_TestConnection(void) { 
    uint8_t response;
		uint8_t test_data=0x53;
		xWriteCH376Cmd(CMD_CHECK_EXIST);
		xWriteCH376Data(test_data);
		response=xReadCH376Data();
//		xWriteCH376Data(response);
//		printf("res=%x\r\n",response);
    if (response == (uint8_t)(~test_data)) {
        return 1;  
    } else {
        return 0;  
    }
}

/* 查询CH376中断(INT#低电平) */
UINT8	Query376Interrupt( void )
{
	#ifdef	CH376_INT_WIRE                  /* 如果连接了CH376的中断引脚则直接查询中断引脚 */
		if(CH376_INT_WIRE) return FALSE ;
		else{
			//xReadCH376Data();               //产生中断的同时，串口会收到一个数据，直接读出来丢掉
			return TRUE ;
		}
	#else
		if (USART2->ISR & 0x80) {
			return( TRUE );
		}
		else return( FALSE );
	#endif	
}

uint8_t file_writeData(char * buf)
{
	uint8_t s,i=0;
//	printf("数据长度%d...",strlen(buf));
	xWriteCH376Cmd(CMD2H_BYTE_WRITE);
	xWriteCH376Data(strlen(buf)%256);
	xWriteCH376Data(strlen(buf)>>8);
		//printf("正在写入数据...");
//xWriteCH376Cmd(CMD_WR_REQ_DATA);
	while(1)
	{
		s = xReadCH376Data();
		
		if ( s == USB_INT_DISK_WRITE ) {
	//		xWriteCH376Data(*buf);
			s = CH376WriteReqBlock( (PUINT8)buf );
			xWriteCH376Cmd( CMD0H_BYTE_WR_GO );
			xEndCH376Cmd( );
			buf += s;
		}
		else if ( s == USB_INT_SUCCESS ) return(s);//*/  /* 结束 */
	}
 
	return s;
}

void ch376_init()
{
	init_flag=0;
//	printf("t2.txt=\"Start\"\xff\xff\xff");
	if (CH376_TestConnection()) {
     printf("CH376 is connected and working!\xff\xff\xff");
		init_flag=1;
   } 
	else
	{
     printf("CH376 connection failed!\xff\xff\xff");
		return;
  }
	//选择u盘模式
	printf("正在选择u盘模式...\xff\xff\xff");
	xWriteCH376Cmd(CMD_SET_USB_MODE);
	xWriteCH376Data(0x06);
		if(xReadCH376Data()==0x51)
		{
			if(xReadCH376Data()==0x15)
			{
				
				printf("t2.txt=\"设置成功\"\xff\xff\xff");
			}
			else{init_flag=0;}
		}	
//		else{init_flag=0;}
	//判断是否连接
//	printf("正在检查u盘连接...\xff\xff\xff");
	CH376DiskConnect();
	if(xReadCH376Data()==USB_INT_SUCCESS) 
	{
	//	printf("连接成功\xff\xff\xff");
	}
	else {}
	//初始化磁盘
//	printf("正在初始化磁盘\xff\xff\xff");
	if(CH376DiskMount()==USB_INT_SUCCESS) 
	{
//		printf("已就绪\xff\xff\xff");
	}
	else {

	}
}

void ch376_writetest()
{
	//打开目录
	char str[200];
	sprintf(str,"/XP.CSV");
//	printf("正在打开目录...\xff\xff\xff");
	if(CH376FileCreate((PUINT8)str)==USB_INT_SUCCESS)
	{
	//	printf("打开成功\xff\xff\xff");
	}
	else 
	{
	//	return;
	//	printf("开启失败\xff\xff\xff");
	}
	//获取当前文件大小
//	uint32_t size=CH376GetFileSize();
//	printf("size=%d\r\n",size);
	//写入表头
	if(file_writeData(",动镜行程(nm),光功率(μW)\n")
		==USB_INT_SUCCESS) 
	{
	//	printf("写入成功\xff\xff\xff");
	}
	else 
	{
	//	return;
	//	printf("写入失败\xff\xff\xff");
	}
	//按行写入数据
	for(int i=0;i<index_save;i++)
	{
		printf("progress.val=%.0f\xff\xff\xff",i/(float)index_save*100);
		sprintf(str,"%d,%d,%.1f\n",i+1,count[i]*5,(VOLTAGE_CENTER+VOLTAGE_INPUT_RANGE/65536.000*voltage[i])*1000);
		if(file_writeData(str)==USB_INT_SUCCESS)
		{			
			//printf("写入成功\xff\xff\xff");
		}
		else 
		{
		//	printf("写入失败\xff\xff\xff");
		}
	}

	
//	size=CH376GetFileSize();
//	printf("filesize=%d\xff\xff\xff",size);
	//关闭文件
//	printf("正在关闭文件\xff\xff\xff");
	
	if(CH376FileClose(1)==USB_INT_SUCCESS){
	//printf("关闭成功\xff\xff\xff");
	output_flag=1;
	}
	else output_flag=0;
	
}

void ch376_writetest_angle()
{
	//打开目录
	char str[200];
	sprintf(str,"/AP.CSV");
//	printf("正在打开目录...\xff\xff\xff");
	if(CH376FileCreate((PUINT8)str)==USB_INT_SUCCESS)
	{
	//	printf("打开成功\xff\xff\xff");
	}
	else 
	{
	//	return;
	//	printf("开启失败\xff\xff\xff");
	}
	//获取当前文件大小
//	uint32_t size=CH376GetFileSize();
//	printf("size=%d\r\n",size);
	//写入表头
	if(file_writeData(",角度(°),光功率(μW)\n")
		==USB_INT_SUCCESS) 
	{
	//	printf("写入成功\xff\xff\xff");
	}
	else 
	{
	//	return;
	//	printf("写入失败\xff\xff\xff");
	}
	//按行写入数据
	for(int i=0;i<index_save_angle;i++)
	{
		printf("progress.val=%.0f\xff\xff\xff",i/(float)index_save_angle*100);
		sprintf(str,"%d,%.2f,%.1f\n",i+1,angle[i]*0.18,(VOLTAGE_CENTER+VOLTAGE_INPUT_RANGE/65536.000*voltage_angle[i])*1000);
		if(file_writeData(str)==USB_INT_SUCCESS)
		{			
			//printf("写入成功\xff\xff\xff");
		}
		else 
		{
		//	printf("写入失败\xff\xff\xff");
		}
	}

	
//	size=CH376GetFileSize();
//	printf("filesize=%d\xff\xff\xff",size);
	//关闭文件
//	printf("正在关闭文件\xff\xff\xff");
	
	if(CH376FileClose(1)==USB_INT_SUCCESS){
	//printf("关闭成功\xff\xff\xff");
	output_flag=1;
	}
	else output_flag=0;
	
}

void ch376_writetest_time()
{
	//打开目录
	char str[200];
	sprintf(str,"/TP.CSV");
//	printf("正在打开目录...\xff\xff\xff");
	if(CH376FileCreate((PUINT8)str)==USB_INT_SUCCESS)
	{
	//	printf("打开成功\xff\xff\xff");
	}
	else 
	{
	//	return;
	//	printf("开启失败\xff\xff\xff");
	}
	//获取当前文件大小
//	uint32_t size=CH376GetFileSize();
//	printf("size=%d\r\n",size);
	//写入表头
	if(file_writeData(",时间(s),光功率(μW)\n")
		==USB_INT_SUCCESS) 
	{
	//	printf("写入成功\xff\xff\xff");
	}
	else 
	{
	//	return;
	//	printf("写入失败\xff\xff\xff");
	}
	//按行写入数据
	for(int i=0;i<index_save_time;i++)
	{
		printf("progress.val=%.0f\xff\xff\xff",i/(float)index_save_time*100);
		sprintf(str,"%d,%.1f,%.1f\n",i+1,time[i]/10.0,(VOLTAGE_CENTER+VOLTAGE_INPUT_RANGE/65536.000*voltage_time[i])*1000);
		if(file_writeData(str)==USB_INT_SUCCESS)
		{			
			//printf("写入成功\xff\xff\xff");
		}
		else 
		{
		//	printf("写入失败\xff\xff\xff");
		}
	}

	
//	size=CH376GetFileSize();
//	printf("filesize=%d\xff\xff\xff",size);
	//关闭文件
//	printf("正在关闭文件\xff\xff\xff");
	
	if(CH376FileClose(1)==USB_INT_SUCCESS){
	//printf("关闭成功\xff\xff\xff");
	output_flag=1;
	}
	else output_flag=0;
	
}


