const competitions = {
    1: "Accounting",
    8: "Calculator",
    9: "CS",
    3: "Current Events",
    10: "Math",
    11: "Number Sense",
    12: "Science",
    7: "Spelling",
    4: "Lit Crit",
    6: "Social Studies",
};

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("resultsForm");
    const regionInput = document.getElementById("regionInput");
    const loading = document.getElementById("loading");
    const results = document.getElementById("results");
    const downloadSection = document.getElementById("downloadSection");
    const downloadIndividualCSV = document.getElementById("downloadIndividualCSV");
    const downloadTeamCSV = document.getElementById("downloadTeamCSV");
    const choiceSelect = form.querySelector('select[name="choice"]');
    const confSelect = form.querySelector('select[name="conf"]');
    const scienceSorting = document.getElementById("scienceSorting");
    const CLASSIFICATION_ROW_CLASSES = {
        "1A": "class-1a-row",
        "2A": "class-2a-row",
        "3A": "class-3a-row",
        "4A": "class-4a-row",
        "5A": "class-5a-row",
        "6A": "class-6a-row",
    };

    let currentResults = null;
    let currentYear = null;
    let currentConf = null;
    let currentComp = null;
    let currentChoice = null;
    let classificationMode = false;
    const apiBase = window.UIL_API_BASE_URL || "";

    function updateRegionVisibility() {
        regionInput.classList.toggle("hidden", choiceSelect.value !== "1");
    }

    function updateChoiceOptionsForConf() {
        const optSingle = document.getElementById("choiceOptionSingleRegion");
        const isAll = confSelect.value === "0";
        optSingle.hidden = isAll;
        optSingle.disabled = isAll;
        if (isAll && choiceSelect.value === "1") {
            choiceSelect.value = "2";
        }
        updateRegionVisibility();
    }

    choiceSelect.addEventListener("change", updateRegionVisibility);
    confSelect.addEventListener("change", updateChoiceOptionsForConf);
    updateChoiceOptionsForConf();

    document.querySelectorAll(".sort-btn").forEach((btn) => {
        btn.addEventListener("click", function () {
            if (!currentResults) return;

            document.querySelectorAll(".sort-btn").forEach((b) => {
                b.classList.remove("bg-blue-100", "text-blue-700");
                b.classList.add("bg-gray-100", "text-gray-700");
            });
            this.classList.remove("bg-gray-100", "text-gray-700");
            this.classList.add("bg-blue-100", "text-blue-700");

            const sortBy = this.dataset.sort;
            const sortedResults = [...currentResults.individual];
            if (sortBy === "overall") {
                sortedResults.sort((a, b) => b.score - a.score);
                assignRanks(sortedResults, "score");
            } else {
                sortedResults.sort((a, b) => b[sortBy] - a[sortBy]);
                assignRanks(sortedResults, sortBy);
            }
            updateIndividualResults(sortedResults);
        });
    });

    function assignRanks(arr, key) {
        let currentRank = 1;
        for (let i = 0; i < arr.length; i += 1) {
            if (i === 0) {
                arr[i].rank = currentRank;
            } else if (arr[i][key] === arr[i - 1][key]) {
                arr[i].rank = currentRank;
            } else {
                currentRank = i + 1;
                arr[i].rank = currentRank;
            }
        }
    }

    function getRegionClass(district) {
        if (district.startsWith("Region")) {
            const regionNum = district.split(" ")[1];
            return `region-${regionNum}-row`;
        }
        if (district.startsWith("District")) {
            const distNum = Number.parseInt(district.split(" ")[1], 10);
            if (distNum <= 8) return "region-1-row";
            if (distNum <= 16) return "region-2-row";
            if (distNum <= 24) return "region-3-row";
            return "region-4-row";
        }
        return "";
    }

    function getRowColorClass(res) {
        if (classificationMode && res.classification) {
            return CLASSIFICATION_ROW_CLASSES[res.classification] || "";
        }
        return getRegionClass(res.district);
    }

    function updateIndividualResults(individualResultRows) {
        const individualResults = document.getElementById("individualResults");
        individualResults.innerHTML = "";
        individualResultRows.forEach((res) => {
            const row = createIndividualRow(res);
            individualResults.appendChild(row);
        });
    }

    function createIndividualRow(res) {
        const row = document.createElement("tr");
        const hasScience = "bio" in res;
        const colorClass = getRowColorClass(res);
        row.className = colorClass;
        const classCell = classificationMode && res.classification
            ? `<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900" style="width: 72px">${res.classification}</td>`
            : "";

        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900" style="width: 80px">${res.rank}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900" style="width: 100px">${res.score}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900" style="width: 200px">${res.name}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900" style="width: 200px">${res.school}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900" style="width: 120px">${res.district}</td>
            ${hasScience ? `
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900" style="width: 100px">${res.bio}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900" style="width: 100px">${res.chem}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900" style="width: 100px">${res.phys}</td>
            ` : ""}
            ${classCell}
        `;
        return row;
    }

    function updateTeamResults(teamResultRows) {
        const teamResults = document.getElementById("teamResults");
        teamResults.innerHTML = "";
        teamResultRows.forEach((res) => {
            const row = createTeamRow(res);
            teamResults.appendChild(row);
        });
    }

    function createTeamRow(res) {
        const row = document.createElement("tr");
        const hasProgScore = res.prog_score !== -999;
        const colorClass = getRowColorClass(res);
        row.className = colorClass;
        const classCell = classificationMode && res.classification
            ? `<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900" style="width: 72px">${res.classification}</td>`
            : "";

        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900" style="width: 80px">${res.rank}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900" style="width: 100px">${res.score}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900" style="width: 200px">${res.school}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900" style="width: 120px">${res.district}</td>
            <td class="px-6 py-4 text-sm text-gray-900" style="width: 400px">${res.names.join(", ")}</td>
            ${hasProgScore ? `
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900" style="width: 150px">${res.prog_score}</td>
            ` : ""}
            ${classCell}
        `;
        return row;
    }

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        loading.classList.remove("hidden");
        results.classList.add("hidden");
        downloadSection.classList.add("hidden");

        const formData = new FormData(form);
        const data = {
            year: formData.get("year"),
            conf: formData.get("conf"),
            comp: formData.get("comp"),
            choice: formData.get("choice"),
            region: formData.get("region"),
        };

        try {
            const response = await fetch(`${apiBase}/results`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
            });
            if (!response.ok) {
                throw new Error(`API request failed: ${response.status}`);
            }
            const result = await response.json();
            currentResults = result;
            currentYear = data.year;
            currentConf = data.conf;
            currentComp = formData.get("comp");
            currentChoice = data.choice;
            classificationMode = Boolean(result.classification_mode);

            const emptyDistrictsWarning = document.getElementById("emptyDistrictsWarning");
            const emptyDistrictsList = document.getElementById("emptyDistrictsList");
            if (result.empty_districts && result.empty_districts.length > 0) {
                emptyDistrictsList.textContent = result.empty_districts.join(", ");
                emptyDistrictsWarning.classList.remove("hidden");
            } else {
                emptyDistrictsWarning.classList.add("hidden");
            }

            const hasScience = currentComp === "12";
            scienceSorting.classList.toggle("hidden", !hasScience);
            document.getElementById("bioHeader").classList.toggle("hidden", !hasScience);
            document.getElementById("chemHeader").classList.toggle("hidden", !hasScience);
            document.getElementById("physHeader").classList.toggle("hidden", !hasScience);

            document.getElementById("progScoreHeader").classList.toggle("hidden", currentComp !== "9");
            document.getElementById("classificationIndivHeader").classList.toggle("hidden", !classificationMode);
            document.getElementById("classificationTeamHeader").classList.toggle("hidden", !classificationMode);

            document.getElementById("competitionTitle").textContent = `${competitions[data.comp]} Results`;
            updateIndividualResults(result.individual);
            updateTeamResults(result.team);

            results.classList.remove("hidden");
            downloadSection.classList.remove("hidden");
        } catch (error) {
            console.error("Error:", error);
            alert("Results are not available yet for this filter. Try again later.");
        } finally {
            loading.classList.add("hidden");
        }
    });

    function csvEscape(value) {
        if (value === null || value === undefined) return "";
        const str = String(value);
        if (str.includes('"') || str.includes(",") || str.includes("\n")) {
            return `"${str.replaceAll('"', '""')}"`;
        }
        return str;
    }

    function downloadCsvString(csv, filename) {
        const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    function buildCsv(type) {
        const rows = [];
        const competition = competitions[currentComp];
        if (type === "individual") {
            if (competition === "Science") {
                const header = ["Rank", "Score", "Name", "School", "District", "Biology", "Chemistry", "Physics"];
                if (classificationMode) header.push("Classification");
                header.push("Qualified?");
                rows.push(header);
            } else if (competition === "CS") {
                const header = ["Rank", "Score", "Name", "School", "District", "Programming Score"];
                if (classificationMode) header.push("Classification");
                header.push("Qualified?");
                rows.push(header);
            } else {
                const header = ["Rank", "Score", "Name", "School", "District"];
                if (classificationMode) header.push("Classification");
                header.push("Qualified?");
                rows.push(header);
            }

            currentResults.all_individual.forEach((result) => {
                let row;
                if (competition === "Science") {
                    row = [
                        result.rank, result.score, result.name, result.school, result.district,
                        result.bio, result.chem, result.phys,
                    ];
                } else if (competition === "CS") {
                    row = [
                        result.rank, result.score, result.name, result.school, result.district, result.prog_score ?? "",
                    ];
                } else {
                    row = [result.rank, result.score, result.name, result.school, result.district];
                }
                if (classificationMode) row.push(result.classification ?? "");
                row.push(result.qualified ? "Yes" : "");
                rows.push(row);
            });
        } else {
            if (competition === "CS") {
                const header = ["Rank", "Score", "School", "District", "Team Members", "Programming Score", "4th Person Score"];
                if (classificationMode) header.push("Classification");
                header.push("Qualified?");
                rows.push(header);
            } else {
                const header = ["Rank", "Score", "School", "District", "Team Members", "4th Person Score"];
                if (classificationMode) header.push("Classification");
                header.push("Qualified?");
                rows.push(header);
            }

            currentResults.all_team.forEach((result) => {
                let row;
                if (competition === "CS") {
                    row = [
                        result.rank, result.score, result.school, result.district, result.names.join(", "),
                        result.prog_score ?? "", result.fourth ?? "",
                    ];
                } else {
                    row = [
                        result.rank, result.score, result.school, result.district, result.names.join(", "), result.fourth ?? "",
                    ];
                }
                if (classificationMode) row.push(result.classification ?? "");
                row.push(result.qualified ? "Yes" : "");
                rows.push(row);
            });
        }
        return rows.map((row) => row.map(csvEscape).join(",")).join("\n");
    }

    function makeFilename(type) {
        const competition = competitions[currentComp];
        const confTag = currentConf === "0" ? "All1A-6A" : `${currentConf}A`;
        const timestamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\..+/, "").replace("T", "_");
        return `${competition}_${currentYear}_${confTag}_${type}_results_${timestamp}.csv`;
    }

    downloadIndividualCSV.addEventListener("click", () => {
        if (!currentResults) return;
        downloadCsvString(buildCsv("individual"), makeFilename("individual"));
    });

    downloadTeamCSV.addEventListener("click", () => {
        if (!currentResults) return;
        downloadCsvString(buildCsv("team"), makeFilename("team"));
    });
});