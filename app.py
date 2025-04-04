from flask import Flask, render_template, request, jsonify, send_file
import requests
import re
from time import sleep
import csv
import io
from datetime import datetime

app = Flask(__name__)

# Constants
url_template = "https://postings.speechwire.com/r-uil-academics.php?"
competitions = {
    1: "Accounting", 8: "Calculator", 
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
    empty_districts = []
    
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
                empty_districts.append(i)
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
                x = team_places[idx].replace('\u00a0', ' ')
                if x.count("<br>") < 2:  # Team rows have multiple <br> tags for member names
                    continue
                    
                try:
                    place = re.search(r"<td class='ddprint centered'>(.*?)<\/td>", x).group(1).strip()
                    school = re.search(r"<td class='ddprint centered'>(.*?)<span", x).group(1).strip()
                    school = school[school.rindex('>')+1:].strip()
                    regex = r"<td class='ddprint centered'>(-?\d+)<\/td>"
                    score, prog_score = 0, 0
                    
                    if comp == "CS":
                        score = re.search(regex * 2, x).group(2)
                        prog_score = re.search(regex, x).group(1)
                    else:
                        score = re.search(regex, x).group(1)
                    names = [(N if '<' not in N else N[:N.index('<')]).strip() for N in x.split("<br>")[1:]]
                    if names:  # Only add if we found team members
                        team_scores = sorted([tup for tup in indiv_results if tup[2] in names], key=lambda tup: tup[0], reverse=True)
                        team_results.append((int(score), prog_score if comp == "CS" else -999, -999 if len(team_scores) <= 3 else team_scores[3][0], place, school, f"District {i}", names))
                        # note the changed order: team score, "prog score", 4th person score, ranking, school, district, people on team
                except Exception as e:
                    print(f"Error processing team row in district {i}: {str(e)}")
                    continue
                
        except Exception as e:
            print(f"Error processing district {i}: {str(e)}")
            continue
            
        print(f"Finished District {i}")
        sleep(0.25)

    # Sort all results
    indiv_results.sort(reverse=True)
    team_results.sort(reverse=True)
    
    # Store all results before filtering
    all_indiv = indiv_results[:]
    all_team = team_results[:]
    
    # Filter team results to only advancing teams
    tmp, second = [], None
    for x in team_results:
        if x[3] == "1st":
            tmp.append(x)
        elif x[3] == "2nd":
            if second == None:
                tmp.append(x)
                second = x
            elif second[0:3] == x[0:3]:
                tmp.append(x) # tie for wildcard, because that's like actually possible
    team_results = tmp
    
    # Filter individual results to only advancing individuals
    tmp = []
    for x in indiv_results:
        found = False
        for team in team_results:
            found |= (x[2] in team[-1])
        if subj == 12:  # Science
            b = (mxbio[int(x[4][9:])] == x[-3])
            c = (mxchem[int(x[4][9:])] == x[-2])
            p = (mxphys[int(x[4][9:])] == x[-1])
            found |= (b or c or p)
        if x[1] in ['1st', '2nd', '3rd'] or found:
            tmp.append(x)
    indiv_results = tmp
    
    return indiv_results, team_results, all_indiv, all_team, empty_districts

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
                # Skip if this doesn't look like a team row (should have multiple <br> tags for team members)
                if x.count("<br>") < 2:  # Team rows have multiple <br> tags for member names
                    continue
                    
                try:
                    place = re.search(r"<td class='ddprint centered'>(.*?)<\/td>", x).group(1).strip()
                    school = re.search(r"<td class='ddprint centered'>(.*?)<span", x).group(1).strip()
                    school = school[school.rindex('>')+1:].strip()
                    regex = r"<td class='ddprint centered'>(-?\d+)<\/td>"
                    score, prog_score = 0, 0
                    
                    if comp == "CS":
                        score = re.search(regex * 2, x).group(2)
                        prog_score = re.search(regex, x).group(1)
                    else:
                        score = re.search(regex, x).group(1)
                    names = [(N if '<' not in N else N[:N.index('<')]).strip() for N in x.split("<br>")[1:]]
                    if names:  # Only add if we found team members
                        team_scores = sorted([tup for tup in indiv_results if tup[2] in names], key=lambda tup: tup[0], reverse=True)
                        team_results.append((int(score), prog_score if comp == "CS" else -999, -999 if len(team_scores) <= 3 else team_scores[3][0], place, school, f"Region {i}", names))
                except Exception as e:
                    print(f"Error processing team row in region {i}: {str(e)}")
                    continue
                
        except Exception as e:
            print(f"Error processing region {i}: {str(e)}")
            continue
            
        print(f"Finished Region {i}")
        sleep(0.25)

    # Sort all results
    indiv_results.sort(reverse=True)
    team_results.sort(reverse=True)
    
    # Store all results before filtering
    all_indiv = indiv_results[:]
    all_team = team_results[:]
    
    # Filter team results to only advancing teams
    tmp, second = [], None
    for x in team_results:
        if x[3] == "1st":
            tmp.append(x)
        elif x[3] == "2nd":
            if second == None:
                tmp.append(x)
                second = x
            elif second[0:3] == x[0:3]:
                tmp.append(x) # tie for wildcard, because that's like actually possible
    team_results = tmp
    
    # Filter individual results to only advancing individuals
    tmp = []
    for x in indiv_results:
        found = False
        for team in team_results:
            found |= (x[2] in team[-1])
        if subj == 12:  # Science
            b = (mxbio[int(x[4][7:])] == x[-3])
            c = (mxchem[int(x[4][7:])] == x[-2])
            p = (mxphys[int(x[4][7:])] == x[-1])
            found |= (b or c or p)
        if x[1] in ['1st', '2nd', '3rd'] or found:
            tmp.append(x)
    indiv_results = tmp

    return indiv_results, team_results, all_indiv, all_team

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
        indiv_results, team_results, all_indiv, all_team, empty_districts = district_parser(reg_number)
    elif choice == 2:
        indiv_results, team_results = [], []
        all_indiv, all_team = [], []
        empty_districts = []
        for r in range(1, 5):
            I, T, AI, AT, E = district_parser(r)
            indiv_results += I
            team_results += T
            all_indiv += AI
            all_team += AT
            empty_districts += E
        indiv_results.sort(reverse=True)
        team_results.sort(reverse=True)
        all_indiv.sort(reverse=True)
        all_team.sort(reverse=True)
    else:  # choice == 3
        indiv_results, team_results, all_indiv, all_team = regional_parser()
        empty_districts = []
    
    # Format results for JSON response
    formatted_indiv = []
    formatted_all_indiv = []
    current_rank = 1
    prev_res = None
    
    # First, format all individual results (for CSV)
    for res in all_indiv:
        # If score is different from previous, update rank
        if prev_res is not None or (prev_res is not None and res[0] != prev_res[0]):
            current_rank = len(formatted_all_indiv) + 1
        prev_res = res
        
        # Check if this result is in the qualifying results
        is_qualified = res in indiv_results
        
        if subj == 12: # score, place, name, school, district, bio, chem, phys
            result_dict = {
                "rank": current_rank,
                "score": int(res[0]),
                "name": res[2],
                "school": res[3],
                "district": res[4],
                "bio": res[-3],
                "chem": res[-2],
                "phys": res[-1],
                "qualified": is_qualified
            }
        else:
            result_dict = {
                "rank": current_rank,
                "score": int(res[0]),
                "name": res[2],
                "school": res[3],
                "district": res[4],
                "qualified": is_qualified
            }
        
        formatted_all_indiv.append(result_dict)
        if is_qualified:
            # Create a copy for the display list, we'll update ranks later
            display_dict = result_dict.copy()
            formatted_indiv.append(display_dict)
    
    # Update ranks for display list to be continuous
    current_rank = 1
    prev_score = None
    for result in formatted_indiv:
        score = result['score']
        if score != prev_score:
            current_rank = len([r for r in formatted_indiv if r['score'] > score]) + 1
        result['rank'] = current_rank
        prev_score = score
    
    # Format team results
    formatted_team = []
    formatted_all_team = []
    current_rank = 1
    prev_res = None
    
    # Format all team results (for CSV)
    for res in all_team: # team score, "prog score", 4th person score, ranking, school, district, people on team
        # If score is different from previous, update rank
        if prev_res is not None and res[0:3] != prev_res[0:3]:
            current_rank = len(formatted_all_team) + 1
        prev_res = res
        
        # Check if this team is in the qualifying results
        is_qualified = res in team_results
        
        result_dict = {
            "rank": current_rank,
            "score": int(res[0]),
            "school": res[4],
            "district": res[5],
            "names": res[6],
            "qualified": is_qualified,
            "fourth": int(res[2]),
            "prog_score": int(res[1])
        }
        
        formatted_all_team.append(result_dict)
        if is_qualified:
            # Create a copy for the display list, we'll update ranks later
            display_dict = result_dict.copy()
            formatted_team.append(display_dict)
    
    # Update ranks for display team list to be continuous
    current_rank = 1
    prev_score = None
    for result in formatted_team:
        score, prog, fourth = result['score'], result['prog_score'], result['fourth']
        if prev_res is not None and prev_score != (score, prog, fourth):
            current_rank = len([r for r in formatted_team if (r['score'], r['prog_score'], r['fourth']) > (score, prog, fourth)]) + 1
        result['rank'] = current_rank
        prev_score = (score, prog, fourth)
    
    return jsonify({
        "individual": formatted_indiv,  # Only qualifying individuals (for display)
        "team": formatted_team,         # Only qualifying teams (for display)
        "all_individual": formatted_all_indiv,  # All individuals (for CSV)
        "all_team": formatted_all_team,        # All teams (for CSV)
        "empty_districts": empty_districts
    })

@app.route('/download_csv', methods=['POST'])
def download_csv():
    data = request.json
    results = data['results']
    competition = data['competition']
    year = data['year']
    conf = data['conf']
    choice = data['choice']
    type = data['type']
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    if type == 'individual':
        # Write headers for individual results
        if competition == "Science":
            writer.writerow(['Rank', 'Score', 'Name', 'School', 'District', 'Biology', 'Chemistry', 'Physics', 'Qualified?'])
        elif competition == "CS":
            writer.writerow(['Rank', 'Score', 'Name', 'School', 'District', 'Qualified?'])
        else:
            writer.writerow(['Rank', 'Score', 'Name', 'School', 'District', 'Qualified?'])
        
        # Write individual results
        for result in results['all_individual']:
            qualification_status = "Yes" if result['qualified'] else ""
            
            if competition == "Science":
                writer.writerow([
                    result['rank'],
                    result['score'],
                    result['name'],
                    result['school'],
                    result['district'],
                    result['bio'],
                    result['chem'],
                    result['phys'],
                    qualification_status
                ])
            elif competition == "CS":
                writer.writerow([
                    result['rank'],
                    result['score'],
                    result['name'],
                    result['school'],
                    result['district'],
                    qualification_status
                ])
            else:
                writer.writerow([
                    result['rank'],
                    result['score'],
                    result['name'],
                    result['school'],
                    result['district'],
                    qualification_status
                ])
    else:  # team results
        # Write headers for team results
        if competition == "CS":
            writer.writerow(['Rank', 'Score', 'School', 'District', 'Team Members', 'Programming Score', 'Qualified?'])
        else:
            writer.writerow(['Rank', 'Score', 'School', 'District', 'Team Members', 'Qualified?'])
        
        # Write team results
        for result in results['all_team']:
            qualification_status = "Yes" if result['qualified'] else ""
            if choice == '3':  # Regional Results
                qualification_status = "Yes" if result['qualified'] else ""
            
            if competition == "CS":
                writer.writerow([
                    result['rank'],
                    result['score'],
                    result['school'],
                    result['district'],
                    ', '.join(result['names']),
                    result.get('prog_score', ''),
                    qualification_status
                ])
            else:
                writer.writerow([
                    result['rank'],
                    result['score'],
                    result['school'],
                    result['district'],
                    ', '.join(result['names']),
                    qualification_status
                ])
    
    # Create the response
    output.seek(0)
    filename = f"{competition}_{year}_{conf}A_{type}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    app.run(debug=True) 