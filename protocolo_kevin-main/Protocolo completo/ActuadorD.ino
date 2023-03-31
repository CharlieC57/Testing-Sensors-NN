#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <ESP8266WebServer.h>
#include <ESP8266mDNS.h>
#include <ArduinoJson.h>
#include <TypeConversion.h>
#include <Crypto.h>

extern "C"{
#include "sign.h"
};

int ret;

namespace TypeCast = experimental::TypeConversion;

const char* ssid = "Totalplay-F1A4";
const char* password = "F1A4BB1AWMA8xJ5X";


//WiFiServer server(80);
ESP8266WebServer server(80);

const String postForms = "<html>\
  <head>\
    <title>ESP8266 Web Server POST Crypto</title>\
    <style>\
      body { background-color: #cccccc; font-family: Arial, Helvetica, Sans-Serif; Color: #000088; }\
    </style>\
  </head>\
  <body>\
    <h1>POST plain text to /postplain/</h1><br>\
  </body>\
</html>";

void setup() {
  Serial.begin(9600);
  delay(100);

  //Configuración  del GPIO2
  pinMode(2, OUTPUT);
  digitalWrite(2,LOW);
  
  
  Serial.println();
  Serial.println();
  Serial.print("Conectandose a red : ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password); //Conexión a la red
  
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi conectado");

  server.on("/", handleRoot);
  server.on("/hash",set_hash);
  //server.on("/pk",setPk);
  server.begin(); //Iniciamos el servidor

  Serial.println("Servidor Iniciado");


  Serial.println("Ingrese desde un navegador web usando la siguiente IP:");
  Serial.println(WiFi.localIP()); //Obtenemos la IP
}

void loop() {
  
 server.handleClient();
}

/*
void setPk()
{
    if (server.method() != HTTP_POST) {
    //digitalWrite(led, 1);
    server.send(405, "text/plain", "Method Not Allowed");
    //digitalWrite(led, 0);
  } else {
    //digitalWrite(led, 1);
    unsigned char pk[CRYPTO_PUBLICKEYBYTES];
    char pk2[CRYPTO_PUBLICKEYBYTES];
    String pk_r = server.arg(0);
    String sm_r = server.arg(1);
    String m_r = server.arg(2);
    int i = pk_r.length();
    int i2 = sm_r.length();
    int MLEN = m_r.length();
    unsigned char m[MLEN];
    unsigned char sm[MLEN + CRYPTO_BYTES];
    char m2[MLEN];
    char sm2[MLEN + CRYPTO_BYTES];
    //pk_r.toCharArray(pk2,i);
    //sm_r.toCharArray(sm2, i2);
    //m_r.toCharArray(m2, MLEN);
    unsigned long long smlen = i2;
    unsigned long long m_len = MLEN;
    //strcpy((char*)pk,pk2);
    //strcpy((char*)sm,sm2);
    //strcpy((char*)m,m2);
    for (int x= 0; x < i2; x++) {
      sm[x]=sm_r.charAt(x); 
      //Serial.println(pk[x]);
      if(x<i){
         pk[x] = pk_r.charAt(x); 
        }
      //if(x<MLEN){
        //m[x]=m_r.charAt(x);  
        //}
    }

    Serial.println(pk[0]);
    Serial.println(sm[0]);
   // Serial.println(m[0]);
    Serial.println(pk[i-1]);
    Serial.println(sm[i2-1]);
   // Serial.println(m[MLEN-1]);
    int ret;
    ret = crypto_sign_open(m, &m_len, sm, smlen, pk);
    Serial.println("La verificacion es:");
    Serial.println(ret);
    server.send(200, "text/plain", "POST body was:\n" + server.arg("plain"));
    //digitalWrite(led, 0);
  }
}
*/

//Esta funcion se encargara de recibir el hasheo y validarlo
void set_hash(){
  using namespace experimental::crypto;
  uint8_t resultArray[SHA256::NATURAL_LENGTH] { 0 };
  
  if (server.method() != HTTP_POST) {
    //digitalWrite(led, 1);
    server.send(405, "text/plain", "Method Not Allowed");
    //digitalWrite(led, 0);
  } else {
    //digitalWrite(led, 1);
    String mi = server.arg(0);
    String msg_hash = server.arg(1);
    String IDD = "87.65.43.21";
    IDD.concat(mi);
    SHA256::hash(IDD.c_str(), IDD.length(), resultArray);
    String stringOne = (char*)resultArray;
    String stringTwo = stringOne.substring(0,32);
    if (stringTwo.equals(msg_hash)) {
      Serial.println("Son Iguales");
   } else {
      Serial.println("Son Diferentes");
   } 
    server.send(200, "text/plain", "POST body was:\n" + server.arg("plain"));
    //digitalWrite(led, 0);
  }
}

void handleRoot() {
  //digitalWrite(led, 1);
  server.send(200, "text/html", postForms);
  //digitalWrite(led, 0);
}

void handleNotFound() {
  //igitalWrite(led, 1);
  String message = "File Not Found\n\n";
  message += "URI: ";
  message += server.uri();
  message += "\nMethod: ";
  message += (server.method() == HTTP_GET) ? "GET" : "POST";
  message += "\nArguments: ";
  message += server.args();
  message += "\n";

  for (uint8_t i = 0; i < server.args(); i++) {
    message += " " + server.argName(i) + ": " + server.arg(i) + "\n";
  }

  server.send(404, "text/plain", message);
  //digitalWrite(led, 0);
}
