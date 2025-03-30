function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    const loadingDiv = document.getElementById('loading');
    const competitionTitle = document.getElementById('competitionTitle');
    const emptyDistrictsWarning = document.getElementById('emptyDistrictsWarning');
    const emptyDistrictsList = document.getElementById('emptyDistrictsList');
    
    // Hide loading spinner and show results
    loadingDiv.classList.add('hidden');
    resultsDiv.classList.remove('hidden');
    
    // Set competition title
    competitionTitle.textContent = data.competition;
    
    // Handle empty districts warning
    if (data.empty_districts && data.empty_districts.length > 0) {
        emptyDistrictsList.textContent = data.empty_districts.join(', ');
        emptyDistrictsWarning.classList.remove('hidden');
    } else {
        emptyDistrictsWarning.classList.add('hidden');
    }
    
    // Display individual results
    const indivTable = document.getElementById('indivTable');
    const indivBody = indivTable.querySelector('tbody');
    indivBody.innerHTML = '';
    
    data.individual.forEach(result => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${result.place}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${result.name}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${result.school}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${result.score}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${result.district}</td>
        `;
        indivBody.appendChild(row);
    });
    
    // Display team results
    const teamTable = document.getElementById('teamTable');
    const teamBody = teamTable.querySelector('tbody');
    teamBody.innerHTML = '';
    
    data.team.forEach(result => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${result.place}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${result.school}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${result.score}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${result.district}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${result.members.join(', ')}</td>
        `;
        teamBody.appendChild(row);
    });
} 