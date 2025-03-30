from flask import Flask, render_template, request, jsonify
import requests
import re
from time import sleep

app = Flask(__name__)

# Constants
url_template = "https://postings.speechwire.com/r-uil-academics.php?"
competitions = {
    1: "Accounting", 8: "Calculator", 2: "Comp Apps", 
    9: "CS", 3: "Current Events", 10: "Math", 11: "Number Sense",
    12: "Science", 7: "Spelling", 4: "Lit Crit", 6: "Social Studies"
}

def req(dist="", reg="", state="", comp="", conf=""):
    inp = f"{url_template}groupingid={comp}&Submit=View+Postings&region={reg}&district={dist}&state={state}&conference={conf}&seasonid={year}"
    return requests.get(inp).content.decode()

def district_parser(reg_number):
    indiv_results = []
    team_results = []
    mxbio, mxchem, mxphys = dict(), dict(), dict()
    
    for i in range(reg_number * 8 - 7, reg_number * 8 + 1):
        try:
            scrape = req(dist=str(i), comp=str(subj), conf=conf)
            tmp = ("0" if i < 10 else "") + str(i)
            regex = f"<tr>.*?{tmp}-{conf}A.*?</tr>"
            indiv_places = re.findall(regex, scrape)
            
            if len(indiv_places) == 0:
                indiv_places = re.findall("<tr>.*?HS.*?</tr>", scrape)
            if len(indiv_places) == 0:
                print(f"NOTHING IN DISTRICT {i}, continuing...")
                continue
                
            for x in indiv_places:
                values = re.findall("<td class='ddprint centered'>(.*?)</td>", x)
                place = values[0]
                school = values[1]
                name = values[2].strip()
                score = values[-3 if subj % 10 == 1 else -4]
                try:
                    score = int(score)
                except:
                    score = float(score)
                tup = (score, place, name, school, f"District {i}")
                
                if subj == 12:
                    bio, chem, phys = int(values[4]), int(values[5]), int(values[6])
                    tup = (score, place, name, school, f"District {i}", bio, chem, phys)
                    if i in mxbio: mxbio[i] = max(mxbio[i], bio)
                    else: mxbio[i] = bio
                    if i in mxchem: mxchem[i] = max(mxchem[i], chem)
                    else: mxchem[i] = chem
                    if i in mxphys: mxphys[i] = max(mxphys[i], phys)
                    else: mxphys[i] = phys
                indiv_results.append(tup)

            regex = "<tr>(.*?)</tr>"
            team_places = re.findall(regex, scrape)
            for idx in range(len(indiv_places), len(team_places)):
                x = team_places[idx]
                place = re.search(r"<td class='ddprint centered'>(.*?)<\/td>", x).group(1)
                school = re.search(r"<td class='ddprint centered'>(.*?)<span", x).group(1)
                school = school[school.rindex('>')+1:]
                regex = r"<td class='ddprint centered'>(\d+)<\/td>"
                score, prog_score = 0, 0
                
                if comp == "CS":
                    score = re.search(regex * 2, x).group(2)
                    prog_score = re.search(regex, x).group(1)
                else:
                    score = re.search(regex, x).group(1)
                names = [(N if '<' not in N else N[:N.index('<')]).strip() for N in x.split("<br>")[1:]]
                team_results.append((int(score), place, school, f"District {i}", names, prog_score))
                
        except Exception as e:
            print(f"Error processing district {i}: {str(e)}")
            continue
            
        print(f"Finished District {i}")
        sleep(0.25)

    indiv_results.sort(reverse=True)
    team_results.sort(reverse=True)
    
    # Filter team results to only advancing teams
    tmp, found = [], False
    for x in team_results:
        if x[1] == "1st":
            tmp.append(x)
        elif x[1] == "2nd" and not found:
            tmp.append(x)
            found = True 
    team_results = tmp
    
    # Filter individual results to only advancing individuals
    tmp = []
    for x in indiv_results:
        found = False
        for team in team_results:
            found |= (x[2] in team[4])
        if subj == 12:
            b = (mxbio[int(x[4][9:])] == x[-3])
            c = (mxchem[int(x[4][9:])] == x[-2])
            p = (mxphys[int(x[4][9:])] == x[-1])
            found |= (b or c or p)
        if x[1] == '1st' or x[1] == '2nd' or x[1] == '3rd' or found:
            tmp.append(x)
    indiv_results = tmp

    return indiv_results, team_results

def regional_parser():
    indiv_results = []
    team_results = []
    mxbio, mxchem, mxphys = dict(), dict(), dict()
    
    for i in range(1, 5):
        try:
            scrape = req(reg=str(i), comp=str(subj), conf=conf)
            regex = f"<tr>.*?{conf}A.*?</tr>"
            indiv_places = re.findall(regex, scrape)
            
            if len(indiv_places) == 0:
                indiv_places = re.findall("<tr>.*?HS.*?</tr>", scrape)
            if len(indiv_places) == 0:
                print(f"NOTHING IN REGION {i}, continuing...")
                continue
                
            for x in indiv_places:
                values = re.findall("<td class='ddprint centered'>(.*?)</td>", x)
                place = values[0]
                school = values[1]
                name = values[2].strip()
                score = values[-3 if subj % 10 == 1 else -4]
                try:
                    score = int(score)
                except:
                    score = float(score)
                tup = (score, place, name, school, f"Region {i}")
                
                if subj == 12:
                    bio, chem, phys = int(values[4]), int(values[5]), int(values[6])
                    tup = (score, place, name, school, f"Region {i}", bio, chem, phys)
                    if i in mxbio: mxbio[i] = max(mxbio[i], bio)
                    else: mxbio[i] = bio
                    if i in mxchem: mxchem[i] = max(mxchem[i], chem)
                    else: mxchem[i] = chem
                    if i in mxphys: mxphys[i] = max(mxphys[i], phys)
                    else: mxphys[i] = phys
                indiv_results.append(tup)

            regex = "<tr>(.*?)</tr>"
            team_places = re.findall(regex, scrape)
            for idx in range(len(indiv_places), len(team_places)):
                x = team_places[idx]
                place = re.search(r"<td class='ddprint centered'>(.*?)<\/td>", x).group(1)
                school = re.search(r"<td class='ddprint centered'>(.*?)<span", x).group(1)
                school = school[school.rindex('>')+1:]
                regex = r"<td class='ddprint centered'>(\d+)<\/td>"
                score, prog_score = 0, 0
                
                if comp == "CS":
                    score = re.search(regex * 2, x).group(2)
                    prog_score = re.search(regex, x).group(1)
                else:
                    score = re.search(regex, x).group(1)
                names = [(N if '<' not in N else N[:N.index('<')]).strip() for N in x.split("<br>")[1:]]
                team_results.append((int(score), place, school, f"Region {i}", names, prog_score))
                
        except Exception as e:
            print(f"Error processing region {i}: {str(e)}")
            continue
            
        print(f"Finished Region {i}")
        sleep(0.25)

    indiv_results.sort(reverse=True)
    team_results.sort(reverse=True)
    
    # Filter team results to only advancing teams
    tmp, found = [], False
    for x in team_results:
        if x[1] == "1st":
            tmp.append(x)
        elif x[1] == "2nd" and not found:
            tmp.append(x)
            found = True 
    team_results = tmp
    
    # Filter individual results to only advancing individuals
    tmp = []
    for x in indiv_results:
        found = False
        for team in team_results:
            found |= (x[2] in team[4])
        if subj == 12:
            b = (mxbio[int(x[4][7:])] == x[-3])
            c = (mxchem[int(x[4][7:])] == x[-2])
            p = (mxphys[int(x[4][7:])] == x[-1])
            found |= (b or c or p)
        if x[1] == '1st' or x[1] == '2nd' or x[1] == '3rd' or found:
            tmp.append(x)
    indiv_results = tmp

    return indiv_results, team_results

@app.route('/')
def index():
    return render_template('index.html', competitions=competitions)

@app.route('/results', methods=['POST'])
def get_results():
    global year, conf, subj, comp
    
    data = request.json
    year = int(data['year']) - 2008
    conf = int(data['conf'])
    subj = int(data['comp'])
    comp = competitions[subj]
    choice = int(data['choice'])
    
    if choice == 1:
        reg_number = int(data['region'])
        indiv_results, team_results = district_parser(reg_number)
    elif choice == 2:
        indiv_results, team_results = [], []
        for r in range(1, 5):
            I, T = district_parser(r)
            indiv_results += I
            team_results += T
        indiv_results.sort(reverse=True)
        team_results.sort(reverse=True)
    else:  # choice == 3
        indiv_results, team_results = regional_parser()
    
    # Format results for JSON response
    formatted_indiv = []
    for res in indiv_results:
        if subj == 12:
            formatted_indiv.append({
                "rank": len(formatted_indiv) + 1,
                "score": int(res[0]),
                "name": res[2],
                "school": res[3],
                "district": res[4],
                "bio": res[-3],
                "chem": res[-2],
                "phys": res[-1]
            })
        else:
            formatted_indiv.append({
                "rank": len(formatted_indiv) + 1,
                "score": int(res[0]),
                "name": res[2],
                "school": res[3],
                "district": res[4]
            })
    
    formatted_team = []
    for res in team_results:
        formatted_team.append({
            "rank": len(formatted_team) + 1,
            "score": res[0],
            "school": res[2],
            "district": res[3],
            "names": res[4],
            "prog_score": res[-1] if comp == "CS" else None
        })
    
    return jsonify({
        "individual": formatted_indiv,
        "team": formatted_team,
        "competition": comp
    })

if __name__ == '__main__':
    app.run(debug=True) 