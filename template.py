# this is what the site is based on

import requests
import re
from time import sleep

def req(dist="", reg="", state="", comp="", conf=""):
	inp = f"{url_template}groupingid={comp}&Submit=View+Postings&region={reg}&district={dist}&state={state}&conference={conf}&seasonid={year}"
	return requests.get(inp).content.decode()

def color(dist, s):
	dist = int(dist)
	if 1 <= dist <= 8:
		return f"\033[38;5;160m{s}\033[0m"
	elif 9 <= dist <= 16:
		return f"\033[38;5;208m{s}\033[0m"
	elif 17 <= dist <= 24:
		return f"\033[38;5;70m{s}\033[0m"
	elif 25 <= dist <= 32:
		return f"\033[94m{s}\033[0m"
	return s  # Default case, no color

def district_parser(reg_number):
	indiv_results = []
	team_results = []
	mxbio, mxchem, mxphys = dict(), dict(), dict()
	for i in range(reg_number * 8 - 7, reg_number * 8 + 1):
		try: # in case scraping fails for whatever reason on anything
			scrape = req(dist = str(i), comp = str(subj), conf = conf)

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
		except: pass # ok so apparently the code does sometimes throw errors but still works???
		print(f"Finished District {i}")
		sleep(0.25) # allow the requests module to relax a bit lol

	indiv_results.sort(reverse=True)
	team_results.sort(reverse=True)
	# fix team results to only have advancing teams
	tmp, found = [], False
	for x in team_results:
		if x[1] == "1st":
			tmp.append(x)
		elif x[1] == "2nd" and not found:
			tmp.append(x)
			found = True 
	team_results = tmp
	# now make indiv results contain ONLY the advancing individuals
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

	print('\n')
	return (indiv_results, team_results)

url_template = "https://postings.speechwire.com/r-uil-academics.php?"
competitions = {1: "Accounting", 8: "Calculator", 2: "Comp Apps", 
	9: "CS", 3: "Current Events", 10: "Math", 11: "Number Sense",
	12: "Science", 7: "Spelling", 4: "Lit Crit", 6: "Social Studies"}
year = -1
print("Choose a UIL Season: 2023, 2024, 2025")
season = input()
while True: # avoid goofy accidental input
	works = False
	try:
		season = int(season)
		if 2023 <= season <= 2025:
			works = True
			year = season - 2008
	except:
		print("Please try again:")
		season = input()
	if works: break
	else:
		print("Please try again:")
		season = input()

print("Input the conference number (1-6)")
conf = input()
while True: # avoid goofy accidental input
	works = False
	try:
		conf = int(conf)
		if 1 <= conf and conf <= 6:
			works = True
	except:
		print("Please try again:")
		conf = input()
	if works: break
	else:
		print("Please try again:")
		conf = input()

print(f"""Input your selection choice
> 1 = District Results (input which {conf}A region to compare to)
> 2 = District Results (all of {conf}A)
> 3 = Regional Results (compares these with all across the state)""")
choice = input()
while True: # avoid goofy accidental input
	works = False
	try:
		choice = int(choice)
		if 1 <= choice and choice <= 3:
			works = True
	except:
		print("Please try again:")
		choice = input()
	if works: break
	else:
		print("Please try again:")
		choice = input()

print("""Now, input the number that matches your competition:
> Number Sense   = 11
> Calculator     =  8
> Math           = 10
> Science        = 12
> Comp Sci       =  9
> Comp Apps      =  2
> Spelling       =  7
> Current Events =  3
> Accounting     =  1
> Lit Crit       =  4
> Social Studies =  6""")
subj, comp = input(), ""
while True:
	try:
		subj = int(subj)
		comp = competitions[subj]
		break
	except:
		print("Please try again:")
		subj = input()

if choice == 1:
	print("Input region number!")
	reg_number = input()
	while True: # avoid goofy accidental input
		works = False
		try:
			reg_number = int(reg_number)
			if 1 <= reg_number and reg_number <= 4:
				works = True
		except:
			print("Please try again:")
			reg_number = input()
		if works: break
		else:
			print("Please try again:")
			reg_number = input()

	indiv_results, team_results = district_parser(reg_number)
	# dipslay all regional qualifiers + all teams advancing to regionals
	print(comp, "results!")
	print("INDIVIDUAL:")
	for i in range(len(indiv_results)):
		res = indiv_results[i]
		print(f"Rank {i+1:2d}: {int(res[0]):3d} --> {res[2]} from {res[3]} ({res[4]})")
	if subj == 12:
		# go ahead and print bio / chem / phys rankings too
		indiv_results.sort(key = lambda a: a[-3], reverse=True)
		print("\nBIO RANKINGS:")
		for i in range(len(indiv_results)):
			res = indiv_results[i]
			print(f"Rank {i+1:2d}: {res[-3]:3d} --> {res[2]} from {res[3]} ({res[4]})")
		indiv_results.sort(key = lambda a: a[-2], reverse=True)
		print("\nCHEM RANKINGS:")
		for i in range(len(indiv_results)):
			res = indiv_results[i]
			print(f"Rank {i+1:2d}: {res[-2]:3d} --> {res[2]} from {res[3]} ({res[4]})")
		indiv_results.sort(key = lambda a: a[-1], reverse=True)
		print("\nPHYS RANKINGS:")
		for i in range(len(indiv_results)):
			res = indiv_results[i]
			print(f"Rank {i+1:2d}: {res[-1]:3d} --> {res[2]} from {res[3]} ({res[4]})")
	print("\nTEAM:")
	for i in range(len(team_results)):
		res = team_results[i]
		print(f"Rank {i+1:2d}: {res[0]:4d}{f' (PROG = {res[-1]})' if comp == 'CS' else ''} --> {res[2]} ({res[3]})")

elif choice == 2:
	indiv_results, team_results = [], []
	for r in range(1, 5):
		I, T = district_parser(r)
		indiv_results += I
		team_results += T
	indiv_results.sort(reverse=True)
	team_results.sort(reverse=True)

	# display only T25 regional qualifiers + all teams advancing to regionals
	print(comp, "results!")
	print("INDIVIDUAL:")
	for i in range(min(25, len(indiv_results))):
		res = indiv_results[i]
		print(color(res[4][-2:], f"Rank {i+1:2d}: {int(res[0]):3d} --> {res[2]} from {res[3]} ({res[4]})"))
	if subj == 12:
		# go ahead and print bio / chem / phys rankings too
		indiv_results.sort(key = lambda a: a[-3], reverse=True)
		print("\nBIO RANKINGS:")
		for i in range(min(25, len(indiv_results))):
			res = indiv_results[i]
			print(color(res[4][-2:], f"Rank {i+1:2d}: {res[-3]:3d} --> {res[2]} from {res[3]} ({res[4]})"))
		indiv_results.sort(key = lambda a: a[-2], reverse=True)
		print("\nCHEM RANKINGS:")
		for i in range(min(25, len(indiv_results))):
			res = indiv_results[i]
			print(color(res[4][-2:], f"Rank {i+1:2d}: {res[-2]:3d} --> {res[2]} from {res[3]} ({res[4]})"))
		indiv_results.sort(key = lambda a: a[-1], reverse=True)
		print("\nPHYS RANKINGS:")
		for i in range(min(25, len(indiv_results))):
			res = indiv_results[i]
			print(color(res[4][-2:], f"Rank {i+1:2d}: {res[-1]:3d} --> {res[2]} from {res[3]} ({res[4]})"))
	print("\nTEAM:")
	for i in range(len(team_results)):
		res = team_results[i]
		print(color(res[3][-2:], f"Rank {i+1:2d}: {res[0]:4d}{f' (PROG = {res[-1]})' if comp == 'CS' else ''} --> {res[2]} ({res[3]})"))
else:
	indiv_results = []
	team_results = []
	mxbio, mxchem, mxphys = dict(), dict(), dict()
	for i in range(1, 5):
		try: # in case scraping fails for whatever reason on anything
			scrape = req(reg = str(i), comp = str(subj), conf = conf)
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
				name = values[2]
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
		except Exception as e: pass# ok so apparently the code does sometimes throw errors but still works???
		print(f"Finished Region {i}\n")
		sleep(0.25) # allow the requests module to relax a bit lol

	indiv_results.sort(reverse=True)
	team_results.sort(reverse=True)
	# fix team results to only have advancing teams
	tmp, found = [], False
	for x in team_results:
		if x[1] == "1st":
			tmp.append(x)
		elif x[1] == "2nd" and not found:
			tmp.append(x)
			found = True 
	team_results = tmp
	# now make indiv results contain ONLY the advancing individuals
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

	# display all state qualifiers + all teams advancing to state
	print(comp, "results!")
	print("INDIVIDUAL:")
	for i in range(len(indiv_results)):
		res = indiv_results[i]
		print(f"Rank {i+1:2d}: {int(res[0]):3d} --> {res[2]} from {res[3]} ({res[4]})")
	if subj == 12:
		# go ahead and print bio / chem / phys rankings too
		indiv_results.sort(key = lambda a: a[-3], reverse=True)
		print("\nBIO RANKINGS:")
		for i in range(len(indiv_results)):
			res = indiv_results[i]
			print(f"Rank {i+1:2d}: {res[-3]:3d} --> {res[2]} from {res[3]} ({res[4]})")
		indiv_results.sort(key = lambda a: a[-2], reverse=True)
		print("\nCHEM RANKINGS:")
		for i in range(len(indiv_results)):
			res = indiv_results[i]
			print(f"Rank {i+1:2d}: {res[-2]:3d} --> {res[2]} from {res[3]} ({res[4]})")
		indiv_results.sort(key = lambda a: a[-1], reverse=True)
		print("\nPHYS RANKINGS:")
		for i in range(len(indiv_results)):
			res = indiv_results[i]
			print(f"Rank {i+1:2d}: {res[-1]:3d} --> {res[2]} from {res[3]} ({res[4]})")
	print("\nTEAM:")
	for i in range(len(team_results)):
		res = team_results[i]
		print(f"Rank {i+1:2d}: {res[0]:4d}{f' (PROG = {res[-1]})' if comp == 'CS' else ''} --> {res[2]} ({res[3]})")

