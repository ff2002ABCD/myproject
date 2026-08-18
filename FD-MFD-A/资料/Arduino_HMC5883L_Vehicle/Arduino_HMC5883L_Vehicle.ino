#include <Wire.h>
#include <HMC5883L.h>
 
HMC5883L compass;
 
void setup()
{
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
  // Initialize HMC5883L
  Serial.println("Initialize HMC5883L");
  while (!compass.begin())
  {
    Serial.println("Could not find a valid HMC5883L sensor, check wiring!");
    delay(500);
  }
  
  compass.setRange(HMC5883L_RANGE_1_3GA);
  compass.setMeasurementMode(HMC5883L_CONTINOUS);
  compass.setDataRate(HMC5883L_DATARATE_15HZ);
  compass.setSamples(HMC5883L_SAMPLES_1);
 
  // Check settings
  checkSettings();
}
 
void checkSettings()
{
  Serial.print("Selected range: ");
  
  switch (compass.getRange())
  {
    case HMC5883L_RANGE_0_88GA: Serial.println("0.88 Ga"); break;
    case HMC5883L_RANGE_1_3GA:  Serial.println("1.3 Ga"); break;
    case HMC5883L_RANGE_1_9GA:  Serial.println("1.9 Ga"); break;
    case HMC5883L_RANGE_2_5GA:  Serial.println("2.5 Ga"); break;
    case HMC5883L_RANGE_4GA:    Serial.println("4 Ga"); break;
    case HMC5883L_RANGE_4_7GA:  Serial.println("4.7 Ga"); break;
    case HMC5883L_RANGE_5_6GA:  Serial.println("5.6 Ga"); break;
    case HMC5883L_RANGE_8_1GA:  Serial.println("8.1 Ga"); break;
    default: Serial.println("Bad range!");
  }
  
  Serial.print("Selected Measurement Mode: ");
  switch (compass.getMeasurementMode())
  {  
    case HMC5883L_IDLE: Serial.println("Idle mode"); break;
    case HMC5883L_SINGLE:  Serial.println("Single-Measurement"); break;
    case HMC5883L_CONTINOUS:  Serial.println("Continuous-Measurement"); break;
    default: Serial.println("Bad mode!");
  }
 
  Serial.print("Selected Data Rate: ");
  switch (compass.getDataRate())
  {  
    case HMC5883L_DATARATE_0_75_HZ: Serial.println("0.75 Hz"); break;
    case HMC5883L_DATARATE_1_5HZ:  Serial.println("1.5 Hz"); break;
    case HMC5883L_DATARATE_3HZ:  Serial.println("3 Hz"); break;
    case HMC5883L_DATARATE_7_5HZ: Serial.println("7.5 Hz"); break;
    case HMC5883L_DATARATE_15HZ:  Serial.println("15 Hz"); break;
    case HMC5883L_DATARATE_30HZ: Serial.println("30 Hz"); break;
    case HMC5883L_DATARATE_75HZ:  Serial.println("75 Hz"); break;
    default: Serial.println("Bad data rate!");
  }
  
  Serial.print("Selected number of samples: ");
  switch (compass.getSamples())
  {  
    case HMC5883L_SAMPLES_1: Serial.println("1"); break;
    case HMC5883L_SAMPLES_2: Serial.println("2"); break;
    case HMC5883L_SAMPLES_4: Serial.println("4"); break;
    case HMC5883L_SAMPLES_8: Serial.println("8"); break;
    default: Serial.println("Bad number of samples!");
  }
 
}

int a,b,c,flag=1;
double ans;

void print_data(){
  Vector raw = compass.readRaw();
  Vector norm = compass.readNormalize();
  ans = sqrt(norm.XAxis*norm.XAxis + norm.YAxis*norm.YAxis + norm.ZAxis*norm.ZAxis);
  Serial.print(ans);
  Serial.print(";");
  Serial.print(norm.YAxis);
  Serial.print(",");
  Serial.print(a);
  Serial.print("/");
  Serial.print(b);
  Serial.print(":");
  Serial.print(c);
  Serial.print("|");
  
  //Serial.println();
}

void loop()
{
  Vector raw = compass.readRaw();
  Vector norm = compass.readNormalize();
  ans = sqrt(norm.XAxis*norm.XAxis + norm.YAxis*norm.YAxis + norm.ZAxis*norm.ZAxis);
  
  if (ans>500&&ans<700)
  {
    while(ans>500&&ans<700){
      Vector raw = compass.readRaw();
      Vector norm = compass.readNormalize();
      ans = sqrt(norm.XAxis*norm.XAxis + norm.YAxis*norm.YAxis + norm.ZAxis*norm.ZAxis);
      print_data();
      flag++;
    }
    flag = 0;
      if(flag==0){
        a++;
      }
  }

  if (ans>700&&ans<900)
  {
    while(ans>700&&ans<900){
      Vector raw = compass.readRaw();
      Vector norm = compass.readNormalize();
      ans = sqrt(norm.XAxis*norm.XAxis + norm.YAxis*norm.YAxis + norm.ZAxis*norm.ZAxis);
      print_data();
      flag++;
    }
    flag = 0;
      if(flag==0){
        b++;
      }
  }
  
  if (ans>900)
  {
    while(ans>900){
      Vector raw = compass.readRaw();
      Vector norm = compass.readNormalize();
      ans = sqrt(norm.XAxis*norm.XAxis + norm.YAxis*norm.YAxis + norm.ZAxis*norm.ZAxis);
      print_data();
      flag++;
    }
    flag = 0;
      if(flag==0){
        c++;
      }
  }
  
  print_data();
  digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)       
}
