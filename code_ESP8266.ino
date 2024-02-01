#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>

#define SEALEVELPRESSURE_HPA (1013.25)

Adafruit_BME280 bme;

const char* ssid = "Alexandre's Galaxy S21 5G";
const char* password = "MMMMMMMM";

void setup() {
  Serial.begin(9600);
  Serial.println("Setup started...");

  // Configuration des broches pour le bus I2C
  Wire.pins(0,2);
  Wire.begin();

  // Connexion Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }

  Serial.println("Connected to WiFi");

  // Utilisation de la fonction getFreeHeap pour afficher la mémoire disponible
  Serial.print("Free Heap: ");
  Serial.println(ESP.getFreeHeap());

  // Initialisation du capteur BME280
  bool status = bme.begin(0x76);
  if (!status) {
    Serial.println("Could not detect a BME280 sensor. Check wiring connections!");
  }

  Serial.println("BME280 detected!");
  Serial.println("Setup completed...");
}

void loop() {
  Serial.println("WEATHER");
  Serial.println();

  // Lecture des valeurs de température, pression et humidité à partir du capteur BME280
  float temperature = bme.readTemperature();
  float pressure = bme.readPressure() / 100.0F;  // Conversion de pascals à hectopascals
  float humidity = bme.readHumidity();

  // Affichage des valeurs sur la console série
  Serial.print(temperature);
  Serial.println(" °C");

  Serial.print(pressure);
  Serial.println(" hPa");

  Serial.print(humidity);
  Serial.println(" % hum");

  // Appeler votre fonction sendJson avec les valeurs appropriées
  sendJson(temperature, humidity, pressure);

  // Attendre avant d'envoyer une nouvelle requête
  delay(5000);
}

void sendJson(float temp, float hum, float press) {
  // Créer un document JSON
  DynamicJsonDocument jsonDocument(1024);
  JsonArray dataArray = jsonDocument.createNestedArray("data");
  JsonObject tempObject = dataArray.createNestedObject();
  tempObject["temperature"] = temp;
  JsonObject humObject = dataArray.createNestedObject();
  humObject["humidity"] = hum;
  JsonObject pressObject = dataArray.createNestedObject();
  pressObject["pressure"] = press;

  // Convertir l'objet JSON en chaîne JSON
  String jsonString;
  serializeJson(jsonDocument, jsonString);

  // Vérifier la connexion Wi-Fi
  if (WiFi.status() == WL_CONNECTED) {
    // Envoyer la requête POST au serveur Raspberry Pi
    HTTPClient http;
    WiFiClient client;
    http.begin(client, "http://192.168.170.82:5000/writejson");
    http.addHeader("Content-Type", "application/json");
    int httpResponseCode = http.POST(jsonString);

    // Afficher les résultats de la requête HTTP
    if (httpResponseCode > 0) {
      Serial.print("HTTP Response code: ");
      Serial.println(httpResponseCode);
    } else {
      Serial.print("HTTP Request failed. Error code: ");
      Serial.println(httpResponseCode);
      Serial.println(http.errorToString(httpResponseCode).c_str());
    }

    http.end();
  } else {
    Serial.println("WiFi not connected!");
  }
}
