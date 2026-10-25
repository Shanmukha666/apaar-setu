"""Generate reproducible synthetic seed data. Run: python -m seed.generate_seed"""
import csv, json, random
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent / "data"
HEADER = ["apaar_id","student_ref","name","dob","gender","category","programme_code","academic_year","admission_date","admission_type","nri","oci","fn"]
PROGRAMMES = [(i, f"{code}-{short}", intake) for i, code in enumerate(["DIT001","CCE002","HSM003","MIP004","KPT005"], 1) for short, intake in [("CSE",60),("ECE",90),("MBA",120)]]
PROGRAMMES = [{"id": index + 1, "institution_id": inst, "code": code, "approved_intake": intake, "supernumerary_limit": (intake + 9)//10} for index, (inst, code, intake) in enumerate(PROGRAMMES)]
FIRST = ["Aarav","Diya","Kabir","Meera","Nivaan","Riya","Vihaan","Zoya"]
LAST = ["Demo","Sample","Synthetic","Example","Prototype","Mock"]

def luhn_check_digit(prefix11):
    for digit in range(10):
        value = prefix11 + str(digit); total = sum((int(x)*2-9 if n%2 else int(x)) for n,x in enumerate(reversed(value)))
        if total % 10 == 0: return str(digit)

def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=(["institution_id"] if "institution_id" in rows[0] else []) + HEADER); writer.writeheader(); writer.writerows(rows)

def generate():
    rng=random.Random(2026); ROOT.mkdir(parents=True, exist_ok=True); (ROOT/"demo_uploads").mkdir(exist_ok=True)
    persons=[]
    for n in range(900):
        apaar=f"{10000000000+n:011d}"; apaar+=luhn_check_digit(apaar)
        persons.append({"apaar_id":apaar,"name":f"{FIRST[n%len(FIRST)]} {LAST[(n//len(FIRST))%len(LAST)]}","dob":date(2002+n%6, 1+n%12, 1+n%27).isoformat(),"status":"INACTIVE" if n%33==0 else "ACTIVE"})
    (ROOT/"apaar_registry.json").write_text(json.dumps(persons, indent=2)+"\n", encoding="utf-8")
    (ROOT/"programmes.json").write_text(json.dumps(PROGRAMMES, indent=2)+"\n", encoding="utf-8")
    def row(person, inst, programme, index, year="2026-27"):
        return {"institution_id":str(inst),"apaar_id":person["apaar_id"],"student_ref":f"SYN-{inst}-{index:03d}","name":person["name"],"dob":person["dob"],"gender":"F" if index%2 else "M","category":"GEN","programme_code":programme["code"],"academic_year":year,"admission_date":"2026-06-15","admission_type":"REGULAR","nri":"N","oci":"N","fn":"N"}
    counts=[50,72,96,68,55,55,70,70,63,22,22,21,12,12,12]; rows=[]; cursor=1
    for p, count in zip(PROGRAMMES, counts):
        for j in range(count): rows.append(row(persons[cursor+j],p["institution_id"],p,j))
        cursor+=count
    # Eight institution-3 students deliberately reuse institution-1 identities.
    for j in range(8): rows[396+j]["apaar_id"]=rows[j]["apaar_id"]; rows[396+j]["name"]=rows[j]["name"]; rows[396+j]["dob"]=rows[j]["dob"]
    for r in rows:
        if r["institution_id"]=="4" and int(r["student_ref"].split("-")[-1]) < 8: r.update(nri="Y",oci="Y",fn="Y")
        if r["institution_id"]=="5" and int(r["student_ref"].split("-")[-1]) < 6: r["admission_date"]="2026-06-01"
    write_csv(ROOT/"students_baseline.csv", rows)
    demo=[]
    for n in range(20): demo.append({k:v for k,v in row(persons[700+n],1,PROGRAMMES[0],n,"2027-28").items() if k!="institution_id"})
    write_csv(ROOT/"demo_uploads"/"demo_clean.csv",demo)
    messy=demo[:15]+demo[:15]
    write_csv(ROOT/"demo_uploads"/"demo_messy.csv",messy)
    overflow=[{k:v for k,v in row(persons[750+n],1,PROGRAMMES[0],n,"2027-28").items() if k!="institution_id"} for n in range(65)]
    write_csv(ROOT/"demo_uploads"/"demo_overflow.csv",overflow)
    (ROOT/"demo_uploads"/"EXPECTED.md").write_text("# Expected demo uploads\n\n- `demo_clean.csv`: 20 accepted.\n- `demo_messy.csv`: 30 deterministic synthetic rows.\n- `demo_overflow.csv`: 65 rows; final 5 exceed DIT001-CSE intake.\n",encoding="utf-8")
if __name__=="__main__": generate()
