import os
import cv2
import json
import re
import datetime
import math
import asyncio
import pytesseract
import numpy as np
import urllib.request as rq
from sanic import Sanic
from sanic.response import json
from functools import wraps, partial


class Identity(object):
    def __init__(self):
        self.type = ""
        self.id = ""
        self.name = ""
        self.province = ""
        self.regency = ""
        self.district = ""
        self.village = ""
        self.birthdate = ""
        self.gender = 0
        self.career = ""
        self.marital = ""
        self.religion = ""
        self.nationality = ""


def month_to_number(arg):
    switcher = {
        "JAN": "01",
        "FEB": "02",
        "MAR": "03",
        "APR": "04",
        "MAY": "05",
        "JUN": "06",
        "JUL": "07",
        "AUG": "08",
        "SEP": "09",
        "OCT": "10",
        "NOV": "11",
        "DEC": "12"
    }
    return switcher.get(arg, "Invalid month")


def parse_passport(lines):
    idSearch = re.search(r'([A-Z]{1}[0-9]{7})', lines)
    id = ""
    date = ""
    name = ""
    if idSearch:
        id = idSearch.group(1)

    gender = re.search('P/F|L/M', lines)
    if gender:
        gender = gender.group(0)
        if gender == "L/M":
            gender = 1
        elif gender == "P/F":
            gender = 2
        else:
            gender = 0
    else:
        gender = 0

    nameSearch = re.findall(r'(<[A-Z]+)', lines)
    if nameSearch:
        nameSearch = list(map(lambda x: x.replace("<", " ").replace("IDN", "").strip().split(" ")[0], nameSearch))
        firstName = ""
        lastName = ""
        centerIndex = math.floor(len(nameSearch) / 2)
        if centerIndex > 0:
            if centerIndex % centerIndex == 0:
                if centerIndex > 1:
                    centerIndex = centerIndex - 1
            else:
                centerIndex = centerIndex + 1
        if centerIndex < 0:
            firstName = nameSearch[0]
        else:
            firstName = nameSearch[centerIndex]
        lastName = [nameSearch[x] for x in range(centerIndex + 1, len(nameSearch))]
        if nameSearch[0] is not firstName:
            lastName = lastName + [nameSearch[0]]
        lastName = " ".join(lastName)
        name = firstName + " " + lastName

    dateSearch = re.search(r'([0-9]{2} ([A-z]){3} ([0-9]){4})', lines)
    if dateSearch:
        try:
            date = dateSearch.group().split(" ")
            month = month_to_number(date[1])
            date[1] = month
            date = "-".join(date)
        except:
            print("err parse date")

    lines = lines.split("\n")
    index = 0
    city = ""
    #     for line in lines:
    #         citySearch = re.search(r'(^(?=.*[0-9])(?=.*[a-zA-Z])([a-zA-Z0-9]+)$)', line)
    #         if citySearch:
    #             if city is "":
    #                 city = lines[index-1]

    #         index=index+1

    identity = Identity()
    identity.name = name
    identity.birthdate = date
    identity.regency = city
    identity.id = id
    identity.type = 3
    identity.gender = gender
    return identity


def parse_sim(lines):
    dates = []
    ids = []
    res = []
    idSearch = re.search(r'([0-9]{12,13})', lines.replace(" ", ""))
    if idSearch:
        if lines != "":
            id = idSearch.group(1)
            if id != "":
                ids.append(id)

    gender = re.search('PRIA|WANITA', lines)
    if gender:
        gender = gender.group(0)
        if gender == "PRIA":
            gender = 1
        elif gender == "WANITA":
            gender = 2
        else:
            gender = 0
    else:
        gender = 0

    careers_file = open("data/ktp/career.txt", 'r')
    careers_data = careers_file.read()
    careers_file.close()

    career = re.search(careers_data, lines)
    if career:
        career = career.group(0)
        career = career

    lines = lines.split("\n")
    index = 0
    city = ''
    name = ''
    for line in lines:
        dateSearch = re.search(r'(([0-9]{2}\-[0-9]{2}\-[0-9]{4}))', line)
        if dateSearch:
            if line != "":
                dates.append(dateSearch.group(1))
                continue

        if re.search('nama|alamat|tempat', line, flags=re.IGNORECASE):
            if re.search('tempat', line, flags=re.IGNORECASE):
                city = lines[index - 1]
            line = line.split(":")
            res.append(line[-1].strip())
            if re.search('nama', line[0], flags=re.IGNORECASE):
                name = line[-1].replace("Nama", "")

        index = index + 1

    identity = Identity()
    identity.type = 2

    if len(ids) > 0:
        identity.id = ids[0].strip()

    identity.name = name.strip()
    identity.gender = gender
    identity.career = career
    city = re.sub('kota|ÐšÐžÐ¢Ð|kabupaten|KAB.|KAB', '', city, flags=re.IGNORECASE)
    identity.regency = city.strip()
    if len(dates) > 0:
        try:
            sorteddates = [datetime.datetime.strptime(ts, "%d-%m-%Y") for ts in dates]
            sorteddates.sort()
            date = "{:%d-%m-%Y}".format(sorteddates[0])
            identity.birthdate = date
        except:
            return identity

    return identity


def parse_ktp(lines):
    res = []
    dates = []

    identity = Identity()

    lines = lines.replace("\n\n\n\n\n", "\n").replace("\n\n\n\n", "\n").replace("\n\n\n", "\n").replace("\n\n", "\n")
    provinces_file = open("data/ktp/regions.txt", 'r')
    provinces_data = provinces_file.read()
    provinces_file.close()
    province = re.search(provinces_data, lines)
    if province:
        identity.province = province.group(0)
        lines = re.sub("/|PROVINSI|" + identity.province, "", lines, flags=re.IGNORECASE)
        regencies_file = open("data/ktp/region-" + identity.province.lower().replace(" ", "-") + ".txt", 'r')
    else:
        identity.province = ""
        regencies_file = open("data/ktp/regencies.txt", 'r')

    regencies_data = regencies_file.read()
    regencies_file.close()
    regency = re.search(regencies_data, lines)
    if regency:
        identity.regency = regency.group(0)
        lines = re.sub("/|" + identity.regency, "", lines, flags=re.IGNORECASE)
        districts_file = open(
            "data/ktp/region-" + identity.province.lower().replace(" ", "-") + "-" + identity.regency.lower().replace(
                " ", "-") + ".txt", 'r')
    else:
        identity.regency = ""
        districts_file = open("data/ktp/districts.txt", 'r')

    districts_data = districts_file.read()
    districts_file.close()
    district = re.search(districts_data, lines)
    if district:
        identity.district = district.group(0)
        lines = re.sub("/|Kecamatan|" + identity.district, "", lines, flags=re.IGNORECASE)
        villages_file = open(
            "data/ktp/region-" + identity.province.lower().replace(" ", "-") + "-" + identity.regency.lower().replace(
                " ", "-") + "-" + identity.district.lower().replace(" ", "-") + ".txt", 'r')
    else:
        identity.district = ""
        villages_file = open("data/ktp/villages.txt", 'r')

    villages_data = villages_file.read()
    villages_file.close()
    village = re.search(villages_data, lines)
    if village:
        identity.village = village.group(0)
        lines = re.sub("/|Kei|KeiDesa|Kel/Desa|Kel|Desa|KelDesa|" + identity.village, "", lines, flags=re.IGNORECASE)
        identity.village = village.group(0)
    else:
        identity.village = ""

    gender = re.search('LAKI|PEREMPUAN', lines)
    if gender:
        gender = gender.group(0)
        lines = re.sub("/|Jenis Kelamin|Jenis amin|Kelamin|" + gender, "", lines, flags=re.IGNORECASE)
        if gender == "LAKI":
            identity.gender = 1
        elif gender == "PEREMPUAN":
            identity.gender = 2
        else:
            identity.gender = 0
    else:
        identity.gender = 0

    careers_file = open("data/ktp/career.txt", 'r')
    careers_data = careers_file.read()
    careers_file.close()

    career = re.search(careers_data, lines)
    if career:
        identity.career = career.group(0)
        lines = re.sub("/|Pekerjaan|Pekerjaan |Pekerjaan:|Pekerjaan: |Pekerjaan :| Pekerjaan : |" + identity.career, "",
                       lines, flags=re.IGNORECASE)
    else:
        identity.career = ""

    marital_file = open("data/ktp/maritals.txt", 'r')
    marital_data = marital_file.read()
    marital_file.close()
    marital = re.search(marital_data, lines)
    if marital:
        identity.marital = marital.group(0)
        lines = re.sub(
            "/|Status Perkawinan|Perkawinan|Status Perkawinan:|Status Perkawinan :|Status Perkawinan: | Status Perkawinan : |" + identity.marital,
            "", lines, flags=re.IGNORECASE)
    else:
        identity.marital = ""

    country_file = open("data/ktp/countries.txt", 'r')
    country_data = country_file.read()
    country_file.close()
    country = re.search(country_data, lines)
    if country:
        identity.nationality = country.group(0)
        lines = re.sub(
            "/|Kewarganegaraan|Kewarganegaraan :|Kewarganegaraan:|Kewarganegaraan : |Kewarganegaraan: |" + identity.nationality,
            "", lines, flags=re.IGNORECASE)
    else:
        identity.nationality = ""

    religion = re.search("ISLAM|KRISTEN|KATHOLIK|HINDU|BUDHA|KONGHUCU", lines)
    if religion:
        identity.religion = religion.group(0)
        lines = re.sub("/|Agama|Agama |Agama:|Agama: |Agama :|Agama : |" + identity.religion, "", lines,
                       flags=re.IGNORECASE)
    else:
        identity.career = ""
    ids = []
    idSearch = re.search(r'([0-9lOS:]{16,18})', lines.replace(" ", ""))
    if idSearch:
        if lines != "":
            id = idSearch.group(1)
            id = id.replace("O", "0").replace(":", "").replace("l", "1").replace("C", "0").replace("S", "5").replace(
                "-", "").replace(",", "").replace(".", "")
            if id != "":
                if len(id) == 17:
                    id = id[1::]
                ids.append(id)

    identity.type = 1
    if len(ids) > 0:
        identity.id = ids[0].strip()

        rawBirthdate = [identity.id[x] for x in range(6, 12)]
        birthDay = int(rawBirthdate[0] + rawBirthdate[1])
        birthYear = int(rawBirthdate[4] + rawBirthdate[5])
        if birthDay > 40:
            birthDay = birthDay - 40

        if birthDay < 10:
            birthDay = "0" + str(birthDay)

        if birthYear > 50:
            birthYear = 1900 + birthYear
        else:
            birthYear = 2000 + birthYear

        identity.birthdate = str(birthDay) + "-" + str(rawBirthdate[2]) + str(rawBirthdate[3]) + "-" + str(birthYear)
    else:
        for line in lines:
            dateSearch = re.search(r'(([0-9]{2}\-[0-9]{2}\-[0-9]{4}))', line.replace("O", "0"))
            if dateSearch:
                if line != "":
                    dates.append(dateSearch.group(1))
                    continue
        if len(dates) > 0:
            sorteddates = [datetime.datetime.strptime(ts, "%d-%m-%Y") for ts in dates]
            sorteddates.sort()
            date = "{:%d-%m-%Y}".format(sorteddates[0])
            identity.birthdate = date

    dob = re.search(r'\b(\d{2}-\d{2}-\d{4})', lines)
    if dob:
        identity.birthdate = dob.group()
        tst = " ".join(lines.split(identity.birthdate)[0].replace(",", "").replace("\n", " ").split())
        aa = re.sub(
            "/|:|Berlaku|Hingga|Alamat|Nama |TempatTgl Lahir : |TempatTgl Lahir :|TempatTgl Lahir:|Tempat/Tgl Lahir : |Tempat/Tgl Lahir :|Tempat/Tgl Lahir: |TempatTgi|Lahir| RTRW",
            "", tst, flags=re.IGNORECASE)
        dta = aa.split(" ")[len(aa.split(" ")) - 1]
        lines = re.sub(
            "/|TempatTgl Lahir : |TempatTgl Lahir :|TempatTgl Lahir:|Tempat/Tgl Lahir : |Tempat/Tgl Lahir :|Tempat/Tgl Lahir: |" + identity.birthdate + "|" + dta,
            "", lines, flags=re.IGNORECASE)

    created = re.search(r'\b(\d{2}-\d{2}-\d{4})', lines)
    if created:
        lines = re.sub("/|" + created.group(), "", lines, flags=re.IGNORECASE)

    lines = lines.replace("Nama", "")
    lines = lines.split("\n")
    for line in lines:
        line = re.sub(
            "/|—|NIK 1|Nama 1|Jenis Kelamin 1|-| -| - |- | ,| , |, |:|GolDarah|0|1 | 1 |rt|rw|PROVINSI|TempatTgi|Tgl|Tgi|TempatTg! Lahir|Lahir|Tempat|gol. darah|nik|Pekerjaan|kewarganegaraan|kabupaten|kota|Nama | Nama|status perkawinan|berlaku hingga|alamat|agama|tempat/ tgl lahir|tempat/tgl lahir|jenis kelamin|gol darah|rt/rw|kel|desa|kecamatan|SEUMUR HIDUP|" + careers_data,
            "", line, flags=re.IGNORECASE)
        line = line.replace(":", "").strip()
        if line != "":
            res.append(line)

    if not res[0].isnumeric():
        res.pop(0)
    print(res)
    identity.name = res[1]
    return identity


def async_wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run


def to_json(object):
    return object.__dict__


def validateInvalidCharacter(text):
    if re.search('\n|:|/|NIK|Alamat|Agama|Provinsi|-', text, flags=re.IGNORECASE):
        return ""
    return text


def validateCity(text):
    if re.search(r'[0-9]', text):
        return ""
    return text


def validateResponse(response):
    response.name = validateInvalidCharacter(response.name)
    response.regency = validateCity(response.regency)
    return response


@async_wrap
def detect_text(path):
    result = Identity()
    try:
        img = cv2.imread(path)
        height, width = img.shape[:2]
        img = cv2.resize(img, (1024, int((height * 1024) / width)))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        th, threshed = cv2.threshold(gray, 127, 255, cv2.THRESH_TRUNC)
        lines = pytesseract.image_to_string((threshed), lang="ind")
        if re.search("paspor|passport", lines, flags=re.IGNORECASE):
            result = parse_passport(lines)
        elif re.search("kepolisian|surat izin mengemudi|surat izin", lines, flags=re.IGNORECASE):
            result = parse_sim(lines)
        elif re.search("provinsi daerah|nik|provinsi|", lines, flags=re.IGNORECASE):
            result = parse_ktp(lines)
        return to_json(validateResponse(result))
    except:
        return to_json(result)


@async_wrap
def detect_text_url(url):
    result = Identity()
    try:
        resp = rq.urlopen(url)
        img = np.asarray(bytearray(resp.read()), dtype="uint8")
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)
        height, width = img.shape[:2]
        img = cv2.resize(img, (1024, int((height * 1024) / width)))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        th, threshed = cv2.threshold(gray, 127, 255, cv2.THRESH_TRUNC)
        lines = pytesseract.image_to_string((threshed), lang="ind")
        if re.search("paspor|passport", lines, flags=re.IGNORECASE):
            result = parse_passport(lines)
        elif re.search("kepolisian|surat izin mengemudi|surat izin", lines, flags=re.IGNORECASE):
            result = parse_sim(lines)
        elif re.search("provinsi daerah|nik|provinsi|", lines, flags=re.IGNORECASE):
            result = parse_ktp(lines)
        return to_json(validateResponse(result))
    except:
        return to_json(result)


app = Sanic("ocr")


@app.route("/scan", methods=['POST'])
async def scan(request):
    if request.json is not None:
        values = request.json
        if "path" in values:
            path = values['path']
            data = await detect_text(path)
            return json(data)
    return json({"error": "path is required."})


@app.route("/scan-url", methods=['POST'])
async def scan(request):
    if request.json is not None:
        values = request.json
        if "url" in values:
            url = values['url']
            data = await detect_text_url(url)
            return json(data)
    return json({"error": "url is required."})


def run():
    app.run(host="0.0.0.0", port=int(os.environ['APP_PORT']), access_log=eval(os.environ['APP_ACCESS_LOG']),
            debug=eval(os.environ['APP_DEBUG']), workers=int(os.environ['APP_WORKER']))


if __name__ == "__main__":
    run()
