package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"strings"
)

func main() {

	var province_res []struct {
		NameDagri string `json:"nama_dagri"`
		NameBPS   string `json:"nama_bps"`
		CodeDagri string `json:"kode_dagri"`
		CodeBPS   string `json:"kode_bps"`
	}

	province, _ := http.Get("https://sig.bps.go.id/rest-bridging-dagri/getwilayah?level=provinsi&parent=0")
	json.NewDecoder(province.Body).Decode(&province_res)
	var provinces []string
	var regenciesAll []string
	var districtsAll []string
	var villagesAll []string
	for _, dt1 := range province_res {
		name_province := strings.Replace(strings.Replace(strings.Replace(dt1.NameDagri, "DI ", "DAERAH ISTIMEWA ", -1), "KEP.", "KEPULAUAN", -1), "  ", " ", -1)
		provinces = append(provinces, name_province)
		regency, _ := http.Get(fmt.Sprintf("https://sig.bps.go.id/rest-bridging/getwilayah?level=kabupaten&parent=%s", dt1.CodeBPS))
		var regencies_res []struct {
			NameDagri string `json:"nama_dagri"`
			NameBPS   string `json:"nama_bps"`
			CodeDagri string `json:"kode_dagri"`
			CodeBPS   string `json:"kode_bps"`
		}
		json.NewDecoder(regency.Body).Decode(&regencies_res)
		var regencies []string
		for _, dt2 := range regencies_res {
			name_regency := strings.Replace(strings.Replace(strings.Replace(dt2.NameDagri, "KAB.", "KABUPATEN", -1), "KOTA ADM. ", "", -1), "  ", " ", -1)
			regencies = append(regencies, name_regency)
			regenciesAll = append(regenciesAll, name_regency)
			district, _ := http.Get(fmt.Sprintf("https://sig.bps.go.id/rest-bridging/getwilayah?level=kecamatan&parent=%s", dt2.CodeBPS))
			var districts_res []struct {
				NameDagri string `json:"nama_dagri"`
				NameBPS   string `json:"nama_bps"`
				CodeDagri string `json:"kode_dagri"`
				CodeBPS   string `json:"kode_bps"`
			}
			json.NewDecoder(district.Body).Decode(&districts_res)
			var districts []string
			for _, dt3 := range districts_res {
				name_district := strings.Replace(dt3.NameDagri, "  ", " ", -1)
				districts = append(districts, name_district)
				districtsAll = append(districtsAll, name_district)
				village, _ := http.Get(fmt.Sprintf("https://sig.bps.go.id/rest-bridging/getwilayah?level=desa&parent=%s", dt3.CodeBPS))
				var vilages_res []struct {
					NameDagri string `json:"nama_dagri"`
					NameBPS   string `json:"nama_bps"`
					CodeDagri string `json:"kode_dagri"`
					CodeBPS   string `json:"kode_bps"`
				}
				json.NewDecoder(village.Body).Decode(&vilages_res)
				var villages []string
				for _, dt4 := range vilages_res {
					name_villages := strings.Replace(dt4.NameDagri, "  ", " ", -1)
					villages = append(villages, name_villages)
					villagesAll = append(villagesAll, name_villages)
				}
				fmt.Println(fmt.Sprintf("%s | %s | %s", dt1.NameDagri, dt2.NameDagri, dt3.NameDagri))
				ioutil.WriteFile(fmt.Sprintf("region-%s-%s-%s.txt", strings.Replace(strings.ToLower(name_province), " ", "-", -1), strings.Replace(strings.ToLower(name_regency), " ", "-", -1), strings.Replace(strings.ToLower(name_district), " ", "-", -1)), []byte(strings.Join(villages[:], "|")), 0755)
			}
			ioutil.WriteFile(fmt.Sprintf("region-%s-%s.txt", strings.Replace(strings.ToLower(name_province), " ", "-", -1), strings.Replace(strings.ToLower(name_regency), " ", "-", -1)), []byte(strings.Join(districts[:], "|")), 0755)
		}
		ioutil.WriteFile(fmt.Sprintf("region-%s.txt", strings.Replace(strings.ToLower(name_province), " ", "-", -1)), []byte(strings.Join(regencies[:], "|")), 0755)
	}
	ioutil.WriteFile("regencies.txt", []byte(strings.Join(regenciesAll[:], "|")), 0755)
	ioutil.WriteFile("districts.txt", []byte(strings.Join(districtsAll[:], "|")), 0755)
	ioutil.WriteFile("villages.txt", []byte(strings.Join(villagesAll[:], "|")), 0755)
	ioutil.WriteFile("regions.txt", []byte(strings.Join(provinces[:], "|")), 0755)
}
