/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "dac.h"
#include "dma.h"
#include "spi.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "stdio.h"
#include "FILE_SYS.H"
#include "SPI_Init.h"
#include "ch376.h"

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
int fputc(int ch, FILE* file)
{
    HAL_UART_Transmit(&huart1,(uint8_t*)&ch,1,0xffff);
    return ch;
}
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_DAC_Init();
  MX_USART1_UART_Init();
  MX_SPI1_Init();
  MX_USART2_UART_Init();
  /* USER CODE BEGIN 2 */
//	HAL_DAC_Start(&hdac, DAC_CHANNEL_1);
//	HAL_DAC_Start(&hdac, DAC_CHANNEL_2);
//	HAL_DAC_SetValue(&hdac,DAC_CHANNEL_1,DAC_ALIGN_12B_R,4096.00*1.283/3.30);
//	HAL_DAC_SetValue(&hdac,DAC_CHANNEL_2,DAC_ALIGN_12B_R,4096.00*3.00/3.30);

	printf( "Start\r\n" );

//	uint8_t rxdata,buf[10];
	if (CH376_TestConnection()) {
     printf("CH376 is connected and working!\r\n");
   } 
	else
	{
     printf("CH376 connection failed!\r\n");
  }
	//选择u盘模式
	printf("正在选择u盘模式...");
	xWriteCH376Cmd(CMD_SET_USB_MODE);
	xWriteCH376Data(0x06);
		if(xReadCH376Data()==0x51)if(xReadCH376Data()==0x15) printf("设置成功\r\n");
	//判断是否连接
	printf("正在检查u盘连接...");
	CH376DiskConnect();
	if(xReadCH376Data()==USB_INT_SUCCESS) printf("连接成功\r\n");
	//初始化磁盘
	printf("正在初始化磁盘...");
	if(CH376DiskMount()==USB_INT_SUCCESS) printf("已就绪\r\n");
	//打开目录
	printf("正在打开目录...");
	if(CH376FileCreate((PUINT8)"/DATA.CSV")==USB_INT_SUCCESS) printf("打开成功\r\n");
	else printf("开启失败\r\n");
	//获取当前文件大小
	uint32_t size=CH376GetFileSize();
	printf("size=%d\r\n",size);
	//读取数据
//	xWriteCH376Cmd(CMD2H_BYTE_READ);
//	printf("res=%c",xReadCH376Data());
//	if(xReadCH376Data()==0x1D) printf("正在读取数据...");
//	xWriteCH376Cmd(CMD01_RD_USB_DATA0);
//	printf("读取数据：%x",xReadCH376Data());
	
	//写入数据1
	char str[50];
	float num=123.456;
	sprintf(str,"%.1f",num);
	if(file_writeData("abcd,")==USB_INT_SUCCESS) printf("写入成功\r\n");
	else printf("写入失败\r\n");
	
	//写入数据2
	num=234.6;
	sprintf(str,"%.1f\n",num);
	if(file_writeData(str)==USB_INT_SUCCESS) printf("写入成功\r\n");
	else printf("写入失败\r\n");
//	
	//写入数据3
	num=456.6;
	sprintf(str,"%.1f",num);
	if(file_writeData(str)==USB_INT_SUCCESS) printf("写入成功\r\n");
	else printf("写入失败\r\n");
	
	size=CH376GetFileSize();
	printf("filesize=%d\r\n",size);
	//关闭文件
	printf("正在关闭文件\r\n");
	
	if(CH376FileClose(1)==USB_INT_SUCCESS) printf("关闭成功\r\n");
	
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL2;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV2;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
