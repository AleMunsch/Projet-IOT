#include <Adafruit_BME280.h>
#include <Adafruit_SSD1306.h>
#include <ArduinoJson.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <Wire.h>

#define PROBE_ID 1
#define READINGS_NUMBER_FOR_AVERAGE 5
#define SCREEN_HEIGHT 64
#define SCREEN_WIDTH 128
#define SEALEVELPRESSURE_HPA (1013.25)

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

Adafruit_BME280 bme;
JsonDocument jsonData;
WiFiClient client;
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 3600);

const char* SSID = "POCOF3";
const char* password = "A08082003a";
int counter = 0;
float temperature = 0;
float totalTemperature = 0;
float averageTemperature = 0;
float pressure = 0;
float totalPressure = 0;
float averagePressure = 0;
float humidity = 0;
float totalHumidity = 0;
float averageHumidity = 0;

void setup() {
  Serial.begin(115200);

  Wire.pins(0,2);
  Wire.begin();

  WiFi.begin(SSID, password);
  Serial.println("Tentative de connection");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected to WiFi");

  timeClient.begin();

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {

    Serial.println(F("SSD1306 allocation failed"));
    for(;;);
  }
  delay(2000);

  bool status;

  status = bme.begin(0x76);  
  if (!status) {

    Serial.println("Could not detect a BME280 sensor, Fix wiring Connections!");
    while (1);
  }

  Serial.println("-- Print BME280 readings--");
  Serial.println();
}

void loop() { 

  timeClient.update();

  String formattedTime = timeClient.getFormattedTime();
  Serial.println("Heure actuelle : " + formattedTime);

  temperature = bme.readTemperature();
  pressure = bme.readPressure() / 100.0F;
  humidity = bme.readHumidity();

  Serial.print("Temperature = ");
  Serial.print(temperature);
  Serial.println(" C");
 
  Serial.print("Pression = ");
  Serial.print(pressure);
  Serial.println(" hPa");

  Serial.print("Humidite = ");
  Serial.print(humidity);
  Serial.println(" %");

  display.clearDisplay();
  display.setCursor(0, 10);
  display.setTextSize(1);
  display.setTextColor(WHITE);

  display.println("METEO");
  display.println();

  display.print("Temp. = ");
  display.print(temperature);
  display.println(" C");

  display.print("Press. = ");
  display.print(pressure);
  display.println(" hPa");

  display.print("Hum. = ");
  display.print(humidity);
  display.println(" %");

  display.display();

  counter++;

  Serial.println(counter);
  Serial.println();

  totalTemperature = totalTemperature + temperature;
  totalPressure = totalPressure + pressure;
  totalHumidity = totalHumidity + humidity;

  if (counter == READINGS_NUMBER_FOR_AVERAGE) {

    averageTemperature = CalculateAverage(totalTemperature);
    averagePressure = CalculateAverage(totalPressure);
    averageHumidity = CalculateAverage(totalHumidity);

    Serial.print("Moyenne temperature = ");
    Serial.print(averageTemperature);
    Serial.println(" C");

    Serial.print("Moyenne pression = ");
    Serial.print(averagePressure);
    Serial.println(" hPa");

    Serial.print("Moyenne humidite = ");
    Serial.print(averageHumidity);
    Serial.println(" %");

    Serial.println();

    if (WiFi.status() == WL_CONNECTED)
    {
      HTTPClient http;
      http.begin(client, "http://192.168.98.230:5000/api/releves");
      http.addHeader("Content-Type", "application/json");
      String jsonPayload = "{\"humidite\": " + String(averageHumidity) + ", \"temperature\": " + String(averageTemperature) + ", \"pression\": " + String(averagePressure) + ", \"date_time\": " + formattedTime + ", \"id_sonde\": " + String(PROBE_ID) + " }";
      int httpCode = http.POST(jsonPayload);
      Serial.println(httpCode);
      Serial.println(jsonPayload);
    }

    counter = 0;
    totalTemperature = 0;
    totalPressure = 0;
    totalHumidity = 0;
  }

  delay(5000);
}

float CalculateAverage (float value) {

    return value / READINGS_NUMBER_FOR_AVERAGE;
}