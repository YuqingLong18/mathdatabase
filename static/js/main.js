/**
 * MathBank Main Application Logic
 */

const state = {
    problems: [],
    filteredProblems: [],
    worksheet: [], // Array of problem objects
    favorites: new Set(),
    filters: {
        search: '',
        level: '',
        yearFrom: '',
        yearTo: '',
        problemRange: '',
        primaryCategory: '',
        secondaryCategory: ''
    },
    currentProblem: null,
    darkMode: false
};

// DOM Elements
const elements = {
    problemList: document.getElementById('problemList'),
    worksheetList: document.getElementById('worksheetList'),
    worksheetCount: document.getElementById('worksheetCount'),
    detailView: document.getElementById('detailView'),
    emptyState: document.getElementById('emptyState'),
    detailContent: document.getElementById('detailContent'),
    searchInput: document.getElementById('searchInput'),
    filters: {
        level: document.getElementById('levelFilter'),
        yearFrom: document.getElementById('yearFromFilter'),
        yearTo: document.getElementById('yearToFilter'),
        problemRange: document.getElementById('problemRangeFilter'),
        primaryCategory: document.getElementById('primaryCategoryFilter'),
        secondaryCategory: document.getElementById('secondaryCategoryFilter')
    },
    sheetName: document.getElementById('sheetName'),
    darkModeToggle: document.getElementById('darkModeToggle')
};

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    loadPreferences();
    loadFilterOptions();
    loadProblems();
    setupEventListeners();
    updateDarkMode();
});

function setupEventListeners() {
    // Search
    elements.searchInput.addEventListener('input', (e) => {
        state.filters.search = e.target.value.toLowerCase();
        applyFilters();
    });

    // Filters
    Object.entries(elements.filters).forEach(([key, element]) => {
        element.addEventListener('change', () => {
            state.filters[key] = element.value;
            // For year inputs, we might want to debounce or wait for valid input
            if (key === 'yearFrom' || key === 'yearTo') {
                loadProblems(); // Reload from server for heavy filtering
            } else {
                applyFilters(); // Client-side filtering for others
            }
        });
    });

    // Dark Mode
    elements.darkModeToggle.addEventListener('click', toggleDarkMode);
}

// Data Loading
async function loadFilterOptions() {
    try {
        const response = await fetch('/api/filters');
        const data = await response.json();
        
        // Populate categories
        populateSelect(elements.filters.primaryCategory, data.primary_categories);
        populateSelect(elements.filters.secondaryCategory, data.secondary_categories);
        
        // Set year placeholders
        if (data.years.length > 0) {
            const minYear = Math.min(...data.years.map(y => parseInt(y)));
            const maxYear = Math.max(...data.years.map(y => parseInt(y)));
            elements.filters.yearFrom.placeholder = `From (${minYear})`;
            elements.filters.yearTo.placeholder = `To (${maxYear})`;
        }
    } catch (error) {
        console.error('Error loading filters:', error);
    }
}

async function loadProblems() {
    const params = new URLSearchParams();
    if (state.filters.level) params.append('level', state.filters.level);
    if (state.filters.yearFrom) params.append('year_from', state.filters.yearFrom);
    if (state.filters.yearTo) params.append('year_to', state.filters.yearTo);
    
    try {
        elements.problemList.innerHTML = '<div class="p-4 text-center text-muted">Loading...</div>';
        const response = await fetch(`/api/problems?${params}`);
        const data = await response.json();
        state.problems = data.problems;
        applyFilters();
    } catch (error) {
        console.error('Error loading problems:', error);
        elements.problemList.innerHTML = '<div class="p-4 text-center text-red-500">Error loading problems</div>';
    }
}

// Filtering
function applyFilters() {
    state.filteredProblems = state.problems.filter(problem => {
        // Search filter
        if (state.filters.search) {
            const searchStr = `${problem.year} ${problem.test_type} ${problem.problem_number} ${problem.primary_category} ${problem.secondary_category}`.toLowerCase();
            if (!searchStr.includes(state.filters.search)) return false;
        }
        
        // Client-side filters (if not handled by backend)
        if (state.filters.problemRange) {
            const num = parseInt(problem.problem_number);
            const [min, max] = state.filters.problemRange.split('-').map(Number);
            if (num < min || num > max) return false;
        }
        
        if (state.filters.primaryCategory && problem.primary_category !== state.filters.primaryCategory) return false;
        if (state.filters.secondaryCategory && problem.secondary_category !== state.filters.secondaryCategory) return false;
        
        return true;
    });
    
    renderProblemList();
}

// Rendering
function renderProblemList() {
    elements.problemList.innerHTML = '';
    
    if (state.filteredProblems.length === 0) {
        elements.problemList.innerHTML = '<div class="p-4 text-center text-muted">No problems found</div>';
        return;
    }
    
    state.filteredProblems.forEach(problem => {
        const card = document.createElement('div');
        card.className = `problem-card ${state.currentProblem?.key === problem.key ? 'active' : ''}`;
        card.onclick = () => viewProblem(problem);
        
        const isFav = state.favorites.has(problem.key);
        const inSheet = state.worksheet.some(p => p.key === problem.key);
        
        card.innerHTML = `
            <div class="problem-info">
                <h3>${problem.display_name}</h3>
                <div class="problem-meta">
                    ${problem.primary_category ? `<span class="badge">${problem.primary_category}</span>` : ''}
                    ${problem.secondary_category ? `<span class="badge">${problem.secondary_category}</span>` : ''}
                </div>
            </div>
            <div class="problem-actions">
                <button class="btn-icon favorite ${isFav ? 'active' : ''}" onclick="toggleFavorite(event, '${problem.key}')">
                    ${isFav ? '★' : '☆'}
                </button>
                <button class="btn-icon ${inSheet ? 'active' : ''}" onclick="toggleWorksheet(event, '${problem.key}')">
                    ${inSheet ? '−' : '＋'}
                </button>
            </div>
        `;
        
        elements.problemList.appendChild(card);
    });
}

function renderWorksheet() {
    elements.worksheetList.innerHTML = '';
    elements.worksheetCount.textContent = state.worksheet.length;
    
    state.worksheet.forEach((problem, index) => {
        const item = document.createElement('div');
        item.className = 'worksheet-item';
        item.draggable = true;
        item.dataset.index = index;
        
        item.innerHTML = `
            <span>${index + 1}. ${problem.display_name}</span>
            <button class="btn-text text-red-500" onclick="removeFromWorksheet(${index})">×</button>
        `;
        
        // Drag and Drop
        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragover', handleDragOver);
        item.addEventListener('drop', handleDrop);
        item.addEventListener('dragenter', handleDragEnter);
        item.addEventListener('dragleave', handleDragLeave);
        
        elements.worksheetList.appendChild(item);
    });
    
    savePreferences();
}

async function viewProblem(problem) {
    state.currentProblem = problem;
    
    // Update active state in list
    document.querySelectorAll('.problem-card').forEach(card => card.classList.remove('active'));
    // Find the card that was clicked (this is a bit hacky, but works for now)
    // In a real framework we'd use state binding
    applyFilters(); // Re-render to update active class
    
    elements.emptyState.classList.add('hidden');
    elements.detailContent.classList.remove('hidden');
    
    // Fetch full details including images
    try {
        const response = await fetch(`/api/problem/${problem.key}`);
        const data = await response.json();
        
        const content = `
            <div class="problem-detail-card">
                <div class="detail-header">
                    <h2 class="detail-title">${data.problem.display_name}</h2>
                    <div class="detail-tags">
                        ${data.problem.primary_category ? `<span class="badge">${data.problem.primary_category}</span>` : ''}
                        ${data.problem.secondary_category ? `<span class="badge">${data.problem.secondary_category}</span>` : ''}
                    </div>
                </div>
                
                <div class="problem-image-container">
                    <img src="${data.problem_image}" class="problem-img" alt="Problem Image">
                </div>
                
                <div class="flex justify-center gap-4">
                    <button class="btn ${state.worksheet.some(p => p.key === problem.key) ? 'btn-danger' : 'btn-primary'}" 
                            onclick="toggleWorksheet(null, '${problem.key}')">
                        ${state.worksheet.some(p => p.key === problem.key) ? 'Remove from Worksheet' : 'Add to Worksheet'}
                    </button>
                </div>
                
                ${data.solution_images.length > 0 ? `
                    <div class="solutions-section">
                        <h3 class="solutions-title">Solutions</h3>
                        ${data.solution_images.map(url => `
                            <div class="problem-image-container">
                                <img src="${url}" class="problem-img" alt="Solution Image">
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
        
        elements.detailContent.innerHTML = content;
        
    } catch (error) {
        console.error('Error loading problem details:', error);
    }
}

// Actions
window.toggleFavorite = (e, key) => {
    if (e) e.stopPropagation();
    if (state.favorites.has(key)) {
        state.favorites.delete(key);
    } else {
        state.favorites.add(key);
    }
    savePreferences();
    renderProblemList();
};

window.toggleWorksheet = (e, key) => {
    if (e) e.stopPropagation();
    
    const index = state.worksheet.findIndex(p => p.key === key);
    if (index !== -1) {
        state.worksheet.splice(index, 1);
    } else {
        const problem = state.problems.find(p => p.key === key);
        if (problem) {
            state.worksheet.push(problem);
        }
    }
    
    renderWorksheet();
    renderProblemList(); // Update buttons
    if (state.currentProblem && state.currentProblem.key === key) {
        viewProblem(state.currentProblem); // Refresh detail view button
    }
};

window.removeFromWorksheet = (index) => {
    state.worksheet.splice(index, 1);
    renderWorksheet();
    renderProblemList();
};

window.clearFilters = () => {
    state.filters.search = '';
    state.filters.level = '';
    state.filters.yearFrom = '';
    state.filters.yearTo = '';
    state.filters.problemRange = '';
    state.filters.primaryCategory = '';
    state.filters.secondaryCategory = '';
    
    // Reset inputs
    elements.searchInput.value = '';
    Object.values(elements.filters).forEach(el => el.value = '');
    
    loadProblems();
};

window.addAllFiltered = () => {
    const newProblems = state.filteredProblems.filter(p => !state.worksheet.some(wp => wp.key === p.key));
    state.worksheet.push(...newProblems);
    renderWorksheet();
    renderProblemList();
};

window.saveWorksheet = () => {
    const name = elements.sheetName.value;
    const worksheetData = {
        name: name,
        problems: state.worksheet,
        date: new Date().toISOString()
    };
    
    const savedSheets = JSON.parse(localStorage.getItem('savedWorksheets') || '[]');
    savedSheets.push(worksheetData);
    localStorage.setItem('savedWorksheets', JSON.stringify(savedSheets));
    alert('Worksheet saved!');
};

window.exportSheet = async (type) => {
    if (state.worksheet.length === 0) {
        alert('Worksheet is empty');
        return;
    }
    
    const data = {
        problem_keys: state.worksheet.map(p => p.key),
        sheet_name: elements.sheetName.value,
        type: type
    };
    
    try {
        const response = await fetch('/api/worksheet/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${data.sheet_name}_${type}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } else {
            alert('Export failed');
        }
    } catch (error) {
        console.error('Export error:', error);
        alert('Export error');
    }
};

window.logout = async () => {
    await fetch('/api/logout', { method: 'POST' });
    window.location.reload();
};

// Drag and Drop Handlers
let dragSrcEl = null;

function handleDragStart(e) {
    dragSrcEl = this;
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.innerHTML);
    this.classList.add('opacity-50');
}

function handleDragOver(e) {
    if (e.preventDefault) e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    return false;
}

function handleDragEnter(e) {
    this.classList.add('bg-gray-100');
}

function handleDragLeave(e) {
    this.classList.remove('bg-gray-100');
}

function handleDrop(e) {
    if (e.stopPropagation) e.stopPropagation();
    
    if (dragSrcEl !== this) {
        const srcIndex = parseInt(dragSrcEl.dataset.index);
        const destIndex = parseInt(this.dataset.index);
        
        // Reorder array
        const item = state.worksheet.splice(srcIndex, 1)[0];
        state.worksheet.splice(destIndex, 0, item);
        
        renderWorksheet();
    }
    
    return false;
}

// Utilities
function populateSelect(element, options) {
    element.innerHTML = '<option value="">All</option>';
    options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt;
        option.textContent = opt;
        element.appendChild(option);
    });
}

function toggleDarkMode() {
    state.darkMode = !state.darkMode;
    updateDarkMode();
    savePreferences();
}

function updateDarkMode() {
    if (state.darkMode) {
        document.body.classList.add('dark-mode');
        elements.darkModeToggle.textContent = '☀️';
    } else {
        document.body.classList.remove('dark-mode');
        elements.darkModeToggle.textContent = '🌙';
    }
}

function loadPreferences() {
    state.darkMode = localStorage.getItem('darkMode') === 'true';
    const savedFavs = localStorage.getItem('favorites');
    if (savedFavs) state.favorites = new Set(JSON.parse(savedFavs));
    
    // Load last worksheet if exists
    const lastSheet = localStorage.getItem('currentWorksheet');
    if (lastSheet) {
        try {
            state.worksheet = JSON.parse(lastSheet);
            renderWorksheet();
        } catch (e) {}
    }
}

function savePreferences() {
    localStorage.setItem('darkMode', state.darkMode);
    localStorage.setItem('favorites', JSON.stringify(Array.from(state.favorites)));
    localStorage.setItem('currentWorksheet', JSON.stringify(state.worksheet));
}
