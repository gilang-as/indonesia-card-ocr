<h1 align="center"  style="margin-bottom: 0px">
  ID CARD EXTRACTOR<br>
</h1>
<h3 align="center" style="margin-top: 0px">INDONESIA</h3>

<div align="center">
    <img src="https://rossrightangle.files.wordpress.com/2012/05/e-ktp-contoh.jpg">
</div>

**ID CARD EXTRACTOR** is a open source python package that attempts to create a production grade ID Card extractor. The aim of the package is to extract as much information as possible yet retain the integrity of the information.

---
<h2 style="font-weight:800;">Requirements</h2>
You will need tesseract with indonesian language support installed in your system. 
- Docker
- Rest API CLient (Postman, Insomnia, stc)
---
<h2 style="font-weight:800;">Support</h2>
* <strong>KTP</strong>
* <strong>SIM</strong> Old or New
* <strong>PASSPORT</strong>
---
<h2 style="font-weight: 800;">How to use</h2>
<h3 style="font-weight: 800;">🚀 Run</h3>
```console
$ git clone https://github.com/gilang-as/id-card-ocr.git
$ cd id-card-ocr
$ docker compose up -d
```
<h3 style="font-weight: 800;">Use</h3>
```shell
# Curl
curl --request POST \
  --url http://localhost:1101/scan-url \
  --header 'Content-Type: application/json' \
  --data '{
	"url": "https://fathanmubiina.id/wp-content/uploads/2017/03/e-ktp-tb-1.jpg"
}'
```
