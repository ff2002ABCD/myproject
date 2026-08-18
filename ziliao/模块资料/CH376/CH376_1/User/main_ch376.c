#include <stdio.h>
#include <string.h>
#include <stm32f10x_lib.h>

#include"file_sys.h"
#include"spi_init.h"
#include"ch376inc.h"
#include"sys.h"
#include"delay.h"
#include"usart.h"
 
UINT8		buf[64];
int 	main(void) 
{	
	UINT8  i,s;
   UINT8	TarName[64];

	JTAG_Set(JTAG_SWD_ENABLE); 
   Stm32_Clock_Init(9);//系统时钟设置 
   delay_init(72);  //延时初始化 
   uart_init(72,9600); //串口 1 初始化  
   SPIx_Init();
	CH376_RST	= 1;			/* 复位 */
	delay_ms( 20 );
	CH376_RST	= 0;				/* 禁止复位 */
	delay_ms( 100 );     /* 延时100毫秒 */
     
	printf( "Start\n" );
	s = mInitCH376Host( );       /* 初始化CH376 */
////////////////////////////////////////////////////////////////
 		   printf("i=%02x \n",(unsigned short)s);
      	printf( "Wait Disk\n" );
         while ( CH376DiskConnect( ) != USB_INT_SUCCESS )/* 检查U盘是否连接,等待U盘插入,对于SD卡,可以由单片机直接查询SD卡座的插拔状态引脚 */
      		{  
      			delay_ms( 100 );
      		}
   		delay_ms( 200 );  // 对于检测到USB设备的,最多等待100*50mS,主要针对有些MP3太慢,对于检测到USB设备
                           //并且连接DISK_MOUNTED的,最多等待5*50mS,主要针对DiskReady不过的  
         for ( i = 0; i < 100; i ++ ) 
            {   
               delay_ms( 50 );
               printf( "Ready ?\n" );
               s = CH376DiskMount( );  //初始化磁盘并测试磁盘是否就绪.   
               if ( s == USB_INT_SUCCESS ) /* 准备好 */
                  break;                                          
               else if ( s == ERR_DISK_DISCON )/* 检测到断开,重新检测并计时 */
                  break;  
               if ( CH376GetDiskStatus( ) >= DEF_DISK_MOUNTED && i >= 5 ) /* 有的U盘总是返回未准备好,不过可以忽略,只要其建立连接MOUNTED且尝试5*50mS */
                  break; 
            }          
         if ( s == ERR_DISK_DISCON ) /* 检测到断开,重新检测并计时 */
            {  
               printf( "Device gone\n" );
               //continue;
            }		
         if ( CH376GetDiskStatus( ) < DEF_DISK_MOUNTED ) /* 未知USB设备,例如USB键盘、打印机等 */
            {  
                printf( "Unknown device\n" );
            }
/////////////////////////////////////获取出厂信息
         i = CH376ReadBlock( buf );  /* 如果需要,可以读取数据块CH376_CMD_DATA.DiskMountInq,返回长度 */
            if ( i == sizeof( INQUIRY_DATA ) )  /* U盘的厂商和产品信息 */
            {  
                  buf[ i ] = 0;
                  printf( "UdiskInfo: %s\n", ((P_INQUIRY_DATA)buf) -> VendorIdStr );
            }
		printf( "DiskQuery: " );		/* 检查U盘或者SD卡的剩余空间 */
		s = CH376DiskQuery( (PUINT32)buf );	/* 查询磁盘剩余空间信息,扇区数 */
		printf("s=%02x \n",(unsigned short)s );
		printf( "free cap = %ld MB\n", *(PUINT32)buf / ( 1000000 / DEF_SECTOR_SIZE ) );
/////////////////////////////////////  创建
		printf( "Create file :" );
		strcpy( (char *)TarName, "\\AAAAAAAA.TXT" ); /* 目标文件名 */
      s = CH376FileCreatePath( TarName );  	/* 新建多级目录下的文件,支持多级目录路径,输入缓冲区必须在RAM中 */
 		printf("s=%02x \n",(unsigned short)s );
////////////////////////////////////// 写入
      printf( "Write ：" );
      strcpy((char *)buf, "兄弟们那个加油哇 呵呵呵呵呵呵呵呵呵呵呵呵呵呵呵呵呵" );
		s = CH376ByteWrite( buf, strlen((const char *)buf), NULL ); /* 以字节为单位向当前位置写入数据块 */
 		printf("s=%02x \n",(unsigned short)s );

 		printf("close file " ); 
 		s = CH376FileClose( TRUE );   /* 关闭文件,对于字节读写建议自动更新文件长度 */
 		printf("s=%02x \n",(unsigned short)s );

   while(1)
      {                                		                        
      }//while（1）
}//main()

























