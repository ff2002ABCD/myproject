#include "ch376.h"
#include "main.h"
#include "usart.h"
#include "stdio.h"
#include "string.h"
#include "stdlib.h"
#include "FILE_SYS.H"
#include "menu.h"
#include "stm32f1xx_hal.h"


_Bool init_flag=0;
extern _Bool output_flag;

void xWriteCH376Cmd( unsigned char cmd ) { 
	uint8_t command[3]={0x57,0xAB,cmd};
	HAL_UART_Transmit(&huart2, command, 3,HAL_MAX_DELAY);
}

void xWriteCH376Data( unsigned char dat ) {
	uint8_t *data=&dat;
	HAL_UART_Transmit(&huart2, data, 1,HAL_MAX_DELAY);
}

/* 锟斤拷锟节凤拷式未锟矫碉拷 */
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

/* 锟斤拷询CH376锟叫讹拷(INT#锟酵碉拷平) */
UINT8	Query376Interrupt( void )
{
	#ifdef	CH376_INT_WIRE                  /* 锟斤拷锟斤拷锟斤拷锟斤拷锟紺H376锟斤拷锟叫讹拷锟斤拷锟斤拷锟斤拷直锟接诧拷询锟叫讹拷锟斤拷锟斤拷 */
		if(CH376_INT_WIRE) return FALSE ;
		else{
			//xReadCH376Data();               //锟斤拷锟斤拷锟叫断碉拷同时锟斤拷锟斤拷锟节伙拷锟秸碉拷一锟斤拷锟斤拷锟捷ｏ拷直锟接讹拷锟斤拷锟斤拷锟斤拷锟斤拷
			return TRUE ;
		}
	#else
		/* Use HAL UART flag to check if data is available on huart2.
		   Older/newer STM32 families use different register names (SR vs ISR),
		   so prefer the HAL macro which is portable across families. */
		if (__HAL_UART_GET_FLAG(&huart2, UART_FLAG_RXNE)) {
			return( TRUE );
		} else {
			return( FALSE );
		}
	#endif	
}

uint8_t file_writeData(char * buf)
{
	uint8_t s;
	uint32_t timeout_count = 0;
	const uint32_t MAX_TIMEOUT = 10000000; // 超时计数（约10秒）
	
	xWriteCH376Cmd(CMD2H_BYTE_WRITE);
	xWriteCH376Data(strlen(buf)%256);
	xWriteCH376Data(strlen(buf)>>8);

	while(1)
	{
		// 超时检测
		timeout_count++;
		if(timeout_count > MAX_TIMEOUT) {
			printf("写入超时\xff\xff\xff");
			return ERR_USB_UNKNOWN; // 返回错误码
		}
		
		s = xReadCH376Data();
		
		if ( s == USB_INT_DISK_WRITE ) {
			s = CH376WriteReqBlock( (PUINT8)buf );
			xWriteCH376Cmd( CMD0H_BYTE_WR_GO );
			xEndCH376Cmd( );
			buf += s;
			timeout_count = 0; // 重置超时计数
		}
		else if ( s == USB_INT_SUCCESS ) return(s);
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
	//选锟斤拷u锟斤拷模式
	printf("锟斤拷锟斤拷选锟斤拷u锟斤拷模式...\xff\xff\xff");
	xWriteCH376Cmd(CMD_SET_USB_MODE);
	xWriteCH376Data(0x06);
		if(xReadCH376Data()==0x51)
		{
			if(xReadCH376Data()==0x15)
			{
				
				printf("t2.txt=\"导出失败\"\xff\xff\xff");
			}
			else{init_flag=0;}
		}	
//		else{init_flag=0;}
	//锟叫讹拷锟角凤拷锟斤拷锟斤拷
//	printf("锟斤拷锟节硷拷锟絬锟斤拷锟斤拷锟斤拷...\xff\xff\xff");
	CH376DiskConnect();
	if(xReadCH376Data()==USB_INT_SUCCESS) 
	{
	//	printf("锟斤拷锟接成癸拷\xff\xff\xff");
	}
	else {}
	//锟斤拷始锟斤拷锟斤拷锟斤拷
//	printf("锟斤拷锟节筹拷始锟斤拷锟斤拷锟斤拷\xff\xff\xff");
	if(CH376DiskMount()==USB_INT_SUCCESS) 
	{
//		printf("锟窖撅拷锟斤拷\xff\xff\xff");
	}
	else {

	}
}

void ch376_writetest()
{
	//锟斤拷目录
	char str[200];
	uint32_t size;
	uint8_t result;
		
	// 锟斤拷始锟斤拷锟斤拷锟斤拷锟斤拷为0%
	printf("j0.val=0\xff\xff\xff");
	printf("开始导出数据...\xff\xff\xff");
	
	// 使锟矫固讹拷锟侥硷拷锟斤拷
	strcpy(str, "/DATA.CSV");
	result = CH376FileCreate((PUINT8)str);
	if(result == USB_INT_SUCCESS) {
		printf("open\xff\xff\xff");
	} else {
		printf("锟侥硷拷锟斤拷锟斤拷失锟斤拷(0x%02X)\xff\xff\xff", result);
		printf("锟斤拷锟斤拷U锟斤拷锟角凤拷锟斤拷锟絓xff\xff\xff");
		output_flag = 0;
		return; // 导出失败
	}
	//获取文件大小
	size=CH376GetFileSize();
	printf("size=%d\r\n",(int)size);
	
	// 使用统一的头格式
	result = file_writeData("像素位,波长(nm),光强度灰值\n");
	if(result == USB_INT_SUCCESS) {
		printf("open2\xff\xff\xff");
	} else {
		printf("false2\xff\xff\xff");
		CH376FileClose(1);
		output_flag = 0;
		return; // 锟斤拷前锟斤拷锟斤拷
	}

	// 锟斤拷取锟斤拷锟斤拷锟斤拷锟斤拷指锟斤拷 - 目前只锟斤拷一锟斤拷锟斤拷锟斤拷spectrum_data_ram[0]
	uint8_t* source_data = spectrum_data_ram[0];
	
	//锟斤拷锟斤拷写锟斤拷锟斤拷锟捷ｏ拷锟斤拷锟斤拷锟斤拷锟斤拷3648锟斤拷锟斤拷锟捷碉拷
	for(int i=0; i<3648; i++)
	{
		// 锟斤拷16锟斤拷锟斤拷强锟斤拷值(0x00-0xFF)转锟斤拷为0-60000锟斤拷围
		uint16_t intensity = (uint16_t)((uint32_t)source_data[i] * 60000 / 255);
		
		if(saved_calib_params.is_valid) {
			// 锟叫标定锟斤拷锟斤拷锟斤拷锟斤拷锟姐波锟斤拷值锟斤拷写锟斤拷
			float wavelength = saved_calib_params.k * (float)i + saved_calib_params.b;
			sprintf(str,"%d,%.2f,%d\n", i+1, wavelength, intensity);
		} else {
			// 没锟叫标定锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷写锟斤拷0
			sprintf(str,"%d,0,%d\n", i+1, intensity);
		}
		result = file_writeData(str);
		if(result == USB_INT_SUCCESS) {
			// 锟斤拷锟斤拷锟斤拷劝俜直锟? (0-100)
			int progress = (i * 100) / 3648;
			
			// 每10锟叫革拷锟斤拷一锟轿斤拷锟斤拷锟斤拷锟酵斤拷锟斤拷锟斤拷示
			if(i % 10 == 0) {
				printf("j0.val=%d\xff\xff\xff", progress);
				printf("导出进度:%d%% (%d/3648)\xff\xff\xff", progress, i);
			}
		}
		else {
			printf("导出失败\xff\xff\xff", i+1);
			CH376FileClose(1);
			output_flag=0;
			return;
		}
	}
	
	size=CH376GetFileSize();
	printf("filesize=%d\xff\xff\xff",(int)size);
	printf("123123\xff\xff\xff");
	
	if(CH376FileClose(1)==USB_INT_SUCCESS){ 
		// 锟斤拷锟斤拷锟缴癸拷锟斤拷锟斤拷锟矫斤拷锟斤拷锟斤拷为100%
		printf("j0.val=100\xff\xff\xff");
		printf("导出完成！\xff\xff\xff");

		output_flag=1;
	}
	else {
		printf("j0.val=0\xff\xff\xff");  // 导出失败
		printf("导出失败\xff\xff\xff");
		output_flag=0;
	}
}
					
// 锟斤拷锟斤拷CH376锟斤拷锟斤拷锟斤拷为115200


// 锟斤拷锟斤拷锟斤拷锟斤拷锟叫伙拷锟斤拷CH376锟斤拷始锟斤拷锟斤拷锟斤拷
// 锟斤拷锟斤拷值: 1=锟缴癸拷, 0=失锟斤拷
uint8_t ch376_init_with_baudrate_change(void)
{
	uint8_t result;

	printf( "锟斤拷锟节筹拷始锟斤拷CH376...\xff\xff\xff" );
	
	// 锟斤拷锟斤拷使锟斤拷9600锟斤拷锟斤拷锟绞诧拷锟斤拷锟斤拷锟斤拷
	if (CH376_TestConnection()) {
		printf("CH376锟斤拷锟接成癸拷\xff\xff\xff");
	} else {
		printf("CH376锟斤拷锟斤拷失锟斤拷\xff\xff\xff");
		printf("锟斤拷锟斤拷硬锟斤拷锟斤拷锟斤拷\xff\xff\xff");
		return 0;
	}

	xWriteCH376Cmd(CMD_SET_USB_MODE);
	xWriteCH376Data(0x06);
	
	// 锟斤拷锟接筹拷时锟斤拷锟?
	uint32_t timeout = 0;
	uint8_t response1 = 0, response2 = 0;
	
	// 锟斤拷取锟斤拷一锟斤拷锟斤拷应
	while(timeout < 1000000) {
		if(__HAL_UART_GET_FLAG(&huart2, UART_FLAG_RXNE)) {
			response1 = xReadCH376Data();
			break;
		}
		timeout++;
	}
	
	if(timeout >= 1000000 || response1 != 0x51) {
		printf("USB模式锟斤拷锟斤拷失锟斤拷\xff\xff\xff");
		return 0;
	}
	
	// 锟斤拷取锟节讹拷锟斤拷锟斤拷应
	timeout = 0;
	while(timeout < 1000000) {
		if(__HAL_UART_GET_FLAG(&huart2, UART_FLAG_RXNE)) {
			response2 = xReadCH376Data();
			break;
		}
		timeout++;
	}
	
	if(timeout >= 1000000 || response2 != 0x15) {
		printf("USB模式锟斤拷锟斤拷失锟斤拷\xff\xff\xff");
		return 0;
	}
	
	printf("USB模式锟斤拷锟矫成癸拷\xff\xff\xff");

	// 锟斤拷锟斤拷锟斤拷锟斤拷锟斤拷
	CH376DiskConnect();
	
	timeout = 0;
	uint8_t connect_status = 0;
	while(timeout < 1000000) {
		if(__HAL_UART_GET_FLAG(&huart2, UART_FLAG_RXNE)) {
			connect_status = xReadCH376Data();
			break;
		}
		timeout++;
	}
	
	if(timeout >= 1000000) {
		printf("未锟斤拷獾経锟斤拷\xff\xff\xff");
		printf("锟斤拷锟斤拷锟経锟教猴拷锟斤拷锟斤拷\xff\xff\xff");
		return 0;
	}
	
	if(connect_status != USB_INT_SUCCESS) {
		printf("U锟斤拷锟斤拷锟斤拷失锟斤拷(0x%02X)\xff\xff\xff", connect_status);
		printf("锟斤拷锟斤拷锟铰诧拷锟斤拷U锟斤拷\xff\xff\xff");
		return 0;
	}
	
	printf("U锟斤拷锟斤拷锟接成癸拷\xff\xff\xff");

	// 锟斤拷锟截达拷锟斤拷
	result = CH376DiskMount();
	if(result == USB_INT_SUCCESS) {
		printf("U锟教癸拷锟截成癸拷\xff\xff\xff");
		return 1; // 锟缴癸拷
	} else {
		printf("U锟教癸拷锟斤拷失锟斤拷(0x%02X)\xff\xff\xff", result);
		printf("锟斤拷锟斤拷U锟教革拷式\xff\xff\xff");
		return 0;
	}
}

// 读取CALIBO文件中的标定系数
uint8_t ch376_read_calibration(void)
{
    char filename[] = "/CALIBO.TXT";
    uint8_t result;
    uint32_t file_size;
    char buffer[100]; // 用于存储读取的数据
    uint32_t bytes_to_read;
    uint32_t total_read = 0;
    
    printf("开始读取标定文件...\xff\xff\xff");
    
    // 打开文件
    if(CH376FileOpen((PUINT8)filename) == USB_INT_SUCCESS) {
        printf("文件打开成功\xff\xff\xff");
        
        // 获取文件大小
        file_size = CH376GetFileSize();
        printf("文件大小: %d 字节\r\n", (int)file_size);
        
        if(file_size > 0 && file_size < sizeof(buffer)) {
            // 读取文件内容
            bytes_to_read = file_size;
            
            // 设置读取字节数
            xWriteCH376Cmd(CMD2H_BYTE_READ);
            xWriteCH376Data(bytes_to_read & 0xFF);
            xWriteCH376Data((bytes_to_read >> 8) & 0xFF);
            
            // 等待读取完成 - 添加超时保护
            uint32_t timeout_count = 0;
            const uint32_t MAX_TIMEOUT = 5000000; // 超时计数（约5秒）
            
            while(1) {
                // 超时检测
                timeout_count++;
                if(timeout_count > MAX_TIMEOUT) {
                    printf("读取超时\xff\xff\xff");
                    CH376FileClose(1);
                    return 0;
                }
                
                result = xReadCH376Data();
                
                if(result == USB_INT_DISK_READ) {
                    // 读取数据
					result = CH376ReadBlock((PUINT8)&buffer[total_read]);
                    total_read += result;
                    timeout_count = 0; // 重置超时计数
                    
                    if(total_read >= file_size) {
                        break; // 读取完成
                    }
                    
                    // 继续读取
                    xWriteCH376Cmd(CMD0H_BYTE_RD_GO);
                    xEndCH376Cmd();
                } else if(result == USB_INT_SUCCESS) {
                    break; // 读取完成
                } else {
                    printf("读取错误: %02X\r\n", result);
                    CH376FileClose(1);
                    return 0;
                }
            }
           
            
            // 确锟斤拷锟街凤拷锟斤拷锟斤拷锟斤拷
            buffer[total_read] = '\0';
            
            // 锟斤拷锟斤拷锟疥定系锟斤拷 (锟斤拷锟斤拷锟侥硷拷锟斤拷式为: k=值,b=值,r2=值)
            char *k_pos = strstr(buffer, "k=");
            char *b_pos = strstr(buffer, "b=");
            char *r2_pos = strstr(buffer, "r2=");
            
            if(k_pos && b_pos && r2_pos) {
                // 锟斤拷锟斤拷k值
                float k_val = atof(k_pos + 2);
                
                // 锟斤拷锟斤拷b值  
                float b_val = atof(b_pos + 2);
                
                // 锟斤拷锟斤拷r2值
                float r2_val = atof(r2_pos + 3);
                
                // 锟斤拷锟斤拷锟解部锟疥定锟斤拷锟斤拷
                extern CalibrationParams saved_calib_params;
                saved_calib_params.k = k_val;
                saved_calib_params.b = b_val;
                saved_calib_params.r_squared = r2_val;
                saved_calib_params.is_valid = 1;
                
                printf("标定系数读取成功\xff\xff\xff");
                printf("k=%.6f, b=%.2f, r2=%.4f\r\n", k_val, b_val, r2_val);
                
                // 锟截憋拷锟侥硷拷
                CH376FileClose(1);
                return 1; // 锟缴癸拷
            } else {
				printf("文件格式错误\xff\xff\xff");
                CH376FileClose(1);
                return 0;
            }
        } else {
			printf("文件大小异常\xff\xff\xff");
            CH376FileClose(1);
            return 0;
        }
    } else {
		printf("文件打开失败\xff\xff\xff");
        return 0;
    }
}

// 锟斤拷锟斤拷锟疥定系锟斤拷锟斤拷CALIBO.TXT锟侥硷拷
uint8_t ch376_export_calibration(void)
{
    char filename[] = "/CALIBO.TXT";
    char buffer[200]; // 锟斤拷锟节存储要写锟斤拷锟斤拷锟斤拷锟?
    uint8_t result;
    
    printf("开始导出标定系数...\xff\xff\xff");
    
    // 锟斤拷锟疥定锟斤拷锟斤拷锟角凤拷锟斤拷效
    if(!saved_calib_params.is_valid) {
		printf("标定参数无效\xff\xff\xff");
        return 0;
    }
    
    // 锟斤拷式锟斤拷锟疥定系锟斤拷锟斤拷锟斤拷
    sprintf(buffer, "k=%.6f,b=%.2f,r2=%.4f\n", 
            saved_calib_params.k, 
            saved_calib_params.b, 
            saved_calib_params.r_squared);
    
    // 锟斤拷锟斤拷锟侥硷拷锟斤拷锟斤拷锟斤拷募锟斤拷锟斤拷诨岜伙拷锟斤拷牵锟?
    result = CH376FileCreate((PUINT8)filename);
    if(result == USB_INT_SUCCESS) {
        printf("锟侥硷拷锟斤拷锟斤拷锟缴癸拷\xff\xff\xff");
        
        // 写锟斤拷甓ㄏ碉拷锟斤拷锟斤拷锟?
        result = file_writeData(buffer);
        if(result == USB_INT_SUCCESS) {
            printf("锟斤拷锟斤拷写锟斤拷晒锟絓xff\xff\xff");
            
            // 锟截憋拷锟侥硷拷
            result = CH376FileClose(1);
            if(result == USB_INT_SUCCESS) {
                printf("锟疥定系锟斤拷锟斤拷锟斤拷锟斤拷桑锟絓xff\xff\xff");
                return 1; // 锟缴癸拷
            } else {
                printf("锟侥硷拷锟截憋拷失锟斤拷(0x%02X)\xff\xff\xff", result);
                return 0;
            }
        } else {
            printf("锟斤拷锟斤拷写锟斤拷失锟斤拷(0x%02X)\xff\xff\xff", result);
            CH376FileClose(1);
            return 0;
        }
    } else {
        printf("锟侥硷拷锟斤拷锟斤拷失锟斤拷(0x%02X)\xff\xff\xff", result);
        printf("锟斤拷锟斤拷U锟斤拷锟角凤拷锟斤拷锟絓xff\xff\xff");
        return 0;
    }
}


