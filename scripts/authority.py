import lxml.etree as ET
import json
import os
from collections import Counter

# ПУТИ К ВАШИМ ФАЙЛАМ
file_1851 = r"C:\Users\vladimir\Desktop\TEI\govreport-sfu-tei-xml\tei_reports_with_tables_formation\1851_report\1851_final_injected.xml"
file_1828 = r"C:\Users\vladimir\Desktop\TEI\govreport-sfu-tei-xml\tei_reports_with_tables_formation\1828_report\1828_final_marked.xml"

config = [
    {"path": file_1851, "short_name": "1851_report.xml"},
    {"path": file_1828, "short_name": "1828_report.xml"}
]

output_json = r"C:\Users\vladimir\Desktop\entities_authority.json"
ns = {'tei': 'http://www.tei-c.org/ns/1.0', 'xml': 'http://www.w3.org/XML/1998/namespace'}

def get_entity_data():
    results = {
        "persons": [],
        "places": {},
        "organizations": {},
        "metadata": {
            "unique_counts": {"persons": 0, "places": 0, "organizations": 0},
            "source_files": []
        }
    }

    person_seen = {} # Для дедупликации персон

    for item in config:
        if not os.path.exists(item["path"]):
            print(f"Файл не найден: {item['path']}")
            continue

        print(f"Обработка {item['short_name']}...")
        tree = ET.parse(item["path"])
        root = tree.getroot()

        # Собираем статистику упоминаний в body (сколько раз на ID ссылаются)
        all_refs = root.xpath("//tei:body//@ref", namespaces=ns)
        # Чистим рефы от решетки: #place_kras -> place_kras
        usage_counter = Counter([r.replace('#', '') for r in all_refs])

        results["metadata"]["source_files"].append({
            "file": item["short_name"],
            "path": item["path"]
        })

        # --- 1. ПЕРСОНЫ ---
        for p in root.xpath("//tei:listPerson/tei:person", namespaces=ns):
            p_id = p.get('{http://www.w3.org/XML/1998/namespace}id')
            name = "".join(p.find("tei:persName", namespaces=ns).itertext()).strip()
            
            # Считаем упоминания в этом файле
            count_in_file = usage_counter.get(p_id, 0)

            results["persons"].append({
                "id": p_id,
                "name": name,
                "mentions_in_report": count_in_file,
                "source": {
                    "file": item["short_name"],
                    "path": item["path"]
                }
            })

        # --- 2. МЕСТА ---
        for pl in root.xpath("//tei:listPlace/tei:place", namespaces=ns):
            pl_id = pl.get('{http://www.w3.org/XML/1998/namespace}id')
            name = "".join(pl.find("tei:placeName", namespaces=ns).itertext()).strip()
            count_in_file = usage_counter.get(pl_id, 0)

            if name not in results["places"]:
                results["places"][name] = {"name": name, "ids": [], "sources": [], "count": 0}
            
            if pl_id not in results["places"][name]["ids"]:
                results["places"][name]["ids"].append(pl_id)
            
            results["places"][name]["sources"].append({
                "file": item["short_name"],
                "mentions": count_in_file
            })
            results["places"][name]["count"] += count_in_file

        # --- 3. ОРГАНИЗАЦИИ ---
        for org in root.xpath("//tei:listOrg/tei:org", namespaces=ns):
            org_id = org.get('{http://www.w3.org/XML/1998/namespace}id')
            name = "".join(org.find("tei:orgName", namespaces=ns).itertext()).strip()
            count_in_file = usage_counter.get(org_id, 0)

            if name not in results["organizations"]:
                results["organizations"][name] = {"name": name, "ids": [], "sources": [], "count": 0}
            
            if org_id not in results["organizations"][name]["ids"]:
                results["organizations"][name]["ids"].append(org_id)
            
            results["organizations"][name]["sources"].append({
                "file": item["short_name"],
                "mentions": count_in_file
            })
            results["organizations"][name]["count"] += count_in_file

    # Превращаем словари мест и оргов в списки как в примере
    results["places"] = list(results["places"].values())
    results["organizations"] = list(results["organizations"].values())

    # Обновляем финальные счетчики
    results["metadata"]["unique_counts"]["persons"] = len(results["persons"])
    results["metadata"]["unique_counts"]["places"] = len(results["places"])
    results["metadata"]["unique_counts"]["organizations"] = len(results["organizations"])

    return results

def main():
    data = get_entity_data()
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\nГотово! JSON файл создан: {output_json}")

if __name__ == "__main__":
    main()